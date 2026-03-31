#!/usr/bin/env python3
"""Асинхронный Telegram бот для управления вакансиями на python-telegram-bot."""

import logging
import signal
import sys
from datetime import datetime
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from telegram.error import TelegramError

from config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    DB_PATH,
    ALLOWED_CHAT_IDS,  # Список разрешённых chat_id
)
from database import VacancyDatabase

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RateLimiter:
    """Ограничитель частоты запросов от пользователя."""

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: dict[int, list[float]] = {}

    def is_allowed(self, user_id: int) -> bool:
        """Проверка, разрешён ли запрос от пользователя."""
        now = datetime.now().timestamp()
        
        if user_id not in self.requests:
            self.requests[user_id] = []
        
        # Удаляем старые запросы
        self.requests[user_id] = [
            ts for ts in self.requests[user_id]
            if now - ts < self.window_seconds
        ]
        
        # Проверяем лимит
        if len(self.requests[user_id]) >= self.max_requests:
            return False
        
        self.requests[user_id].append(now)
        return True

    def get_wait_time(self, user_id: int) -> float:
        """Время ожидания до следующего запроса."""
        if user_id not in self.requests or not self.requests[user_id]:
            return 0
        
        oldest = min(self.requests[user_id])
        wait = self.window_seconds - (datetime.now().timestamp() - oldest)
        return max(0, wait)


