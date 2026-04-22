"""
Главный агент — один агент с одной тулзой (RSS)
Реализует Chain-of-Thought 
"""

import json
from datetime import datetime
from typing import Dict, List, Tuple
import os

from rss_tool import RSSReader
from reasoner import ReasoningEngine
from monitor import MetricsMonitor


class NaukaIShiznAgent:
    """
    Агент для работы с журналом «Наука и жизнь»
    Использует RSS как единственный внешний инструмент
    """
    
    def __init__(self, log_dir: str = "logs"):
        self.rss = RSSReader()
        self.reasoner = ReasoningEngine()
        self.monitor = MetricsMonitor(log_file=f"{log_dir}/metrics.json")
        self.log_dir = log_dir
        self.conversation_log = []
        self._ensure_log_dir()
    
    def _ensure_log_dir(self):
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
    
    def _log(self, step: str, data: any):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "step": step,
            "data": str(data)[:500]
        }
        self.conversation_log.append(log_entry)
        
        log_file = f"{self.log_dir}/agent_log.json"
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        except Exception as e:
            print(f"Ошибка записи лога: {e}")
    
    def answer(self, question: str) -> str:
        """Простой ответ """
        articles = self.rss.search(question)
        
        if articles:
            return self.reasoner.generate_summary(articles, question)
        else:
            return f"По вашему запросу «{question}» ничего не найдено."
    
    def answer_with_cot(self, question: str) -> Tuple[str, List[Dict]]:
        """Ответ с цепочкой рассуждений (поиск по запросу)"""
        start_time = datetime.now()
        
        self._log("cot_start", question)
        
        # Обычный поиск
        articles = self.rss.search(question)
        
        self._log("articles_found", len(articles))
        
        elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
        self.monitor.record_response_time(elapsed_ms)
        
        reasoning_steps = self.reasoner.chain_of_thought(question, articles)
        
        if articles:
            analysis = self.reasoner.summarize_findings(articles)
            summary = self.reasoner.generate_summary(articles, question)
            answer = f"{summary}\n\n **Аналитика:** {analysis}"
        else:
            answer = f" По вашему запросу «{question}» ничего не найдено."
        
        self._log("final_answer", answer[:200])
        
        return answer, reasoning_steps
    
    def get_latest_news(self) -> Tuple[str, List[Dict]]:
        """Показывает последние новости (без поиска)"""
        articles = self.rss.fetch_all_articles()
        
        reasoning_steps = self.reasoner.chain_of_thought("последние новости", articles)
        
        if articles:
            analysis = self.reasoner.summarize_findings(articles)
            summary = self.reasoner.generate_summary(articles, "последние новости")
            answer = f"{summary}\n\n **Аналитика:** {analysis}"
        else:
            answer = " Новостей не найдено."
        
        return answer, reasoning_steps
    
    def get_conversation_history(self) -> List[Dict]:
        return self.conversation_log[-20:]