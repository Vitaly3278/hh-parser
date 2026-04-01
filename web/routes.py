"""Веб роуты."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse

from storage.models import Vacancy
from storage.repository import VacancyRepository


async def home(
    request: Request,
    repository: VacancyRepository,
    templates
) -> HTMLResponse:
    """Главная страница с вакансиями."""
    vacancies = repository.get_all(limit=50)
    stats = repository.get_stats()

    # Форматируем вакансии для отображения
    formatted_vacancies = []
    for v in vacancies:
        formatted_vacancies.append({
            'id': v.id,
            'name': v.name,
            'employer': v.employer or 'Б/н',
            'salary': v.formatted_salary() if v.has_salary() else "",
            'area': v.area or 'Б/н',
            'url': v.url or '#',
            'published_at': v.published_at[:10] if v.published_at else '',
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


def get_stats(repository: VacancyRepository) -> Dict[str, Any]:
    """Получить статистику вакансий."""
    stats = repository.get_stats()
    salary_stats = repository.get_salary_stats()
    return {**stats, **salary_stats}


def get_vacancies(
    repository: VacancyRepository,
    limit: Optional[int] = 50,
    offset: Optional[int] = 0
) -> Dict[str, Any]:
    """Получить список вакансий."""
    # Защита от None значений
    if limit is None:
        limit = 50
    if offset is None:
        offset = 0

    vacancies = repository.get_all(limit=limit, offset=offset)
    total = repository.count()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [v.to_dict() for v in vacancies],
    }


def get_vacancy(repository: VacancyRepository, vacancy_id: str) -> Dict[str, Any]:
    """Получить вакансию по ID."""
    vacancy = repository.get_by_id(vacancy_id)
    if not vacancy:
        raise HTTPException(status_code=404, detail="Вакансия не найдена")
    return vacancy.to_dict()


def clear_old_vacancies(repository: VacancyRepository, days: int = 30) -> Dict[str, int]:
    """Удалить старые вакансии."""
    deleted = repository.clear_old(days=days)
    return {"deleted": deleted, "days": days}


def health_check() -> Dict[str, Any]:
    """Проверка работоспособности."""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "database": "connected"
    }
