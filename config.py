"""Конфигурация приложения."""

# Telegram
TELEGRAM_BOT_TOKEN = "8731932315:AAE4iZxEx8cEX_WGn5LeLtQVVLnAnXBeT2I"  # Токен от @BotFather
TELEGRAM_CHAT_ID = "388770105"  # ID чата для уведомлений

# HH.ru параметры поиска
HH_SEARCH_TEXT = "Python разработчик"  # Поисковый запрос
HH_AREA = "104"  # Регион (1=Москва, 2=СПб, 104=Россия, None=все)
HH_SALARY_FROM = None  # Минимальная зарплата (None для любого)
HH_EMPLOYMENT = None  # Тип занятости (None для любого)
HH_EXPERIENCE = None  # Опыт работы (None для любого)

# Интервал проверки в секундах
CHECK_INTERVAL = 120  # 2 минуты

# Путь к базе данных
DB_PATH = "vacancies.db"
