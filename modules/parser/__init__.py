"""Модуль парсера hh.ru."""

from .hh_client import HHClient
from .filters import VacancyFilter


__all__ = [
    'HHClient',
    'VacancyFilter',
]
