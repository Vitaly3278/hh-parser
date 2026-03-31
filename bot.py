#!/usr/bin/env python3
"""Telegram бот с кнопками для управления вакансиями."""

import logging
import signal
import sys
from datetime import datetime

from config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    DB_PATH,
)
from database import VacancyDatabase

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VacancyBot:
    """Telegram бот для просмотра вакансий."""

    def __init__(self):
        """Инициализация бота."""
        self.token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        self.db = VacancyDatabase(DB_PATH)
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.running = True
        
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Обработчик сигналов."""
        logger.info("Остановка бота...")
        self.running = False

    def _make_request(self, method: str, data: dict) -> dict:
        """Вызов API Telegram."""
        import requests
        url = f"{self.base_url}/{method}"
        try:
            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"API error: {e}")
            return {}

    def get_updates(self, offset: int = 0) -> list:
        """Получение обновлений."""
        data = {"timeout": 30, "offset": offset}
        result = self._make_request("getUpdates", data)
        return result.get("result", [])

    def send_message(self, text: str, reply_markup: dict = None):
        """Отправка сообщения."""
        data = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",
        }
        if reply_markup:
            data["reply_markup"] = reply_markup
        return self._make_request("sendMessage", data)

    def answer_callback(self, callback_query_id: str, text: str = None):
        """Ответ на callback."""
        data = {"callback_query_id": callback_query_id}
        if text:
            data["text"] = text
            data["show_alert"] = False
        self._make_request("answerCallbackQuery", data)

    def edit_message(self, message_id: int, text: str, reply_markup: dict = None):
        """Редактирование сообщения."""
        data = {
            "chat_id": self.chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": "HTML",
        }
        if reply_markup:
            data["reply_markup"] = reply_markup
        return self._make_request("editMessageText", data)

    def get_menu_keyboard(self):
        """Главное меню."""
        return {
            "inline_keyboard": [
                [{"text": "📊 Статистика", "callback_data": "stats"}],
                [{"text": "📋 Последние вакансии", "callback_data": "last_10"}],
                [{"text": "🔍 Все вакансии", "callback_data": "all_vacancies"}],
                [{"text": "🗑 Очистить старые", "callback_data": "clear_old"}],
            ]
        }

    def handle_command(self, command: str):
        """Обработка команд."""
        if command == "/start":
            message = (
                "👋 <b>Привет! Я HH Tracker Bot</b>\n\n"
                "Я умею:\n"
                "• Показывать статистику вакансий\n"
                "• Выводить последние вакансии\n"
                "• Очищать старую базу\n\n"
                "Выберите действие:"
            )
            self.send_message(message, self.get_menu_keyboard())
        
        elif command == "/stats":
            self.show_stats()
        
        elif command == "/vacancies":
            self.show_vacancies(limit=10)
        
        elif command == "/menu":
            self.send_message("Главное меню:", self.get_menu_keyboard())
        
        else:
            self.send_message(
                "❓ Неизвестная команда\n\n"
                "Доступные команды:\n"
                "/start - Главное меню\n"
                "/stats - Статистика\n"
                "/vacancies - Последние вакансии\n"
                "/menu - Показать меню"
            )

    def show_stats(self):
        """Показать статистику."""
        stats = self.db.get_stats()
        message = (
            f"📊 <b>Статистика вакансий</b>\n\n"
            f"Всего в базе: <b>{stats['total']}</b>\n"
            f"За сегодня: <b>{stats['today']}</b>\n"
            f"За неделю: <b>{stats['week']}</b>\n"
        )
        if stats.get('avg_salary'):
            message += f"Средняя ЗП: <b>{stats['avg_salary']}</b>\n"
        
        keyboard = {
            "inline_keyboard": [
                [{"text": "📋 Последние", "callback_data": "last_10"}],
                [{"text": "🔙 Меню", "callback_data": "menu"}],
            ]
        }
        self.send_message(message, keyboard)

    def show_vacancies(self, limit: int = 10, page: int = 0):
        """Показать вакансии."""
        vacancies = self.db.get_all_vacancies()
        
        if not vacancies:
            self.send_message("📭 В базе нет вакансий")
            return
        
        per_page = 5
        start = page * per_page
        end = start + per_page
        page_vacancies = vacancies[start:end]
        total_pages = (len(vacancies) + per_page - 1) // per_page

        message = f"📋 <b>Вакансии ({start+1}-{min(end, len(vacancies))} из {len(vacancies)})</b>\n\n"

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
            
            message += f"{i}. <b>{v.get('name', 'Б/н')}</b>\n"
            message += f"   🏢 {v.get('employer', 'Б/н')}{salary}\n"
            message += f"   📍 {v.get('area', 'Б/н')}\n"
            url = v.get('url', '#')
            message += f"   🔗 <a href='{url}'>Ссылка</a>\n\n"

        keyboard = []
        nav_row = []
        
        if page > 0:
            nav_row.append({"text": "⬅️", "callback_data": f"page_{page-1}"})
        
        if page < total_pages - 1:
            nav_row.append({"text": "➡️", "callback_data": f"page_{page+1}"})
        
        if nav_row:
            keyboard.append(nav_row)
        
        keyboard.append([{"text": "🔙 Меню", "callback_data": "menu"}])

        self.send_message(message, {"inline_keyboard": keyboard})

    def clear_old_vacancies(self, days: int = 30):
        """Очистка старых вакансий."""
        deleted = self.db.clear_old_vacancies(days)
        message = f"🗑 Удалено старых вакансий: <b>{deleted}</b>"
        self.send_message(message)

    def handle_callback(self, callback: dict):
        """Обработка callback от кнопок."""
        callback_id = callback.get("id")
        data = callback.get("data", "")
        message = callback.get("message", {})
        message_id = message.get("message_id") if message else None

        logger.info(f"Callback: {data}")
        self.answer_callback(callback_id)

        if data == "menu":
            self.send_message("Главное меню:", self.get_menu_keyboard())
        
        elif data == "stats":
            self.show_stats()
        
        elif data == "last_10":
            self.show_vacancies(limit=10)
        
        elif data == "all_vacancies":
            self.show_vacancies(limit=100)
        
        elif data == "clear_old":
            self.clear_old_vacancies()
        
        elif data.startswith("page_"):
            page = int(data.split("_")[1])
            self.show_vacancies(limit=100, page=page)

    def run(self):
        """Запуск бота."""
        logger.info("🤖 Запуск HH Tracker Bot...")
        
        # Проверка подключения
        result = self._make_request("getMe", {})
        if not result.get("ok"):
            logger.error("❌ Ошибка подключения к Telegram API")
            return
        
        bot_name = result.get("result", {}).get("username", "Bot")
        logger.info(f"✅ Бот @{bot_name} запущен")
        
        # Отправляем приветственное сообщение
        self.send_message(
            "🤖 <b>HH Tracker Bot запущен!</b>\n\n"
            f"Я @{bot_name}\n"
            "Используйте /start для начала работы",
            self.get_menu_keyboard()
        )
        
        offset = 0
        logger.info("Ожидание сообщений...")
        
        while self.running:
            try:
                updates = self.get_updates(offset)
                
                for update in updates:
                    offset = max(offset, update.get("update_id", 0) + 1)
                    
                    # Сообщение
                    message = update.get("message")
                    if message:
                        chat_id = message.get("chat", {}).get("id")
                        if str(chat_id) != str(self.chat_id):
                            continue
                        
                        text = message.get("text", "")
                        if text.startswith("/"):
                            command = text.split()[0]
                            self.handle_command(command)
                    
                    # Callback от кнопки
                    callback = update.get("callback_query")
                    if callback:
                        self.handle_callback(callback)
                
            except Exception as e:
                logger.error(f"Ошибка в цикле: {e}", exc_info=True)
        
        logger.info("Бот остановлен")


def main():
    """Точка входа."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error("❌ Не настроен TELEGRAM_BOT_TOKEN или TELEGRAM_CHAT_ID")
        sys.exit(1)
    
    bot = VacancyBot()
    bot.run()


if __name__ == "__main__":
    main()
