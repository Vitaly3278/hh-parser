"""Конфигурация приложения."""

import os
from typing import Optional, List
from dotenv import load_dotenv

load_dotenv()


def parse_list(value: str) -> List[str]:
    """Парсинг строки в список."""
    if not value:
        return []
    return [item.strip() for item in value.split(',') if item.strip()]


def parse_optional(value: str, type_func=None):
    """Парсинг опционального значения."""
    if not value or value.lower() in ('none', 'null', ''):
        return None
    return type_func(value) if type_func else value


# =============================================================================
# Telegram
# =============================================================================
TELEGRAM_BOT_TOKEN: str = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID: str = os.getenv('TELEGRAM_CHAT_ID', '')
ALLOWED_CHAT_IDS: List[str] = parse_list(os.getenv('ALLOWED_CHAT_IDS', ''))


# =============================================================================
# Email уведомления
# =============================================================================
EMAIL_ENABLED: bool = os.getenv('EMAIL_ENABLED', 'false').lower() == 'true'
EMAIL_HOST: str = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT: int = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USER: str = os.getenv('EMAIL_USER', '')
EMAIL_PASSWORD: str = os.getenv('EMAIL_PASSWORD', '')
EMAIL_RECIPIENT: str = os.getenv('EMAIL_RECIPIENT', '')


# =============================================================================
# HH.ru параметры поиска
# =============================================================================
HH_SEARCH_TEXT: str = os.getenv('HH_SEARCH_TEXT', 'Python разработчик')
HH_AREA: Optional[str] = parse_optional(os.getenv('HH_AREA', ''))
HH_SALARY_FROM = parse_optional(os.getenv('HH_SALARY_FROM', ''), int)
HH_EMPLOYMENT: Optional[List[str]] = parse_list(os.getenv('HH_EMPLOYMENT', '')) or None
HH_EXPERIENCE: Optional[List[str]] = parse_list(os.getenv('HH_EXPERIENCE', '')) or None
HH_EXCLUDE_WORDS: List[str] = parse_list(os.getenv('HH_EXCLUDE_WORDS', ''))


# =============================================================================
# Интервал проверки (секунды)
# =============================================================================
CHECK_INTERVAL: int = int(os.getenv('CHECK_INTERVAL', '300'))


# =============================================================================
# База данных
# =============================================================================
DB_PATH: str = os.getenv('DB_PATH', os.path.expanduser('~/hh_data/vacancies.db'))
DATA_DIR: str = os.getenv('DATA_DIR', os.path.expanduser('~/hh_data'))


# =============================================================================
# Логирование
# =============================================================================
LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE: str = os.getenv('LOG_FILE', 'logs/hh_tracker.log')
LOG_MAX_BYTES: int = int(os.getenv('LOG_MAX_BYTES', '10485760'))  # 10 MB
LOG_BACKUP_COUNT: int = int(os.getenv('LOG_BACKUP_COUNT', '5'))


# =============================================================================
# Веб-интерфейс
# =============================================================================
WEB_HOST: str = os.getenv('WEB_HOST', '0.0.0.0')
WEB_PORT: int = int(os.getenv('WEB_PORT', '8000'))


# =============================================================================
# Rate limiting для бота
# =============================================================================
BOT_RATE_LIMIT: int = int(os.getenv('BOT_RATE_LIMIT', '10'))  # запросов
BOT_RATE_WINDOW: int = int(os.getenv('BOT_RATE_WINDOW', '60'))  # секунд
