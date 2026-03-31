"""Конфигурация приложения."""

import os
from typing import Optional, List
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
TELEGRAM_BOT_TOKEN: str = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID: str = os.getenv('TELEGRAM_CHAT_ID', '')
ALLOWED_CHAT_IDS: List[str] = parse_list(os.getenv('ALLOWED_CHAT_IDS', ''))

# Email уведомления (опционально)
EMAIL_ENABLED: bool = os.getenv('EMAIL_ENABLED', 'false').lower() == 'true'
EMAIL_HOST: str = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT: int = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USER: str = os.getenv('EMAIL_USER', '')
EMAIL_PASSWORD: str = os.getenv('EMAIL_PASSWORD', '')
EMAIL_RECIPIENT: str = os.getenv('EMAIL_RECIPIENT', '')

# HH.ru параметры
HH_SEARCH_TEXT: str = os.getenv('HH_SEARCH_TEXT', 'Python разработчик')
HH_AREA: Optional[str] = parse_optional(os.getenv('HH_AREA', ''))
HH_SALARY_FROM: Optional[int] = parse_optional(os.getenv('HH_SALARY_FROM', ''), int)
HH_EMPLOYMENT: Optional[List[str]] = parse_list(os.getenv('HH_EMPLOYMENT', '')) or None
HH_EXPERIENCE: Optional[List[str]] = parse_list(os.getenv('HH_EXPERIENCE', '')) or None
HH_EXCLUDE_WORDS: List[str] = parse_list(os.getenv('HH_EXCLUDE_WORDS', ''))

# Интервал проверки (секунды)
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '300'))

# База данных
DB_PATH = os.getenv('DB_PATH', 'vacancies.db')

# Логирование
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'hh_tracker.log')
