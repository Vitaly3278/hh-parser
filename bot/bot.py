"""Telegram бот на python-telegram-bot."""

import asyncio
import logging
from typing import Optional

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from core import TELEGRAM_BOT_TOKEN
from core.exceptions import ConfigError
from bot.handlers import CommandHandlers
from bot.rate_limiter import RateLimiter
from storage.repository import VacancyRepository


logger = logging.getLogger(__name__)


class TelegramBot:
    """Telegram бот для управления вакансиями."""

    def __init__(
        self,
        token: Optional[str] = None,
        repository: Optional[VacancyRepository] = None,
        allowed_chat_ids: Optional[list] = None
    ):
        """
        Инициализация бота.

        :param token: Токен бота
        :param repository: Репозиторий вакансий
        :param allowed_chat_ids: Разрешённые chat_id
        """
        self.token = token or TELEGRAM_BOT_TOKEN
        self.repository: Optional[VacancyRepository] = repository
        self.allowed_chat_ids = allowed_chat_ids

        if not self.token:
            raise ConfigError("TELEGRAM_BOT_TOKEN не настроен")

        self.application: Optional[Application] = None
        self.rate_limiter = RateLimiter()
        self.handlers: Optional[CommandHandlers] = None

    def _create_handlers(self) -> CommandHandlers:
        """Создание обработчиков команд."""
        if self.repository is None:
            raise ConfigError("Repository не инициализирован")
        return CommandHandlers(
            repository=self.repository,
            allowed_chat_ids=self.allowed_chat_ids
        )

    async def _error_handler(self, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ошибок."""
        logger.error(f"Exception caused error: {context.error}")

    async def _error_handler_wrapper(self, context: ContextTypes.DEFAULT_TYPE):
        """Обертка для error_handler."""
        await self._error_handler(context)

    async def start(self) -> None:
        """Асинхронный запуск бота."""
        logger.info("🤖 Запуск HH Tracker Bot...")

        # Создаём обработчики
        self.handlers = self._create_handlers()

        # Создаём приложение
        self.application = (
            Application.builder()
            .token(self.token)
            .build()
        )

        # Добавляем обработчики команд
        self.application.add_handler(CommandHandler("start", self.handlers.start_command))
        self.application.add_handler(CommandHandler("stats", self.handlers.stats_command))
        self.application.add_handler(CommandHandler("vacancies", self.handlers.vacancies_command))
        self.application.add_handler(CommandHandler("menu", self.handlers.menu_command))
        self.application.add_handler(CommandHandler("help", self.handlers.help_command))
        self.application.add_handler(CommandHandler("next", self.handlers.next_command))
        self.application.add_handler(CommandHandler("prev", self.handlers.prev_command))

        # Обработчик ошибок
        self.application.add_error_handler(self._error_handler_wrapper)

        # Запуск
        logger.info("Ожидание сообщений...")
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling(allowed_updates=Update.ALL_TYPES)

        # Держим бота запущенным
        while True:
            await asyncio.sleep(1)

    def run(self) -> None:
        """Запуск бота (синхронная обертка)."""
        asyncio.run(self.start())
