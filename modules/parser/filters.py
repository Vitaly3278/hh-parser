"""Фильтры для вакансий."""

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from modules.storage.models import Vacancy


logger = logging.getLogger(__name__)


class VacancyFilter:
    """Фильтр для обработки вакансий."""

    def __init__(self, exclude_words: Optional[List[str]] = None):
        """
        Инициализация фильтра.

        :param exclude_words: Слова для исключения
        """
        self.exclude_words = [w.lower() for w in exclude_words] if exclude_words else []

    def filter_by_date(self, vacancies: List[Vacancy], hours: int = 24) -> List[Vacancy]:
        """
        Фильтрация по дате публикации.

        :param vacancies: Список вакансий
        :param hours: Период в часах
        :return: Отфильтрованный список
        """
        filtered = []
        now = datetime.utcnow()
        cutoff = now - timedelta(hours=hours)

        for vacancy in vacancies:
            if vacancy.published_at:
                try:
                    pub_date = datetime.fromisoformat(
                        vacancy.published_at.replace("Z", "+00:00")
                    ).replace(tzinfo=None)
                    if pub_date >= cutoff:
                        filtered.append(vacancy)
                except (ValueError, TypeError):
                    filtered.append(vacancy)
            else:
                filtered.append(vacancy)

        return filtered

    def filter_by_exclude_words(self, vacancies: List[Vacancy]) -> List[Vacancy]:
        """
        Фильтрация по исключающим словам.

        :param vacancies: Список вакансий
        :return: Отфильтрованный список
        """
        if not self.exclude_words:
            return vacancies

        filtered = []
        for vacancy in vacancies:
            text = f"{vacancy.name.lower()} {vacancy.employer.lower() if vacancy.employer else ''}"
            if not any(word in text for word in self.exclude_words):
                filtered.append(vacancy)
            else:
                logger.debug(f"Исключена вакансия: {vacancy.name}")

        return filtered

    def filter_by_salary(
        self,
        vacancies: List[Vacancy],
        min_salary: Optional[int] = None
    ) -> List[Vacancy]:
        """
        Фильтрация по минимальной зарплате.

        :param vacancies: Список вакансий
        :param min_salary: Минимальная зарплата
        :return: Отфильтрованный список
        """
        if min_salary is None:
            return vacancies

        return [
            v for v in vacancies
            if (v.salary_from and v.salary_from >= min_salary) or
               (v.salary_to and v.salary_to >= min_salary)
        ]

    def filter_by_area(
        self,
        vacancies: List[Vacancy],
        areas: List[str]
    ) -> List[Vacancy]:
        """
        Фильтрация по регионам.

        :param vacancies: Список вакансий
        :param areas: Список регионов
        :return: Отфильтрованный список
        """
        if not areas:
            return vacancies

        return [
            v for v in vacancies
            if v.area and v.area in areas
        ]
