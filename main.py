#!/usr/bin/env python3
"""
Приложение для отслеживания новых вакансий на hh.ru
с отправкой уведомлений в Telegram, Email и Slack.
"""

import time
import signal
import sys
import argparse
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler

from config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    EMAIL_ENABLED,
    EMAIL_HOST,
    EMAIL_PORT,
    EMAIL_USER,
    EMAIL_PASSWORD,
    EMAIL_RECIPIENT,
    SLACK_ENABLED,
    SLACK_WEBHOOK_URL,
    HH_SEARCH_TEXT,
    HH_AREA,
    HH_SALARY_FROM,
    HH_EMPLOYMENT,
    HH_EXPERIENCE,
    HH_EXCLUDE_WORDS,
    CHECK_INTERVAL,
    DB_PATH,
    LOG_LEVEL,
    LOG_FILE,
)
from hh_parser import HHParser
from telegram_bot import TelegramBot
from email_bot import EmailNotifier
from slack_bot import SlackBot
from database import VacancyDatabase


def setup_logging(level: str, log_file: str):
    """Настройка логирования."""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Создаём обработчики
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    console_handler = logging.StreamHandler()
    
    # Уровни логирования
    file_handler.setLevel(level)
    console_handler.setLevel(level)
    
    # Формат
    formatter = logging.Formatter(log_format)
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Настройка корневого логгера
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)


