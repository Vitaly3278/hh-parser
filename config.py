"""Конфигурация приложения."""

# Telegram
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # Токен от @BotFather
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID_HERE"  # ID чата для уведомлений

# HH.ru параметры поиска
HH_SEARCH_TEXT = "Python разработчик"  # Поисковый запрос
HH_AREA = "1"  # Регион (1=Москва, 2=СПб, можно None для всех)
HH_SALARY_FROM = None  # Минимальная зарплата (None для любого)
HH_EMPLOYMENT = None  # Тип занятости (None для любого)
HH_EXPERIENCE = None  # Опыт работы (None для любого)

# Интервал проверки в секундах
CHECK_INTERVAL = 300  # 5 минут

# Путь к базе данных
DB_PATH = "vacancies.db"
