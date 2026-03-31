"""Настройка логирования."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from .config import LOG_LEVEL, LOG_FILE, LOG_MAX_BYTES, LOG_BACKUP_COUNT


def setup_logging(
    level: Optional[str] = None,
    log_file: Optional[str] = None,
    console: bool = True
) -> None:
    """
    Настройка логирования.

    :param level: Уровень логирования
    :param log_file: Путь к файлу логов
    :param console: Вывод в консоль
    """
    level = level or LOG_LEVEL
    log_file = log_file or LOG_FILE

    # Создаём директорию для логов
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Формат
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    formatter = logging.Formatter(log_format)

    # Корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # File handler
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Console handler
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)


def get_logger(name: str) -> logging.Logger:
    """Получить логгер по имени."""
    return logging.getLogger(name)
