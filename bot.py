#!/usr/bin/env python3
"""Telegram бот HH Tracker."""

from modules.bot import TelegramBot
from modules.storage import get_database, VacancyRepository


def main():
    """Запуск Telegram бота."""
    # Инициализация БД
    db = get_database()
    repository = VacancyRepository(db.SessionLocal)

    # Создание и запуск бота
    bot = TelegramBot(repository=repository)
    bot.run()


if __name__ == "__main__":
    main()
