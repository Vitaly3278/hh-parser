#!/usr/bin/env python3
"""
Приложение для отслеживания новых вакансий на hh.ru
с отправкой уведомлений в Telegram.
"""

import time
import signal
import sys
from datetime import datetime

from config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    HH_SEARCH_TEXT,
    HH_AREA,
    HH_SALARY_FROM,
    HH_EMPLOYMENT,
    HH_EXPERIENCE,
    CHECK_INTERVAL,
    DB_PATH,
)
from hh_parser import HHParser
from telegram_bot import TelegramBot
from database import VacancyDatabase


class VacancyTracker:
    """Трекер вакансий с уведомлениями."""

    def __init__(self):
        """Инициализация трекера."""
        # Преобразуем строку "None" в None
        area = HH_AREA if HH_AREA and HH_AREA != "None" else None
        self.parser = HHParser(area=area)
        self.bot = TelegramBot(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
        self.db = VacancyDatabase(DB_PATH)
        self.running = True

        # Настройка обработки сигналов
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Обработчик сигналов завершения."""
        print("\n🛑 Получен сигнал завершения. Остановка...")
        self.running = False

    def check_vacancies(self) -> int:
        """
        Проверка новых вакансий.

        :return: Количество новых вакансий
        """
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Проверка вакансий...")

        # Поиск вакансий
        result = self.parser.search_vacancies(
            search_text=HH_SEARCH_TEXT,
            salary_from=HH_SALARY_FROM,
            employment=HH_EMPLOYMENT,
            experience=HH_EXPERIENCE,
        )

        items = result.get("items", [])
        found = result.get("found", 0)

        print(f"Найдено вакансий: {found}, получено: {len(items)}")

        # Фильтрация новых вакансий
        new_vacancies = []
        for vacancy in items:
            if not self.db.vacancy_exists(vacancy.get("id", "")):
                new_vacancies.append(vacancy)

        print(f"Новых вакансий: {len(new_vacancies)}")

        # Добавление в базу и отправка уведомлений
        for vacancy in new_vacancies:
            self.db.add_vacancy(vacancy)
            self.bot.send_vacancy(vacancy)
            print(f"Отправлено: {vacancy.get('name', 'Без названия')}")

        # Очистка старых записей (раз в час)
        if datetime.now().minute == 0:
            deleted = self.db.clear_old_vacancies(days=30)
            if deleted:
                print(f"Удалено старых записей: {deleted}")

        return len(new_vacancies)

    def run(self):
        """Запуск основного цикла."""
        print("🚀 Запуск трекера вакансий...")
        print(f"Поисковый запрос: {HH_SEARCH_TEXT}")
        print(f"Регион: {HH_AREA or 'Все регионы'}")
        print(f"Интервал проверки: {CHECK_INTERVAL} сек.")

        # Тест соединения
        if not self.bot.test_connection():
            print("❌ Ошибка подключения к Telegram! Проверьте токен и chat_id.")
            return

        # Статистика
        stats = self.db.get_stats()
        print(f"В базе вакансий: {stats['total']} (за сегодня: {stats['today']})")

        # Основной цикл
        while self.running:
            try:
                self.check_vacancies()

                # Ожидание до следующей проверки
                for _ in range(CHECK_INTERVAL):
                    if not self.running:
                        break
                    time.sleep(1)

            except Exception as e:
                print(f"❌ Ошибка в цикле проверки: {e}")
                if not self.running:
                    break
                time.sleep(10)  # Пауза перед повторной попыткой

        print("✅ Трекер остановлен.")


def main():
    """Точка входа."""
    # Проверка конфигурации
    if TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ Укажите TELEGRAM_BOT_TOKEN в config.py")
        sys.exit(1)

    if TELEGRAM_CHAT_ID == "YOUR_CHAT_ID_HERE":
        print("❌ Укажите TELEGRAM_CHAT_ID в config.py")
        sys.exit(1)

    if HH_SEARCH_TEXT == "Python разработчик":
        print("⚠️ Измените HH_SEARCH_TEXT в config.py на нужный запрос")

    # Запуск трекера
    tracker = VacancyTracker()
    tracker.run()


if __name__ == "__main__":
    main()
