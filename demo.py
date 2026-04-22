"""
Агент «Наука и жизнь» — рабочая версия
"""
import streamlit as st
import sys
import os

sys.path.insert(0, 'src')

st.set_page_config(page_title="Агент «Наука и жизнь»", page_icon="🔬", layout="wide")

st.title(" Агент «Наука и жизнь»")
st.caption("RSS-агент с логическими рассуждениями на основе научно-популярного журнала")

try:
    from agent import NaukaIShiznAgent
    from monitor import MetricsMonitor
    st.success(" Все модули загружены")
except ImportError as e:
    st.error(f" Ошибка импорта: {e}")
    st.stop()

if 'agent' not in st.session_state:
    with st.spinner("Загрузка агента..."):
        st.session_state.agent = NaukaIShiznAgent()
        st.session_state.monitor = MetricsMonitor()
        st.session_state.messages = []

# Функция для отображения ответа с рассуждениями
def display_answer(answer, reasoning):
    """Отображает ответ агента и цепочку рассуждений"""
    st.markdown("###  Ответ агента")
    st.write(answer)
    
    with st.expander(" Показать цепочку рассуждений (Chain-of-Thought)"):
        for step in reasoning:
            st.markdown(f"**Шаг {step['step']}: {step['title']}**")
            st.write(f"_{step['content']}_")
            st.caption(f" {step['reasoning']}")
            st.divider()

# Строка поиска
question = st.text_input(" Задайте вопрос:", placeholder="Например: археология, африканские рыбы")

# Кнопки под строкой поиска
col1, col2 = st.columns([1, 1])
with col1:
    submit = st.button(" Искать", type="primary", use_container_width=True)
with col2:
    show_news = st.button("📰 Последние новости", use_container_width=True)

# Обработка поиска
if submit and question:
    with st.spinner(" Агент ищет..."):
        try:
            answer, reasoning = st.session_state.agent.answer_with_cot(question)
            display_answer(answer, reasoning)
        except Exception as e:
            st.error(f"Ошибка: {e}")
            st.code(str(e))

# Обработка кнопки "Последние новости"
if show_news:
    with st.spinner(" Агент анализирует последние новости..."):
        try:
            answer, reasoning = st.session_state.agent.get_latest_news()
            display_answer(answer, reasoning)
        except Exception as e:
            st.error(f"Ошибка: {e}")
            st.code(str(e))

with st.sidebar:
    st.header(" Информация")
    st.info("""
    **Агент умеет:**
    -  Искать по любым словам
    -  Логически рассуждать (Chain-of-Thought)
    -  Показывать последние новости с рассуждениями
    """)
    
    st.header(" Примеры запросов")
    st.code("""
археология
африканские рыбы
женщина гладиатор
нейросеть
    """)
    
    stats = st.session_state.monitor.get_stats()
    if stats['total_requests'] > 0:
        st.header(" Метрики")
        st.metric("Среднее время ответа", f"{stats['avg_response_time_ms']} мс")
        st.metric("Всего запросов", stats['total_requests'])