class VacancyTracker:
    """Трекер вакансий с уведомлениями."""

    def __init__(self):
        """Инициализация трекера."""
        self.logger = logging.getLogger(__name__)
        
        # Инициализация компонентов
        area = HH_AREA if HH_AREA else None
        self.parser = HHParser(area=area)
        self.db = VacancyDatabase(DB_PATH)
        
        # Нотификаторы
        self.telegram_bot = TelegramBot(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID) if TELEGRAM_BOT_TOKEN else None
        
        self.email_bot = None
        if EMAIL_ENABLED and all([EMAIL_HOST, EMAIL_USER, EMAIL_PASSWORD, EMAIL_RECIPIENT]):
            self.email_bot = EmailNotifier(
                EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASSWORD, EMAIL_RECIPIENT
            )
        
        self.slack_bot = None
        if SLACK_ENABLED and SLACK_WEBHOOK_URL:
            self.slack_bot = SlackBot(SLACK_WEBHOOK_URL)
        
        self.running = True

        # Настройка обработки сигналов
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Обработчик сигналов завершения."""
        self.logger.info("🛑 Получен сигнал завершения. Остановка...")
        self.running = False

    def check_vacancies(self) -> int:
        """
        Проверка новых вакансий.

        :return: Количество новых вакансий
        """
        self.logger.info(f"Проверка вакансий... (запрос: {HH_SEARCH_TEXT})")

        # Поиск вакансий
        result = self.parser.search_vacancies(
            search_text=HH_SEARCH_TEXT,
            salary_from=HH_SALARY_FROM,
            employment=HH_EMPLOYMENT,
            experience=HH_EXPERIENCE,
        )

        items = result.get("items", [])
        found = result.get("found", 0)

        self.logger.info(f"Найдено вакансий: {found}, получено: {len(items)}")

        # Фильтрация по исключающим словам
        if HH_EXCLUDE_WORDS:
            items = self.parser.filter_by_exclude_words(items, HH_EXCLUDE_WORDS)
            self.logger.info(f"После фильтрации: {len(items)} вакансий")

        # Фильтрация новых вакансий
        new_vacancies = []
        for vacancy in items:
            if not self.db.vacancy_exists(vacancy.get("id", "")):
                new_vacancies.append(vacancy)

        self.logger.info(f"Новых вакансий: {len(new_vacancies)}")

        # Добавление в базу и отправка уведомлений
        for vacancy in new_vacancies:
            self.db.add_vacancy(vacancy)
            self._send_notifications(vacancy)

        # Очистка старых записей (раз в час)
        if datetime.now().minute == 0:
            deleted = self.db.clear_old_vacancies(days=30)
            if deleted:
                self.logger.info(f"Удалено старых записей: {deleted}")

        return len(new_vacancies)

    def _send_notifications(self, vacancy: dict):
        """Отправка уведомлений всеми способами."""
        name = vacancy.get("name", "Без названия")
        
        # Telegram
        if self.telegram_bot:
            try:
                self.telegram_bot.send_vacancy(vacancy)
                self.logger.debug(f"Telegram: {name}")
            except Exception as e:
                self.logger.error(f"Ошибка отправки в Telegram: {e}")
        
        # Email
        if self.email_bot:
            try:
                self.email_bot.send_vacancy(vacancy)
                self.logger.debug(f"Email: {name}")
            except Exception as e:
                self.logger.error(f"Ошибка отправки Email: {e}")
        
        # Slack
        if self.slack_bot:
            try:
                self.slack_bot.send_vacancy(vacancy)
                self.logger.debug(f"Slack: {name}")
            except Exception as e:
                self.logger.error(f"Ошибка отправки в Slack: {e}")

    def print_stats(self):
        """Вывод статистики."""
        stats = self.db.get_stats()
        salary_stats = self.db.get_salary_stats()
        
        self.logger.info("=" * 50)
        self.logger.info("📊 Статистика вакансий")
        self.logger.info("=" * 50)
        self.logger.info(f"Всего в базе: {stats['total']}")
        self.logger.info(f"За сегодня: {stats['today']}")
        self.logger.info(f"За неделю: {stats['week']}")
        
        if stats['avg_salary']:
            self.logger.info(f"Средняя зарплата: от {stats['avg_salary']}")
        
        if salary_stats['with_salary']:
            self.logger.info(f"Вакансий с зарплатой: {salary_stats['with_salary']}")
            if salary_stats['min_from']:
                self.logger.info(f"Мин. зарплата: {salary_stats['min_from']}")
            if salary_stats['max_to']:
                self.logger.info(f"Макс. зарплата: {salary_stats['max_to']}")
        
        if stats['top_employers']:
            self.logger.info("Топ работодателей:")
            for emp in stats['top_employers']:
                self.logger.info(f"  - {emp['employer']}: {emp['count']}")
        
        self.logger.info("=" * 50)

    def run(self, once: bool = False):
        """
        Запуск основного цикла.

        :param once: Однократный запуск (для cron)
        """
        self.logger.info("🚀 Запуск трекера вакансий...")
        self.logger.info(f"Поисковый запрос: {HH_SEARCH_TEXT}")
        self.logger.info(f"Регион: {HH_AREA or 'Все регионы'}")
        
        if HH_EXCLUDE_WORDS:
            self.logger.info(f"Исключить слова: {', '.join(HH_EXCLUDE_WORDS)}")
        
        self.logger.info(f"Интервал проверки: {CHECK_INTERVAL} сек.")
        
        if once:
            self.logger.info("Режим: однократная проверка")

        # Тест соединений
        connections_ok = False
        
        if self.telegram_bot and self.telegram_bot.test_connection():
            connections_ok = True
            self.logger.info("✅ Telegram подключен")
        
        if self.email_bot and self.email_bot.test_connection():
            connections_ok = True
            self.logger.info("✅ Email подключен")
        
        if self.slack_bot and self.slack_bot.test_connection():
            connections_ok = True
            self.logger.info("✅ Slack подключен")
        
        if not connections_ok:
            self.logger.warning("⚠️ Ни один нотификатор не подключен!")

        # Статистика
        stats = self.db.get_stats()
        self.logger.info(f"В базе вакансий: {stats['total']} (за сегодня: {stats['today']})")

        # Основной цикл
        while self.running:
            try:
                self.check_vacancies()

                if once:
                    self.logger.info("Однократная проверка завершена")
                    break

                # Ожидание до следующей проверки
                for _ in range(CHECK_INTERVAL):
                    if not self.running:
                        break
                    time.sleep(1)

            except Exception as e:
                self.logger.error(f"Ошибка в цикле проверки: {e}", exc_info=True)
                if not self.running:
                    break
                time.sleep(10)  # Пауза перед повторной попыткой

        self.logger.info("✅ Трекер остановлен.")


def main():
    """Точка входа."""
    parser = argparse.ArgumentParser(
        description="Трекер вакансий hh.ru с уведомлениями"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Однократная проверка (для cron)"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Показать статистику и выйти"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default=LOG_LEVEL,
        help="Уровень логирования"
    )
    
    args = parser.parse_args()
    
    # Настройка логирования
    setup_logging(args.log_level, LOG_FILE)
    logger = logging.getLogger(__name__)
    
    # Проверка конфигурации
    if not TELEGRAM_BOT_TOKEN and not (EMAIL_ENABLED and EMAIL_USER) and not (SLACK_ENABLED and SLACK_WEBHOOK_URL):
        logger.error("❌ Не настроен ни один нотификатор!")
        logger.error("Настройте TELEGRAM_BOT_TOKEN, EMAIL или SLACK_WEBHOOK_URL в .env")
        sys.exit(1)

    # Запуск трекера
    tracker = VacancyTracker()
    
    if args.stats:
        tracker.print_stats()
    else:
        tracker.run(once=args.once)


if __name__ == "__main__":
    main()
