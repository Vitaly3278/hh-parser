"""Конфигурация приложения."""

# Импорт локальных секретов (токен, chat_id)
try:
    from config_local import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
except ImportError:
    TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
    TELEGRAM_CHAT_ID = "YOUR_CHAT_ID_HERE"

# HH.ru параметры поиска
HH_SEARCH_TEXT = "Python"  # Поисковый запрос
HH_AREA = None  # Регион (1=Москва, 2=СПб, 104=Россия, None=все)
HH_SALARY_FROM = None  # Минимальная зарплата (None для любого)
HH_EMPLOYMENT = None  # Тип занятости (None для любого)
HH_EXPERIENCE = None  # Опыт работы (None для любого)

# Интервал проверки в секундах
CHECK_INTERVAL = 120  # 2 минуты

# Путь к базе данных
DB_PATH = "vacancies.db"
