"""Создание веб-приложения FastAPI."""

from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from core import WEB_HOST, WEB_PORT


def create_web_app(repository, templates_dir: str = "templates") -> FastAPI:
    """
    Создание веб-приложения.

    :param repository: Репозиторий вакансий
    :param templates_dir: Директория шаблонов
    :return: FastAPI приложение
    """
    app = FastAPI(
        title="HH Tracker API",
        description="API для просмотра вакансий и статистики",
        version="2.0.0"
    )

    # Шаблоны
    BASE_DIR = Path(__file__).parent
    TEMPLATES_DIR = BASE_DIR / templates_dir
    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

    # Статика
    STATIC_DIR = BASE_DIR / "static"
    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    # Импортируем роуты
    from .routes import (
        home,
        get_stats,
        get_vacancies,
        get_vacancy,
        clear_old_vacancies,
        health_check,
    )

    # Регистрируем роуты
    app.get("/", response_class=HTMLResponse)(
        lambda request: home(request, repository, templates)
    )
    app.get("/api/stats")(lambda: get_stats(repository))
    app.get("/api/vacancies")(lambda limit=50, offset=0: get_vacancies(repository, limit, offset))
    app.get("/api/vacancies/{vacancy_id}")(lambda vacancy_id: get_vacancy(repository, vacancy_id))
    app.delete("/api/vacancies/clear")(lambda days=30: clear_old_vacancies(repository, days))
    app.get("/health")(health_check)

    return app
