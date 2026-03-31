"""Telegram бот на python-telegram-bot."""

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
from modules.bot.handlers import CommandHandlers
from modules.bot.rate_limiter import RateLimiter


logger = logging.getLogger(__name__)


class TelegramBot:
    """Telegram бот для управления вакансиями."""

    def __init__(
        self,
        token: Optional[str] = None,
        repository=None,
        allowed_chat_ids: Optional[list] = None
    ):
        """
        Инициализация бота.

        :param token: Токен бота
        :param repository: Репозиторий вакансий
        :param allowed_chat_ids: Разрешённые chat_id
        """
        self.token = token or TELEGRAM_BOT_TOKEN
        self.repository = repository
        self.allowed_chat_ids = allowed_chat_ids

        if not self.token:
            raise ConfigError("TELEGRAM_BOT_TOKEN не настроен")

        self.application: Optional[Application] = None
        self.rate_limiter = RateLimiter()
        self.handlers: Optional[CommandHandlers] = None

    def _create_handlers(self) -> CommandHandlers:
        """Создание обработчиков команд."""
        return CommandHandlers(
            repository=self.repository,
            allowed_chat_ids=self.allowed_chat_ids
        )

    async def _error_handler(self, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ошибок."""
        logger.error(f"Exception caused error: {context.error}")

    def run(self) -> None:
        """Запуск бота."""
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
        self.application.add_error_handler(self._error_handler)

        # Запуск
        logger.info("Ожидание сообщений...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)