class VacancyBot:
    """Telegram бот для просмотра вакансий."""

    def __init__(self):
        """Инициализация бота."""
        self.token = TELEGRAM_BOT_TOKEN
        self.main_chat_id = TELEGRAM_CHAT_ID
        self.db = VacancyDatabase(DB_PATH)
        self.rate_limiter = RateLimiter(max_requests=10, window_seconds=60)
        self.application: Optional[Application] = None
        self.running = False

        # Разрешённые chat_id (из конфига + основной)
        self.allowed_chat_ids = set(ALLOWED_CHAT_IDS) if ALLOWED_CHAT_IDS else set()
        if self.main_chat_id:
            self.allowed_chat_ids.add(self.main_chat_id)

    def is_authorized(self, chat_id: int) -> bool:
        """Проверка авторизации пользователя."""
        if not self.allowed_chat_ids:
            return True  # Если список пустой, разрешаем всем
        return str(chat_id) in self.allowed_chat_ids or chat_id in self.allowed_chat_ids

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /start."""
        if not update.effective_chat:
            return
            
        chat_id = update.effective_chat.id

        if not self.is_authorized(chat_id):
            if update.effective_message:
                await update.effective_message.reply_text("❌ Доступ запрещён")
            return

        message = (
            "👋 <b>Привет! Я HH Tracker Bot</b>\n\n"
            "Я умею:\n"
            "• Показывать статистику вакансий\n"
            "• Выводить последние вакансии\n"
            "• Очищать старую базу\n\n"
            "<b>Доступные команды:</b>\n"
            "/stats - Статистика вакансий\n"
            "/vacancies - Последние 10 вакансий\n"
            "/menu - Показать это сообщение\n"
            "/help - Помощь\n"
            "/next - Следующая страница вакансий\n"
            "/prev - Предыдущая страница"
        )
        if update.effective_message:
            await update.effective_message.reply_text(message, parse_mode="HTML")
        await self.show_vacancies(update, context, limit=10)

    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /stats."""
        if not update.effective_chat:
            return
            
        chat_id = update.effective_chat.id

        if not self.is_authorized(chat_id):
            if update.effective_message:
                await update.effective_message.reply_text("❌ Доступ запрещён")
            return

        if not self.rate_limiter.is_allowed(chat_id):
            wait = self.rate_limiter.get_wait_time(chat_id)
            if update.effective_message:
                await update.effective_message.reply_text(
                    f"⏳ Слишком много запросов. Подождите {wait:.0f} сек."
                )
            return

        if update.effective_message:
            await self._show_stats(update.effective_message)

    async def vacancies_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /vacancies."""
        if not update.effective_chat:
            return
            
        chat_id = update.effective_chat.id

        if not self.is_authorized(chat_id):
            if update.effective_message:
                await update.effective_message.reply_text("❌ Доступ запрещён")
            return

        if not self.rate_limiter.is_allowed(chat_id):
            wait = self.rate_limiter.get_wait_time(chat_id)
            if update.effective_message:
                await update.effective_message.reply_text(
                    f"⏳ Слишком много запросов. Подождите {wait:.0f} сек."
                )
            return

        await self.show_vacancies(update, context, limit=10)

    async def menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /menu."""
        if not update.effective_chat:
            return
            
        chat_id = update.effective_chat.id

        if not self.is_authorized(chat_id):
            if update.effective_message:
                await update.effective_message.reply_text("❌ Доступ запрещён")
            return

        message = (
            "📋 <b>Главное меню</b>\n\n"
            "<b>Доступные команды:</b>\n"
            "/start - Приветствие и вакансии\n"
            "/stats - Статистика вакансий\n"
            "/vacancies - Последние 10 вакансий\n"
            "/next - Следующая страница\n"
            "/prev - Предыдущая страница\n"
            "/help - Помощь"
        )
        if update.effective_message:
            await update.effective_message.reply_text(message, parse_mode="HTML")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /help."""
        if not update.effective_chat:
            return
            
        chat_id = update.effective_chat.id

        if not self.is_authorized(chat_id):
            if update.effective_message:
                await update.effective_message.reply_text("❌ Доступ запрещён")
            return

        message = (
            "❓ <b>Помощь</b>\n\n"
            "<b>Команды управления:</b>\n"
            "/start - Запуск бота, показ последних вакансий\n"
            "/stats - Статистика по базе вакансий\n"
            "/vacancies - Показать 10 последних вакансий\n"
            "/menu - Главное меню\n"
            "/next - Следующая страница вакансий\n"
            "/prev - Предыдущая страница вакансий\n"
            "/help - Эта справка\n\n"
            "<b>Ограничения:</b>\n"
            "• Максимум 10 запросов в минуту\n"
            "• Доступ только для авторизованных пользователей"
        )
        if update.effective_message:
            await update.effective_message.reply_text(message, parse_mode="HTML")

    async def next_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /next."""
        if not update.effective_chat:
            return
            
        chat_id = update.effective_chat.id

        if not self.is_authorized(chat_id):
            if update.effective_message:
                await update.effective_message.reply_text("❌ Доступ запрещён")
            return

        # Получаем текущую страницу из context
        current_page = context.user_data.get('vacancies_page', 0) if context.user_data is not None else 0
        if context.user_data is not None:
            context.user_data['vacancies_page'] = current_page + 1

        await self.show_vacancies(update, context, limit=10, page=current_page + 1)

    async def prev_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /prev."""
        if not update.effective_chat:
            return
            
        chat_id = update.effective_chat.id

        if not self.is_authorized(chat_id):
            if update.effective_message:
                await update.effective_message.reply_text("❌ Доступ запрещён")
            return

        current_page = max(0, context.user_data.get('vacancies_page', 0) - 1)
        if context.user_data is not None:
            context.user_data['vacancies_page'] = current_page

        await self.show_vacancies(update, context, limit=10, page=current_page)

    async def _show_stats(self, message):
        """Показать статистику."""
        try:
            stats = self.db.get_stats()
            text = (
                f"📊 <b>Статистика вакансий</b>\n\n"
                f"Всего в базе: <b>{stats['total']}</b>\n"
                f"За сегодня: <b>{stats['today']}</b>\n"
                f"За неделю: <b>{stats['week']}</b>\n"
            )
            if stats.get('avg_salary'):
                text += f"Средняя ЗП: <b>{stats['avg_salary']}</b>\n"

            await message.reply_text(text, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Ошибка при показе статистики: {e}")
            await message.reply_text("❌ Ошибка при получении статистики")

    async def show_vacancies(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        limit: int = 10,
        page: Optional[int] = None
    ):
        """Показать вакансии."""
        try:
            vacancies = self.db.get_all_vacancies()

            if not vacancies:
                if update.effective_message:
                    await update.effective_message.reply_text("📭 В базе нет вакансий")
                return

            # Если страница не указана, берём из context или 0
            if page is None:
                page = context.user_data.get('vacancies_page', 0) if context.user_data is not None else 0

            per_page = 5
            total_pages = (len(vacancies) + per_page - 1) // per_page

            # Ограничиваем страницу
            page = max(0, min(page, total_pages - 1))
            if context.user_data is not None:
                context.user_data['vacancies_page'] = page

            start = page * per_page
            end = start + per_page
            page_vacancies = vacancies[start:end]

            text = f"📋 <b>Вакансии ({start+1}-{min(end, len(vacancies))} из {len(vacancies)})</b>\n\n"

            for i, v in enumerate(page_vacancies, start + 1):
                salary = ""
                if v.get('salary_from') or v.get('salary_to'):
                    from_s = v.get('salary_from', '')
                    to_s = v.get('salary_to', '')
                    curr = v.get('currency', 'RUR')
                    if from_s and to_s:
                        salary = f" | 💰 {from_s}-{to_s} {curr}"
                    elif from_s:
                        salary = f" | 💰 от {from_s} {curr}"

                text += f"{i}. <b>{v.get('name', 'Б/н')}</b>\n"
                text += f"   🏢 {v.get('employer', 'Б/н')}{salary}\n"
                text += f"   📍 {v.get('area', 'Б/н')}\n"
                url = v.get('url', '#')
                text += f"   🔗 <a href='{url}'>Ссылка</a>\n\n"

            # Добавляем навигацию
            if page < total_pages - 1:
                text += f"\n<i>Страница {page + 1} из {total_pages}</i>\n"
                text += "<i>Используйте /next для следующей страницы</i>"
            elif page > 0:
                text += f"\n<i>Страница {page + 1} из {total_pages}</i>\n"
                text += "<i>Используйте /prev для предыдущей страницы</i>"

            if update.effective_message:
                await update.effective_message.reply_text(text, parse_mode="HTML")

        except Exception as e:
            logger.error(f"Ошибка при показе вакансий: {e}", exc_info=True)
            if update.effective_message:
                await update.effective_message.reply_text("❌ Ошибка при получении вакансий")

    async def clear_old_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Очистка старых вакансий."""
        if not update.effective_chat:
            return
            
        chat_id = update.effective_chat.id

        if not self.is_authorized(chat_id):
            if update.effective_message:
                await update.effective_message.reply_text("❌ Доступ запрещён")
            return

        try:
            deleted = self.db.clear_old_vacancies(days=30)
            if update.effective_message:
                await update.effective_message.reply_text(
                    f"🗑 Удалено старых вакансий: <b>{deleted}</b>",
                    parse_mode="HTML"
                )
        except Exception as e:
            logger.error(f"Ошибка при очистке: {e}")
            if update.effective_message:
                await update.effective_message.reply_text("❌ Ошибка при очистке старых вакансий")

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ошибок."""
        logger.error(f"Update {update} caused error: {context.error}")
        
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ Произошла ошибка при обработке запроса"
            )

    async def post_init(self, application: Application):
        """Инициализация после запуска."""
        logger.info("✅ Бот инициализирован")

    def run(self):
        """Запуск бота."""
        logger.info("🤖 Запуск HH Tracker Bot на python-telegram-bot...")

        # Создаём приложение
        self.application = (
            Application.builder()
            .token(self.token)
            .post_init(self.post_init)
            .build()
        )

        # Добавляем обработчики команд
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("vacancies", self.vacancies_command))
        self.application.add_handler(CommandHandler("menu", self.menu_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("next", self.next_command))
        self.application.add_handler(CommandHandler("prev", self.prev_command))
        self.application.add_handler(CommandHandler("clear_old", self.clear_old_command))

        # Обработчик ошибок
        self.application.add_error_handler(self.error_handler)

        # Запуск
        logger.info("Ожидание сообщений...")
        self.running = True
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    """Точка входа."""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("❌ Не настроен TELEGRAM_BOT_TOKEN")
        sys.exit(1)

    bot = VacancyBot()
    bot.run()


if __name__ == "__main__":
    main()
