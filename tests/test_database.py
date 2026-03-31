"""Unit тесты для модуля storage."""

import pytest
import os
import tempfile
from datetime import datetime, timedelta

from modules.storage.database import Database
from modules.storage.models import Vacancy


@pytest.fixture
def db():
    """Фикстура для создания временной базы данных."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    database = Database(db_path)
    yield database
    
    # Очистка после теста
    os.unlink(db_path)


@pytest.fixture
def sample_vacancy():
    """Фикстура с тестовой вакансией."""
    return {
        "id": "test_123",
        "name": "Python Developer",
        "employer": {"name": "Test Company"},
        "salary": {"from": 100000, "to": 150000, "currency": "RUR"},
        "area": {"name": "Москва"},
        "url": "https://hh.ru/vacancy/123",
        "published_at": datetime.now().isoformat(),
    }


@pytest.fixture
def sample_vacancies():
    """Фикстура со списком тестовых вакансий."""
    return [
        {
            "id": f"test_{i}",
            "name": f"Python Developer {i}",
            "employer": {"name": f"Company {i}"},
            "salary": {"from": 100000 + i * 10000, "to": 150000 + i * 10000, "currency": "RUR"},
            "area": {"name": "Москва"},
            "url": f"https://hh.ru/vacancy/{i}",
            "published_at": datetime.now().isoformat(),
        }
        for i in range(5)
    ]


class TestVacancyDatabase:
    """Тесты для VacancyDatabase."""

    def test_create_table(self, db):
        """Тест создания таблицы."""
        # Таблица должна быть создана при инициализации
        assert db.vacancy_exists("nonexistent") is False

    def test_vacancy_exists_not_exists(self, db):
        """Тест проверки несуществующей вакансии."""
        assert db.vacancy_exists("nonexistent_id") is False

    def test_vacancy_exists(self, db, sample_vacancy):
        """Тест проверки существующей вакансии."""
        db.add_vacancy(sample_vacancy)
        assert db.vacancy_exists("test_123") is True

    def test_add_vacancy(self, db, sample_vacancy):
        """Тест добавления вакансии."""
        result = db.add_vacancy(sample_vacancy)
        assert result is True
        assert db.vacancy_exists("test_123") is True

    def test_add_duplicate_vacancy(self, db, sample_vacancy):
        """Тест добавления дубликата вакансии."""
        db.add_vacancy(sample_vacancy)
        result = db.add_vacancy(sample_vacancy)
        assert result is False

    def test_add_vacancies_batch(self, db, sample_vacancies):
        """Тест пакетного добавления вакансий."""
        count = db.add_vacancies_batch(sample_vacancies)
        assert count == 5

    def test_add_vacancies_batch_with_duplicates(self, db, sample_vacancies):
        """Тест пакетного добавления с дубликатами."""
        # Добавляем все вакансии
        db.add_vacancies_batch(sample_vacancies)
        # Пытаемся добавить те же вакансии снова
        count = db.add_vacancies_batch(sample_vacancies)
        assert count == 0

    def test_get_all_vacancies_empty(self, db):
        """Тест получения пустого списка вакансий."""
        vacancies = db.get_all_vacancies()
        assert len(vacancies) == 0

    def test_get_all_vacancies(self, db, sample_vacancies):
        """Тест получения всех вакансий."""
        db.add_vacancies_batch(sample_vacancies)
        vacancies = db.get_all_vacancies()
        assert len(vacancies) == 5

    def test_get_recent_vacancies(self, db, sample_vacancy):
        """Тест получения недавних вакансий."""
        db.add_vacancy(sample_vacancy)
        recent = db.get_recent_vacancies(hours=24)
        assert len(recent) == 1
        assert recent[0]['id'] == "test_123"

    def test_clear_old_vacancies(self, db):
        """Тест очистки старых вакансий."""
        # Добавляем вакансию
        vacancy = {
            "id": "old_123",
            "name": "Old Vacancy",
            "employer": {"name": "Old Company"},
            "salary": {},
            "area": {"name": "Москва"},
            "url": "https://hh.ru/vacancy/old",
            "published_at": (datetime.now() - timedelta(days=60)).isoformat(),
        }
        db.add_vacancy(vacancy)
        
        # Очищаем старые (старше 30 дней)
        deleted = db.clear_old_vacancies(days=30)
        assert deleted == 1
        assert db.vacancy_exists("old_123") is False

    def test_get_stats(self, db, sample_vacancies):
        """Тест получения статистики."""
        db.add_vacancies_batch(sample_vacancies)
        stats = db.get_stats()
        
        assert stats['total'] == 5
        assert stats['today'] == 5
        assert stats['week'] == 5
        assert 'avg_salary' in stats
        assert 'top_employers' in stats

    def test_get_salary_stats(self, db, sample_vacancies):
        """Тест получения статистики по зарплатам."""
        db.add_vacancies_batch(sample_vacancies)
        stats = db.get_salary_stats()
        
        assert 'min_from' in stats
        assert 'max_to' in stats
        assert 'avg_from' in stats
        assert 'avg_to' in stats
        assert stats['with_salary'] == 5

    def test_vacancy_to_dict(self, db, sample_vacancy):
        """Тест преобразования вакансии в словарь."""
        db.add_vacancy(sample_vacancy)
        vacancies = db.get_all_vacancies()
        
        assert len(vacancies) == 1
        v = vacancies[0]
        assert v['name'] == "Python Developer"
        assert v['employer'] == "Test Company"
        assert v['salary_from'] == 100000
        assert v['salary_to'] == 150000
