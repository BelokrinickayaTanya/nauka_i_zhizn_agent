"""
Модуль логических рассуждений для агента
Chain-of-Thought и анализ новостей
"""

from typing import List, Dict
from collections import Counter
import re


class ReasoningEngine:
    """Движок логических рассуждений"""
    
    @staticmethod
    def extract_main_topics(articles: List[Dict], top_n: int = 5) -> List[str]:
        """Извлекает основные темы из списка статей"""
        if not articles:
            return []
        
        # Собираем все слова из заголовков
        all_text = " ".join([a['title'] for a in articles])
        # Оставляем только русские слова длиной > 4
        words = re.findall(r'[а-яё]{5,}', all_text.lower())
        
        # Частотный анализ 
        word_freq = Counter(words)
        
        top_words = word_freq.most_common(top_n)
        return [word for word, count in top_words if count > 1]
    
    @staticmethod
    def summarize_findings(articles: List[Dict]) -> str:
        """Краткое резюме найденных статей"""
        if not articles:
            return "Статьи не найдены"
        
        if len(articles) == 1:
            return f"Найдена одна статья"
        
        return f"Найдено {len(articles)} статей"
    
    @staticmethod
    def generate_summary(articles: List[Dict], question: str) -> str:
        """Генерирует сводку на основе вопроса пользователя"""
        if not articles:
            return "По вашему запросу ничего не найдено."
        
        summary = f"Найдено {len(articles)} статей по вашему запросу.\n\n"
        
        for i, article in enumerate(articles[:3], 1):
            summary += f"{i}. **{article['title']}**\n"
            summary += f"   {article['summary'][:150]}...\n"
            summary += f"    {article['link']}\n\n"
        
        return summary
    
    @staticmethod
    def chain_of_thought(question: str, articles: List[Dict]) -> List[Dict]:
        """Цепочка рассуждений (Chain-of-Thought) для отображения пользователю"""
        steps = []
        
        steps.append({
            "step": 1,
            "title": " Анализ вопроса",
            "content": f"Пользователь спрашивает: «{question}»",
            "reasoning": "Агент анализирует запрос пользователя"
        })
        
        steps.append({
            "step": 2,
            "title": " Поиск",
            "content": "Поиск статей в RSS ленте",
            "reasoning": "Используется BM25 с морфологической нормализацией (pymorphy3)"
        })
        
        steps.append({
            "step": 3,
            "title": " Результат поиска",
            "content": f"Найдено статей: {len(articles)}",
            "reasoning": "Статьи отфильтрованы по релевантности"
        })
        
        if articles:
            topics = ReasoningEngine.extract_main_topics(articles, top_n=1)
            steps.append({
                "step": 4,
                "title": " Анализ",
                "content": f"Основная тема: {topics[0] if topics else 'определена'}",
                "reasoning": "Проанализированы заголовки статей"
            })
        else:
            steps.append({
                "step": 4,
                "title": " Результат",
                "content": "Релевантные статьи не найдены",
                "reasoning": "В ленте нет материалов по данному запросу"
            })
        
        steps.append({
            "step": 5,
            "title": " Ответ",
            "content": "Ответ сформирован",
            "reasoning": "Структурированный ответ с ссылками на источники"
        })
        
        return steps