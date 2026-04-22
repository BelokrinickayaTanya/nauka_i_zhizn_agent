"""
Модуль мониторинга — сбор одной ключевой метрики
Время выполнения запроса агента
"""

import time
from collections import deque
from datetime import datetime
from typing import Dict, List
import json
import os


class MetricsMonitor:
    """Сбор и хранение метрик работы агента"""
    
    def __init__(self, log_file: str = "logs/metrics.json"):
        self.log_file = log_file
        self.response_times = deque(maxlen=100)
        self.request_count = 0
        self._ensure_log_dir()
    
    def _ensure_log_dir(self):
        """Создаёт директорию для логов если её нет"""
        log_dir = os.path.dirname(self.log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
    
    @staticmethod
    def measure(func):
        """Декоратор для замера времени выполнения (статический метод)"""
        def wrapper(self, *args, **kwargs):
            start_time = time.time()
            result = func(self, *args, **kwargs)
            elapsed_ms = (time.time() - start_time) * 1000
            self.record_response_time(elapsed_ms)
            return result
        return wrapper
    
    def record_response_time(self, time_ms: float):
        """Записывает время ответа"""
        self.response_times.append(time_ms)
        self.request_count += 1
        
        # Сохраняем в лог-файл
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "metric": "response_time_ms",
            "value": round(time_ms, 2),
            "request_number": self.request_count
        }
        
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        except Exception as e:
            print(f"Ошибка записи лога: {e}")
    
    def get_stats(self) -> Dict:
        """Возвращает статистику по метрикам"""
        if not self.response_times:
            return {
                "avg_response_time_ms": 0,
                "min_response_time_ms": 0,
                "max_response_time_ms": 0,
                "total_requests": 0
            }
        
        return {
            "avg_response_time_ms": round(sum(self.response_times) / len(self.response_times), 2),
            "min_response_time_ms": round(min(self.response_times), 2),
            "max_response_time_ms": round(max(self.response_times), 2),
            "total_requests": self.request_count,
            "last_10_avg_ms": round(sum(list(self.response_times)[-10:]) / min(10, len(self.response_times)), 2)
        }
    
    def get_full_logs(self, limit: int = 50) -> List[Dict]:
        """Возвращает последние записи из лог-файла"""
        if not os.path.exists(self.log_file):
            return []
        
        logs = []
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        logs.append(json.loads(line))
        except Exception as e:
            print(f"Ошибка чтения логов: {e}")
        
        return logs[-limit:]