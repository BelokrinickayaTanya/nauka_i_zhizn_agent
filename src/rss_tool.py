"""
RSS тулза для работы с лентами журнала «Наука и жизнь»
"""

import feedparser
import json
from datetime import datetime
from typing import List, Dict, Optional
import os
import re

from rank_bm25 import BM25Okapi
import pymorphy3


class RSSReader:
    """Класс для работы с RSS лентами"""
    
    def __init__(self, config_path: str = "feeds/config.json"):
        self.config_path = config_path
        self.feeds = self._load_config()
        self.last_fetch_time = None
        self.last_fetch_count = 0
        self.morph = pymorphy3.MorphAnalyzer()
        self.articles_cache = None
        self.bm25_index = None
        self.indexed_articles = None
    
    def _load_config(self) -> List[Dict]:

        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config.get('feeds', [])
    
    def _lemmatize(self, word: str) -> str:
        try:
            parsed = self.morph.parse(word)[0]
            return parsed.normal_form
        except:
            return word.lower()
    
    def _normalize_text(self, text: str) -> List[str]:
        """Полная нормализация текста (лемматизация всех слов)"""
        words = re.findall(r'[а-яёa-z]+', text.lower())
        return [self._lemmatize(w) for w in words]
    
    def fetch_all_articles(self, force_refresh: bool = False) -> List[Dict]:
        """Загружает ВСЕ статьи из ВСЕХ RSS лент и удаляет дубликаты"""
        if self.articles_cache is not None and not force_refresh:
            print(f"[INFO] Использую кэш: {len(self.articles_cache)} уникальных статей")
            return self.articles_cache
        
        all_articles = []
        
        for feed_info in self.feeds:
            try:
                feed = feedparser.parse(feed_info['url'])
                
                if feed.bozo:
                    print(f"Warning: проблемы с загрузкой {feed_info['name']}")
                    continue
                
                print(f"[INFO] Загрузка {feed_info['name']}: {len(feed.entries)} статей")
                
                for entry in feed.entries:

                    # Извлекаем полный текст
                    full_text = ""
                    if hasattr(entry, 'yandex_full_text'):
                        full_text = entry.yandex_full_text
                    elif hasattr(entry, 'turbo_content'):
                        full_text = entry.turbo_content
                    elif hasattr(entry, 'content'):
                        full_text = entry.content

                    article = {
                        'source': 'Наука и жизнь',
                        'rubric': feed_info['name'],
                        'category': feed_info.get('category', 'unknown'),
                        'title': entry.get('title', 'Без заголовка'),
                        'summary': self._clean_text(entry.get('summary', '')[:400]),
                        'full_text': self._clean_text(full_text)[:3000],
                        'link': entry.get('link', ''),
                        'date': self._parse_date(entry),
                        'author': entry.get('author', 'Редакция')
                    }
                    all_articles.append(article)
                    
            except Exception as e:
                print(f"Ошибка при загрузке {feed_info['name']}: {e}")
                continue
        
        # Убираем дубликаты по заголовкам
        seen_titles = set()
        unique_articles = []
        for a in all_articles:
            title_key = a['title'].lower().strip()
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_articles.append(a)
        
        # Убираем дубликаты по ссылкам
        seen_links = set()
        final_articles = []
        for a in unique_articles:
            if a['link'] not in seen_links:
                seen_links.add(a['link'])
                final_articles.append(a)
        
        self.articles_cache = final_articles
        self.last_fetch_time = datetime.now()
        self.last_fetch_count = len(final_articles)
        
        print(f"[INFO] Всего загружено: {len(all_articles)} статей")
        print(f"[INFO] Уникальных статей после удаления дубликатов: {len(final_articles)}")
        
        return final_articles  
    
    def build_bm25_index(self, articles: List[Dict]):
        """Строит BM25 индекс из статей"""
        print("[INFO] Построение BM25 индекса...")
        
        texts = []
        for a in articles:
            text = f"{a['title']} {a['summary']} {a.get('full_text', '')}"
            tokens = self._normalize_text(text)
            texts.append(tokens)
        
        self.bm25_index = BM25Okapi(texts)
        self.indexed_articles = articles
        print(f"[INFO] Индекс построен: {len(articles)} статей")
    
    def search(self, query: str, limit: int = 5) -> List[Dict]:
        """Поиск с использованием предварительно построенного индекса"""
        # Загружаем все статьи
        articles = self.fetch_all_articles()
        
        if not articles:
            return []
        
        # Строим индекс (если ещё не построен)
        if self.bm25_index is None or self.indexed_articles != articles:
            self.build_bm25_index(articles)
        
        # Нормализуем запрос
        query_tokens = self._normalize_text(query)
        
        if not query_tokens:
            return []
        
        # Получаем оценки
        scores = self.bm25_index.get_scores(query_tokens)
        
        # Сортируем
        indexed_scores = list(enumerate(scores))
        indexed_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Берём топ результатов
        results = []
        for idx, score in indexed_scores[:limit]:
            if score > 0:
                results.append(self.indexed_articles[idx])
        
        return results
    
    def _clean_text(self, text: str) -> str:
        if not text:
            return ""
        clean = re.sub(r'<[^>]+>', '', text)
        clean = re.sub(r'\s+', ' ', clean)
        return clean.strip()
    
    def _parse_date(self, entry) -> str:
        if hasattr(entry, 'published'):
            return entry.published
        elif hasattr(entry, 'updated'):
            return entry.updated
        else:
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def get_stats(self) -> Dict:
        return {
            "last_fetch_time": str(self.last_fetch_time) if self.last_fetch_time else None,
            "last_fetch_count": self.last_fetch_count,
            "feeds_count": len(self.feeds)
        }