"""Конфигурация приложения."""

import os
from dotenv import load_dotenv

# Загрузка переменных из .env
load_dotenv()


def parse_list(value: str) -> list:
    """Парсинг строки в список."""
    if not value:
        return []
    return [item.strip() for item in value.split(',') if item.strip()]


def parse_optional(value: str, type_func=None):
    """Парсинг опционального значения."""
    if not value or value.lower() in ('none', 'null', ''):
        return None
    return type_func(value) if type_func else value


# Telegram (обязательно)
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
ALLOWED_CHAT_IDS = parse_list(os.getenv('ALLOWED_CHAT_IDS', ''))  # Список разрешённых chat_id

# Email уведомления (опционально)
EMAIL_ENABLED = os.getenv('EMAIL_ENABLED', 'false').lower() == 'true'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USER = os.getenv('EMAIL_USER', '')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')
EMAIL_RECIPIENT = os.getenv('EMAIL_RECIPIENT', '')

# HH.ru параметры
HH_SEARCH_TEXT = os.getenv('HH_SEARCH_TEXT', 'Python разработчик')
HH_AREA = parse_optional(os.getenv('HH_AREA', ''))
HH_SALARY_FROM = parse_optional(os.getenv('HH_SALARY_FROM', ''), int)
HH_EMPLOYMENT = parse_list(os.getenv('HH_EMPLOYMENT', '')) or None
HH_EXPERIENCE = parse_list(os.getenv('HH_EXPERIENCE', '')) or None
HH_EXCLUDE_WORDS = parse_list(os.getenv('HH_EXCLUDE_WORDS', ''))

# Интервал проверки (секунды)
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '300'))

# База данных
DB_PATH = os.getenv('DB_PATH', 'vacancies.db')

# Логирование
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'hh_tracker.log')
