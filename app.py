"""Главное приложение HH Tracker."""

import asyncio
import signal
import logging
from typing import Optional, List

import aiohttp

from core import setup_logging, get_logger, CHECK_INTERVAL
from core.exceptions import ConfigError
from modules.storage import Database, VacancyRepository, get_database
from modules.parser import HHClient
from modules.notifier import TelegramNotifier, EmailNotifier, AbstractNotifier
from modules.bot import TelegramBot
from services import VacancyService


logger = get_logger(__name__)


class Application:
    """Основное приложение."""

    def __init__(self):
        """Инициализация приложения."""
        self.http_session: Optional[aiohttp.ClientSession] = None
        self.database: Optional[Database] = None
        self.repository: Optional[VacancyRepository] = None
        self.service: Optional[VacancyService] = None
        self.telegram_bot: Optional[TelegramBot] = None
        self.notifiers: List[AbstractNotifier] = []
        self.running = False

    async def initialize(self):
        """Инициализация компонентов приложения."""
        logger.info("🚀 Инициализация приложения...")

        # HTTP сессия
        self.http_session = aiohttp.ClientSession()

        # База данных
        self.database = get_database()
        self.repository = VacancyRepository(self.database.SessionLocal)

        # Сервис вакансий
        self.service = VacancyService(
            repository=self.repository,
            http_session=self.http_session
        )

        # Нотификаторы
        self.notifiers = await self._create_notifiers()

        # Telegram бот
        self.telegram_bot = await self._create_bot()

        logger.info("✅ Приложение инициализировано")

    async def _create_notifiers(self) -> List[AbstractNotifier]:
        """Создание нотификаторов."""
        notifiers = []

        # Telegram
        try:
            telegram = TelegramNotifier(session=self.http_session)
            if await telegram.test_connection():
                notifiers.append(telegram)
                logger.info("✅ Telegram подключен")
        except Exception as e:
            logger.warning(f"Telegram не подключен: {e}")

        # Email
        try:
            email = EmailNotifier()
            if email.test_connection():
                notifiers.append(email)
                logger.info("✅ Email подключен")
        except Exception as e:
            logger.warning(f"Email не подключен: {e}")

        return notifiers

    async def _create_bot(self) -> Optional[TelegramBot]:
        """Создание Telegram бота."""
        try:
            bot = TelegramBot(repository=self.repository)
            logger.info("✅ Telegram бот готов к запуску")
            return bot
        except ConfigError as e:
            logger.warning(f"Telegram бот не настроен: {e}")
            return None

    async def run_tracker(self, once: bool = False):
        """
        Запуск трекера вакансий.

        :param once: Однократный запуск
        """
        logger.info("🚀 Запуск трекера вакансий...")

        self.running = True
        while self.running:
            try:
                new_count = await self.service.check_vacancies()

                if new_count > 0:
                    logger.info(f"Найдено {new_count} новых вакансий")
                    # Отправка уведомлений
                    recent = self.repository.get_recent(hours=1)
                    for vacancy in recent[-new_count:]:
                        await self.service.notify_vacancy(vacancy, self.notifiers)

                if once:
                    logger.info("Однократная проверка завершена")
                    break

                # Ожидание
                for _ in range(CHECK_INTERVAL):
                    if not self.running:
                        break
                    await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Ошибка в цикле проверки: {e}", exc_info=True)
                if not self.running:
                    break
                await asyncio.sleep(10)

    def run_bot(self):
        """Запуск Telegram бота (в отдельном потоке)."""
        if self.telegram_bot:
            logger.info("🤖 Запуск Telegram бота...")
            self.telegram_bot.run()

    def stop(self):
        """Остановка приложения."""
        logger.info("🛑 Остановка приложения...")
        self.running = False

    async def shutdown(self):
        """Завершение работы."""
        logger.info("🧹 Завершение работы...")

        if self.http_session:
            await self.http_session.close()

        if self.database:
            self.database.dispose()

        logger.info("✅ Приложение остановлено")


def create_app() -> Application:
    """Фабрика приложений."""
    return Application()
