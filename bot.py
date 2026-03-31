#!/usr/bin/env python3
"""Telegram бот HH Tracker."""

import asyncio
import aiohttp

from core import get_logger
from modules.bot import TelegramBot
from modules.storage import get_database, VacancyRepository
from modules.parser import HHClient
from services import VacancyService


logger = get_logger(__name__)


async def load_initial_vacancies(repository, http_session):
    """
    Загрузка начальных вакансий при старте.

    :param repository: Репозиторий вакансий
    :param http_session: HTTP сессия
    :return: Количество загруженных вакансий
    """
    # Проверяем есть ли вакансии в базе
    count = repository.count()
    if count > 0:
        logger.info(f"✅ В базе уже есть {count} вакансий")
        return 0

    # Загружаем с hh.ru
    logger.info("📥 База пуста. Загрузка вакансий с hh.ru...")

    service = VacancyService(repository=repository, http_session=http_session)
    new_count = await service.check_vacancies()

    if new_count > 0:
        logger.info(f"✅ Загружено {new_count} вакансий")
    else:
        logger.warning("⚠️ Не удалось загрузить вакансии")

    return new_count


def main():
    """Запуск Telegram бота."""
    # Инициализация БД
    db = get_database()
    repository = VacancyRepository(db.SessionLocal)

    # Загрузка начальных вакансий
    logger.info("🚀 Запуск бота...")
    
    async def init():
        async with aiohttp.ClientSession() as http_session:
            loaded = await load_initial_vacancies(repository, http_session)
            if loaded > 0:
                logger.info(f"✅ Загружено {loaded} вакансий в базу")

    asyncio.run(init())

    # Создание и запуск бота
    bot = TelegramBot(repository=repository)
    bot.run()


if __name__ == "__main__":
    main()
