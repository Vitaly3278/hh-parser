#!/usr/bin/env python3
"""
Асинхронное приложение для отслеживания вакансий hh.ru
с уведомлениями в Telegram и управлением через бота.
"""

import asyncio
import signal
import sys
import argparse
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional, List

import aiohttp

from config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    EMAIL_ENABLED,
    EMAIL_HOST,
    EMAIL_PORT,
    EMAIL_USER,
    EMAIL_PASSWORD,
    EMAIL_RECIPIENT,
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
from database import VacancyDatabase


def setup_logging(level: str, log_file: str):
    """Настройка логирования."""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Создаём обработчики
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
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
    """Асинхронный трекер вакансий с уведомлениями."""

    def __init__(self, http_session: aiohttp.ClientSession):
        """Инициализация трекера."""
        self.logger = logging.getLogger(__name__)
        self.http_session = http_session
        self.running = False

        # Инициализация компонентов
        area = HH_AREA if HH_AREA else None
        self.parser = HHParser(area=area, session=http_session)
        self.db = VacancyDatabase(DB_PATH)

        # Нотификаторы
        self.telegram_bot: Optional[TelegramBot] = None
        if TELEGRAM_BOT_TOKEN:
            self.telegram_bot = TelegramBot(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, http_session)

        self.email_bot: Optional[EmailNotifier] = None
        if EMAIL_ENABLED and all([EMAIL_HOST, EMAIL_USER, EMAIL_PASSWORD, EMAIL_RECIPIENT]):
            self.email_bot = EmailNotifier(
                EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASSWORD, EMAIL_RECIPIENT
            )

        # Статистика
        self.stats = {
            'checks_count': 0,
            'new_vacancies_count': 0,
            'errors_count': 0,
            'last_check': None,
        }

    async def check_vacancies(self) -> int:
        """
        Проверка новых вакансий.

        :return: Количество новых вакансий
        """
        self.logger.info(f"Проверка вакансий... (запрос: {HH_SEARCH_TEXT})")
        self.stats['checks_count'] += 1
        self.stats['last_check'] = datetime.now().isoformat()

        try:
            # Поиск вакансий
            result = await self.parser.search_vacancies(
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
                await self._send_notifications(vacancy)
                self.stats['new_vacancies_count'] += 1

            # Очистка старых записей (раз в час)
            if datetime.now().minute == 0:
                deleted = self.db.clear_old_vacancies(days=30)
                if deleted:
                    self.logger.info(f"Удалено старых записей: {deleted}")

            return len(new_vacancies)

        except Exception as e:
            self.logger.error(f"Ошибка при проверке вакансий: {e}", exc_info=True)
            self.stats['errors_count'] += 1
            return 0

    async def _send_notifications(self, vacancy: dict):
        """Отправка уведомлений всеми способами."""
        name = vacancy.get("name", "Без названия")
        tasks = []

        # Telegram
        if self.telegram_bot:
            try:
                tasks.append(self.telegram_bot.send_vacancy(vacancy))
            except Exception as e:
                self.logger.error(f"Ошибка подготовки Telegram: {e}")

        # Email
        if self.email_bot:
            try:
                tasks.append(self.email_bot.send_vacancy(vacancy))
            except Exception as e:
                self.logger.error(f"Ошибка подготовки Email: {e}")

        # Выполняем все уведомления параллельно
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.logger.error(f"Ошибка уведомления {i}: {result}")

    def get_stats(self) -> dict:
        """Получение статистики работы трекера."""
        db_stats = self.db.get_stats()
        return {
            **self.stats,
            **db_stats,
        }

    async def run(self, once: bool = False):
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

        if self.telegram_bot:
            try:
                if await self.telegram_bot.test_connection():
                    connections_ok = True
                    self.logger.info("✅ Telegram подключен")
            except Exception as e:
                self.logger.error(f"Ошибка подключения Telegram: {e}")

        if self.email_bot:
            try:
                if self.email_bot.test_connection():
                    connections_ok = True
                    self.logger.info("✅ Email подключен")
            except Exception as e:
                self.logger.error(f"Ошибка подключения Email: {e}")

        if not connections_ok:
            self.logger.warning("⚠️ Ни один нотификатор не подключен!")

        # Статистика
        db_stats = self.db.get_stats()
        self.logger.info(f"В базе вакансий: {db_stats['total']} (за сегодня: {db_stats['today']})")

        # Основной цикл
        self.running = True
        while self.running:
            try:
                await self.check_vacancies()

                if once:
                    self.logger.info("Однократная проверка завершена")
                    break

                # Ожидание до следующей проверки
                for _ in range(CHECK_INTERVAL):
                    if not self.running:
                        break
                    await asyncio.sleep(1)

            except Exception as e:
                self.logger.error(f"Ошибка в цикле проверки: {e}", exc_info=True)
                if not self.running:
                    break
                await asyncio.sleep(10)  # Пауза перед повторной попыткой

        self.logger.info("✅ Трекер остановлен.")

    def stop(self):
        """Остановка трекера."""
        self.logger.info("🛑 Остановка трекера...")
        self.running = False


class Application:
    """Основное приложение, объединяющее трекер и бота."""

    def __init__(self):
        """Инициализация приложения."""
        self.logger = logging.getLogger(__name__)
        self.http_session: Optional[aiohttp.ClientSession] = None
        self.tracker: Optional[VacancyTracker] = None
        self.bot_task: Optional[asyncio.Task] = None
        self.tracker_task: Optional[asyncio.Task] = None
        self.running = False

    async def _run_bot(self, bot_instance):
        """Запуск бота в отдельной задаче."""
        try:
            bot_instance.run()
        except Exception as e:
            self.logger.error(f"Ошибка бота: {e}", exc_info=True)

    async def _run_tracker(self, tracker_instance, once: bool = False):
        """Запуск трекера в отдельной задаче."""
        try:
            await tracker_instance.run(once=once)
        except Exception as e:
            self.logger.error(f"Ошибка трекера: {e}", exc_info=True)

    async def run(self, once: bool = False, bot_only: bool = False, tracker_only: bool = False):
        """
        Запуск приложения.

        :param once: Однократная проверка трекера
        :param bot_only: Запуск только бота
        :param tracker_only: Запуск только трекера
        """
        self.logger.info("🚀 Запуск HH Tracker приложения...")
        self.running = True

        # Создаем HTTP сессию
        self.http_session = aiohttp.ClientSession()

        try:
            # Создаем трекер
            self.tracker = VacancyTracker(self.http_session)

            # Обработка сигналов
            loop = asyncio.get_event_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(sig, self.stop)

            if bot_only:
                # Запуск только бота
                from bot import VacancyBot
                bot_instance = VacancyBot()
                self.logger.info("Запуск только бота...")
                bot_instance.run()
            elif tracker_only:
                # Запуск только трекера
                self.logger.info("Запуск только трекера...")
                await self.tracker.run(once=once)
            else:
                # Запуск обоих компонентов
                self.logger.info("Запуск бота и трекера...")

                # Запускаем бота в отдельном потоке (т.к. он использует polling)
                from bot import VacancyBot
                bot_instance = VacancyBot()

                # Создаем задачи
                self.bot_task = asyncio.create_task(self._run_bot(bot_instance))
                await asyncio.sleep(2)  # Даём боту запуститься

                self.tracker_task = asyncio.create_task(self._run_tracker(self.tracker, once=once))

                # Ожидаем завершения
                await asyncio.gather(self.bot_task, self.tracker_task, return_exceptions=True)

        except Exception as e:
            self.logger.error(f"Критическая ошибка приложения: {e}", exc_info=True)
        finally:
            await self.cleanup()

    def stop(self):
        """Остановка приложения."""
        self.logger.info("🛑 Получен сигнал остановки...")
        self.running = False
        if self.tracker:
            self.tracker.stop()

    async def cleanup(self):
        """Очистка ресурсов."""
        self.logger.info("🧹 Очистка ресурсов...")

        if self.http_session:
            await self.http_session.close()

        # Закрываем Telegram бота если есть
        if self.tracker and self.tracker.telegram_bot:
            await self.tracker.telegram_bot.close()

        self.logger.info("✅ Приложение остановлено")


def print_stats(tracker: VacancyTracker):
    """Вывод статистики."""
    stats = tracker.get_stats()

    print("=" * 50)
    print("📊 Статистика приложения")
    print("=" * 50)
    print(f"Всего в базе: {stats['total']}")
    print(f"За сегодня: {stats['today']}")
    print(f"За неделю: {stats['week']}")
    print(f"Проверок выполнено: {stats['checks_count']}")
    print(f"Новых вакансий найдено: {stats['new_vacancies_count']}")
    print(f"Ошибок: {stats['errors_count']}")
    print(f"Последняя проверка: {stats['last_check'] or 'Никогда'}")

    if stats['avg_salary']:
        print(f"Средняя зарплата: от {stats['avg_salary']}")

    if stats['top_employers']:
        print("Топ работодателей:")
        for emp in stats['top_employers']:
            print(f"  - {emp['employer']}: {emp['count']}")

    print("=" * 50)


def main():
    """Точка входа."""
    parser = argparse.ArgumentParser(
        description="Асинхронный трекер вакансий hh.ru с Telegram ботом"
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
        "--bot-only",
        action="store_true",
        help="Запуск только Telegram бота"
    )
    parser.add_argument(
        "--tracker-only",
        action="store_true",
        help="Запуск только трекера (без бота)"
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
    has_notifier = (
        (TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID) or
        (EMAIL_ENABLED and EMAIL_USER)
    )

    if not has_notifier:
        logger.error("❌ Не настроен ни один нотификатор!")
        logger.error("Настройте TELEGRAM_BOT_TOKEN или EMAIL в .env")
        sys.exit(1)

    # Запуск приложения
    app = Application()

    if args.stats:
        # Показ статистики
        tracker = VacancyTracker(aiohttp.ClientSession())
        print_stats(tracker)
        asyncio.run(tracker.db.engine.dispose())
    else:
        # Запуск
        try:
            asyncio.run(app.run(
                once=args.once,
                bot_only=args.bot_only,
                tracker_only=args.tracker_only
            ))
        except KeyboardInterrupt:
            logger.info("Остановка по Ctrl+C")


if __name__ == "__main__":
    main()
