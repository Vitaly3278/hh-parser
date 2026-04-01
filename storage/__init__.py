"""Модуль хранения данных."""

from .models import Vacancy
from .repository import VacancyRepository, AbstractVacancyRepository
from .database import Database, get_database


__all__ = [
    'Vacancy',
    'VacancyRepository',
    'AbstractVacancyRepository',
    'Database',
    'get_database',
]
