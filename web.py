#!/usr/bin/env python3
"""Веб-интерфейс HH Tracker на FastAPI."""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from database import VacancyDatabase
from config import DB_PATH

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="HH Tracker API",
    description="API для просмотра вакансий и статистики",
    version="2.0.0"
)

# Инициализация БД
db = VacancyDatabase(DB_PATH)

# Шаблоны (абсолютный путь)
BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@app.get("/", response_class=HTMLResponse, tags=["UI"])
async def home(request: Request):
    """Главная страница с вакансиями."""
    vacancies = db.get_all_vacancies()
    stats = db.get_stats()
    
    # Форматируем вакансии для отображения
    formatted_vacancies = []
    for v in vacancies[:50]:  # Показываем максимум 50
        salary = ""
        if v.get('salary_from') or v.get('salary_to'):
            from_s = v.get('salary_from', '')
            to_s = v.get('salary_to', '')
            curr = v.get('currency', 'RUR')
            if from_s and to_s:
                salary = f"{from_s}-{to_s} {curr}"
            elif from_s:
                salary = f"от {from_s} {curr}"
            elif to_s:
                salary = f"до {to_s} {curr}"
        
        formatted_vacancies.append({
            'id': v.get('id', ''),
            'name': v.get('name', 'Б/н'),
            'employer': v.get('employer', 'Б/н'),
            'salary': salary,
            'area': v.get('area', 'Б/н'),
            'url': v.get('url', '#'),
            'published_at': v.get('published_at', ''),
        })
    
    return templates.TemplateResponse(
        name="index.html",
        request=request,
        context={
            "vacancies": formatted_vacancies,
            "stats": stats,
            "total_count": len(vacancies),
        }
    )


@app.get("/api/stats", tags=["API"])
async def get_stats():
    """Получить статистику вакансий."""
    stats = db.get_stats()
    salary_stats = db.get_salary_stats()
    return {
        **stats,
        **salary_stats,
    }


@app.get("/api/vacancies", tags=["API"])
async def get_vacancies(
    limit: Optional[int] = 50,
    offset: Optional[int] = 0
):
    """Получить список вакансий."""
    vacancies = db.get_all_vacancies()
    total = len(vacancies)
    
    # Защита от None значений
    if limit is None:
        limit = 50
    if offset is None:
        offset = 0
    
    paginated = vacancies[offset:offset + limit]

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": paginated,
    }


@app.get("/api/vacancies/{vacancy_id}", tags=["API"])
async def get_vacancy(vacancy_id: str):
    """Получить вакансию по ID."""
    vacancies = db.get_all_vacancies()
    for v in vacancies:
        if v.get('id') == vacancy_id:
            return v
    
    raise HTTPException(status_code=404, detail="Вакансия не найдена")


@app.delete("/api/vacancies/clear", tags=["API"])
async def clear_old_vacancies(days: int = 30):
    """Удалить старые вакансии."""
    deleted = db.clear_old_vacancies(days=days)
    return {"deleted": deleted, "days": days}


@app.get("/health", tags=["System"])
async def health_check():
    """Проверка работоспособности."""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "database": "connected"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
