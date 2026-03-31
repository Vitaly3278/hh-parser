#!/usr/bin/env python3
"""Веб-интерфейс для управления трекером вакансий."""

import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List
import uvicorn

from config import DB_PATH, LOG_FILE
from database import VacancyDatabase

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="HH Tracker API", version="1.0.0")
db = VacancyDatabase(DB_PATH)


class VacancyResponse(BaseModel):
    id: str
    name: str
    employer: Optional[str]
    salary_from: Optional[int]
    salary_to: Optional[int]
    currency: Optional[str]
    area: Optional[str]
    url: str
    published_at: Optional[str]
    created_at: Optional[str]


class StatsResponse(BaseModel):
    total: int
    today: int
    week: int
    avg_salary: Optional[float]
    top_employers: List[dict]


class SearchRequest(BaseModel):
    search_text: Optional[str] = None
    area: Optional[str] = None
    salary_from: Optional[int] = None


# HTML шаблон
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HH Tracker - Вакансии</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { color: #333; margin-bottom: 20px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 30px; }
        .stat-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .stat-card h3 { color: #666; font-size: 14px; margin-bottom: 5px; }
        .stat-card .value { font-size: 28px; font-weight: bold; color: #007bff; }
        .vacancies { background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .vacancy { padding: 20px; border-bottom: 1px solid #eee; }
        .vacancy:last-child { border-bottom: none; }
        .vacancy h3 { color: #007bff; margin-bottom: 8px; }
        .vacancy .company { color: #666; margin-bottom: 8px; }
        .vacancy .salary { color: #28a745; font-weight: bold; }
        .vacancy .area { color: #999; font-size: 14px; }
        .vacancy a { display: inline-block; margin-top: 10px; padding: 8px 16px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; }
        .vacancy a:hover { background: #0056b3; }
        .filters { margin-bottom: 20px; padding: 20px; background: white; border-radius: 8px; }
        .filters input, .filters select { padding: 10px; margin-right: 10px; border: 1px solid #ddd; border-radius: 4px; }
        .filters button { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
        .filters button:hover { background: #0056b3; }
        .loading { text-align: center; padding: 40px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔔 HH Tracker - Вакансии</h1>
        
        <div class="stats" id="stats"></div>
        
        <div class="filters">
            <input type="text" id="search" placeholder="Поиск по названию">
            <input type="number" id="salary" placeholder="Мин. зарплата">
            <button onclick="loadVacancies()">Найти</button>
            <button onclick="refreshStats()" style="background: #28a745;">📊 Обновить</button>
        </div>
        
        <div class="vacancies" id="vacancies">
            <div class="loading">Загрузка...</div>
        </div>
    </div>
    
    <script>
        async function loadVacancies() {
            const search = document.getElementById('search').value;
            const salary = document.getElementById('salary').value;
            let url = '/api/vacancies?limit=50';
            if (search) url += '&search=' + encodeURIComponent(search);
            if (salary) url += '&salary=' + salary;
            
            const res = await fetch(url);
            const data = await res.json();
            
            const container = document.getElementById('vacancies');
            if (data.length === 0) {
                container.innerHTML = '<div class="loading">Вакансии не найдены</div>';
                return;
            }
            
            container.innerHTML = data.map(v => `
                <div class="vacancy">
                    <h3>${v.name}</h3>
                    <div class="company">🏢 ${v.employer || 'Не указана'}</div>
                    <div class="salary">💰 ${formatSalary(v.salary_from, v.salary_to, v.currency)}</div>
                    <div class="area">📍 ${v.area || 'Не указан'}</div>
                    <a href="${v.url}" target="_blank">Смотреть</a>
                </div>
            `).join('');
        }
        
        function formatSalary(from, to, currency) {
            if (!from && !to) return 'Зарплата не указана';
            if (from && to) return `${from} - ${to} ${currency}`;
            if (from) return `от ${from} ${currency}`;
            return `до ${to} ${currency}`;
        }
        
        async function refreshStats() {
            const res = await fetch('/api/stats');
            const stats = await res.json();
            
            document.getElementById('stats').innerHTML = `
                <div class="stat-card">
                    <h3>Всего вакансий</h3>
                    <div class="value">${stats.total}</div>
                </div>
                <div class="stat-card">
                    <h3>За сегодня</h3>
                    <div class="value">${stats.today}</div>
                </div>
                <div class="stat-card">
                    <h3>За неделю</h3>
                    <div class="value">${stats.week}</div>
                </div>
                <div class="stat-card">
                    <h3>Средняя ЗП</h3>
                    <div class="value">${stats.avg_salary || '—'}</div>
                </div>
            `;
        }
        
        loadVacancies();
        refreshStats();
    </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def root():
    """Главная страница."""
    return HTML_TEMPLATE


@app.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    """Получить статистику."""
    try:
        stats = db.get_stats()
        return StatsResponse(**stats)
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/vacancies", response_model=List[VacancyResponse])
async def get_vacancies(
    limit: int = 50,
    search: Optional[str] = None,
    salary: Optional[int] = None,
):
    """Получить список вакансий."""
    try:
        vacancies = db.get_all_vacancies()
        
        # Фильтрация
        if search:
            search_lower = search.lower()
            vacancies = [
                v for v in vacancies
                if search_lower in v.get("name", "").lower()
                or search_lower in (v.get("employer") or "").lower()
            ]
        
        if salary:
            vacancies = [
                v for v in vacancies
                if (v.get("salary_from") or 0) >= salary
                or (v.get("salary_to") or 0) >= salary
            ]
        
        return vacancies[:limit]
    except Exception as e:
        logger.error(f"Ошибка получения вакансий: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/vacancies/{vacancy_id}", response_model=VacancyResponse)
async def get_vacancy(vacancy_id: str):
    """Получить вакансию по ID."""
    vacancies = db.get_all_vacancies()
    for v in vacancies:
        if v["id"] == vacancy_id:
            return VacancyResponse(**v)
    raise HTTPException(status_code=404, detail="Вакансия не найдена")


@app.delete("/api/vacancies/clear")
async def clear_old_vacancies(days: int = 30):
    """Удалить старые вакансии."""
    try:
        deleted = db.clear_old_vacancies(days)
        return {"deleted": deleted}
    except Exception as e:
        logger.error(f"Ошибка очистки: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Проверка здоровья."""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


if __name__ == "__main__":
    from datetime import datetime
    uvicorn.run(app, host="0.0.0.0", port=8000)
