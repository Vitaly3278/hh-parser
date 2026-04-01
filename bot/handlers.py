"""Обработчики команд бота."""

import logging
from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes

from core import ALLOWED_CHAT_IDS, TELEGRAM_CHAT_ID
from core.exceptions import UnauthorizedError
from storage.repository import VacancyRepository


logger = logging.getLogger(__name__)


class CommandHandlers:
    """Обработчики команд Telegram бота."""

    def __init__(
        self,
        repository: VacancyRepository,
        allowed_chat_ids: Optional[list] = None
    ):
        """
        Инициализация обработчиков.

        :param repository: Репозиторий вакансий
        :param allowed_chat_ids: Разрешённые chat_id
        """
        self.repository = repository
        self.allowed_chat_ids = set(allowed_chat_ids or ALLOWED_CHAT_IDS)
        if TELEGRAM_CHAT_ID:
            self.allowed_chat_ids.add(TELEGRAM_CHAT_ID)

        # Хранилище состояния для пагинации
        self.user_pages: dict[int, int] = {}

    def is_authorized(self, chat_id: int) -> bool:
        """Проверка авторизации пользователя."""
        if not self.allowed_chat_ids:
            return True
        return str(chat_id) in self.allowed_chat_ids or chat_id in self.allowed_chat_ids

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /start."""
        logger.info(f"Получена команда /start от chat_id={update.effective_chat.id if update.effective_chat else 'None'}")
        
        if not update.effective_chat or not update.effective_message:
            logger.warning("Нет effective_chat или effective_message")
            return

        chat_id = update.effective_chat.id
        logger.info(f"Проверка авторизации для chat_id={chat_id}")

        if not self.is_authorized(chat_id):
            logger.warning(f"Неавторизованный доступ: chat_id={chat_id}")
            await update.effective_message.reply_text("❌ Доступ запрещён")
            return

        # Проверяем количество вакансий
        count = self.repository.count()
        
        if count == 0:
            message = (
                "👋 <b>Привет! Я HH Tracker Bot</b>\n\n"
                "📭 В базе пока нет вакансий\n"
                "Запустите трекер для поиска вакансий:\n"
                "<code>python main.py --tracker-only</code>\n\n"
                "<b>Доступные команды:</b>\n"
                "/stats - Статистика вакансий\n"
                "/vacancies - Последние 10 вакансий\n"
                "/menu - Показать это сообщение\n"
                "/help - Помощь"
            )
            await update.effective_message.reply_text(message, parse_mode="HTML")
            return

        message = (
            "👋 <b>Привет! Я HH Tracker Bot</b>\n\n"
            f"✅ В базе <b>{count}</b> вакансий\n\n"
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
        await update.effective_message.reply_text(message, parse_mode="HTML")
        
        # Показываем 5 последних вакансий
        await self._show_vacancies(update, context, limit=5)

    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /stats."""
        if not update.effective_message:
            return

        chat_id = update.effective_chat.id if update.effective_chat else None
        if chat_id and not self.is_authorized(chat_id):
            await update.effective_message.reply_text("❌ Доступ запрещён")
            return

        try:
            stats = self.repository.get_stats()
            text = (
                f"📊 <b>Статистика вакансий</b>\n\n"
                f"Всего в базе: <b>{stats['total']}</b>\n"
                f"За сегодня: <b>{stats['today']}</b>\n"
                f"За неделю: <b>{stats['week']}</b>\n"
            )
            if stats.get('avg_salary'):
                text += f"Средняя ЗП: <b>{stats['avg_salary']}</b>\n"

            await update.effective_message.reply_text(text, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Ошибка при показе статистики: {e}")
            await update.effective_message.reply_text("❌ Ошибка при получении статистики")

    async def vacancies_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /vacancies."""
        logger.info(f"Получена команда /vacancies от chat_id={update.effective_chat.id if update.effective_chat else 'None'}")
        
        if not update.effective_message:
            logger.warning("Нет effective_message")
            return
            
        if not self.is_authorized(update.effective_chat.id if update.effective_chat else 0):
            logger.warning(f"Неавторизованный доступ: chat_id={update.effective_chat.id if update.effective_chat else 'None'}")
            await update.effective_message.reply_text("❌ Доступ запрещён")
            return
            
        await self._show_vacancies(update, context, limit=10)

    async def menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /menu."""
        if not update.effective_message:
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
        await update.effective_message.reply_text(message, parse_mode="HTML")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /help."""
        if not update.effective_message:
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
            "/help - Эта справка"
        )
        await update.effective_message.reply_text(message, parse_mode="HTML")

    async def next_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /next."""
        if not update.effective_chat or not update.effective_message:
            return

        chat_id = update.effective_chat.id
        if not self.is_authorized(chat_id):
            await update.effective_message.reply_text("❌ Доступ запрещён")
            return

        current_page = self.user_pages.get(chat_id, 0)
        self.user_pages[chat_id] = current_page + 1

        await self._show_vacancies(update, context, limit=10, page=current_page + 1)

    async def prev_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /prev."""
        if not update.effective_chat or not update.effective_message:
            return

        chat_id = update.effective_chat.id
        if not self.is_authorized(chat_id):
            await update.effective_message.reply_text("❌ Доступ запрещён")
            return

        current_page = max(0, self.user_pages.get(chat_id, 0) - 1)
        self.user_pages[chat_id] = current_page

        await self._show_vacancies(update, context, limit=10, page=current_page)

    async def _show_vacancies(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        limit: int = 10,
        page: Optional[int] = None
    ):
        """Показать вакансии."""
        if not update.effective_message:
            return

        try:
            vacancies = self.repository.get_all(limit=limit)

            if not vacancies:
                await update.effective_message.reply_text("📭 В базе нет вакансий")
                return

            # Показываем все вакансии в пределах limit (без пагинации для /vacancies)
            text = f"📋 <b>Последние {len(vacancies)} вакансий</b>\n\n"

            for i, v in enumerate(vacancies, 1):
                salary = ""
                if v.has_salary():
                    salary = f" | 💰 {v.formatted_salary()}"

                text += f"{i}. <b>{v.name}</b>\n"
                text += f"   🏢 {v.employer or 'Б/н'}{salary}\n"
                text += f"   📍 {v.area or 'Б/н'}\n"
                text += f"   🔗 <a href='{v.url or '#'}'>Ссылка</a>\n\n"

            if len(vacancies) >= limit:
                text += f"\n<i>Показано {limit} из {self.repository.count()} вакансий</i>\n"

            await update.effective_message.reply_text(text, parse_mode="HTML")

        except Exception as e:
            logger.error(f"Ошибка при показе вакансий: {e}", exc_info=True)
            await update.effective_message.reply_text("❌ Ошибка при получении вакансий")
