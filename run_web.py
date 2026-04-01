#!/usr/bin/env python3
"""Веб-интерфейс HH Tracker."""

import uvicorn
from core import WEB_HOST, WEB_PORT
from storage import get_database, VacancyRepository
from web.app import create_web_app


def main():
    """Запуск веб-интерфейса."""
    # Инициализация БД
    db = get_database()
    repository = VacancyRepository(db.SessionLocal)

    # Создание приложения
    app = create_web_app(repository)

    # Запуск
    print(f"🌐 Веб-интерфейс запущен на http://{WEB_HOST}:{WEB_PORT}")
    uvicorn.run(app, host=WEB_HOST, port=WEB_PORT)


if __name__ == "__main__":
    main()
