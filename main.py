#!/usr/bin/env python3
"""
HH Tracker — Точка входа приложения.

Модульная архитектура:
- core/ — ядро (config, logging, exceptions)
- modules/ — модули (storage, parser, notifier, bot, web)
- services/ — сервисы приложения
- app.py — сборка приложения
"""

import asyncio
import argparse
import sys
import threading

from core import setup_logging, LOG_LEVEL, LOG_FILE
from core.logger import get_logger
from app import Application, create_app


logger = get_logger(__name__)


async def run_main_app(app: Application, once: bool = False):
    """Запуск основного приложения."""
    await app.initialize()

    # Запуск веб-интерфейса в отдельном потоке
    web_thread = threading.Thread(target=app.run_web, args=(), daemon=True)
    web_thread.start()

    # Запуск трекера в отдельном потоке
    tracker_thread = threading.Thread(target=lambda: asyncio.run(app.run_tracker(once=once)), daemon=True)
    tracker_thread.start()

    # Бот запускается в главном потоке (требование python-telegram-bot)
    logger.info("🤖 Бот запущен в главном потоке")
    try:
        app.run_bot()
    except KeyboardInterrupt:
        logger.info("Остановка по Ctrl+C")
    finally:
        # Остановка трекера
        app.running = False
        tracker_thread.join(timeout=2)
        # Остановка веб
        app.shutdown()


def main():
    """Точка входа."""
    parser = argparse.ArgumentParser(description="HH Tracker — Трекер вакансий hh.ru")

    parser.add_argument(
        "--once",
        action="store_true",
        help="Однократная проверка (для cron)"
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
        "--web",
        action="store_true",
        help="Запуск веб-интерфейса"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default=LOG_LEVEL,
        help="Уровень логирования"
    )

    args = parser.parse_args()

    # Настройка логирования
    setup_logging(level=args.log_level, log_file=LOG_FILE)
    logger.info("🚀 Запуск HH Tracker...")

    # Создание приложения
    app = create_app()

    try:
        if args.bot_only:
            # Только бот
            asyncio.run(app.initialize())
            app.run_bot()

        elif args.tracker_only:
            # Только трекер
            asyncio.run(app.initialize())
            asyncio.run(app.run_tracker(once=args.once))

        elif args.web:
            # Веб-интерфейс
            from modules.web.app import create_web_app
            from modules.storage import get_database
            import uvicorn

            db = get_database()
            repository = db.SessionLocal
            web_app = create_web_app(repository)

            logger.info("🌐 Запуск веб-интерфейса...")
            uvicorn.run(web_app, host="0.0.0.0", port=8000)

        else:
            # Полный режим (трекер + бот)
            asyncio.run(run_main_app(app, once=args.once))

    except KeyboardInterrupt:
        logger.info("Остановка по Ctrl+C")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
        sys.exit(1)
    finally:
        asyncio.run(app.shutdown())


if __name__ == "__main__":
    main()
