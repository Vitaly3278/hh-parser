#!/usr/bin/env python3
"""Модуль для работы с API hh.ru."""

import logging
import requests
from datetime import datetime
from typing import Optional, List

logger = logging.getLogger(__name__)


class HHParser:
    """Парсер вакансий с hh.ru."""

    BASE_URL = "https://api.hh.ru/vacancies"
    USER_AGENT = "Mozilla/5.0 (compatible; HH.ru API client)"

    def __init__(self, area: Optional[str] = None, period: int = 1):
        """
        Инициализация парсера.

        :param area: ID региона (например, '1' для Москвы, '2' для СПб)
        :param period: Период поиска в днях (для фильтрации по дате публикации)
        """
        self.area = area
        self.period = period

    def search_vacancies(
        self,
        search_text: str,
        page: int = 0,
        per_page: int = 20,
        salary_from: Optional[int] = None,
        employment: Optional[list] = None,
        experience: Optional[list] = None,
    ) -> dict:
        """
        Поиск вакансий.

        :param search_text: Поисковый запрос (название вакансии)
        :param page: Номер страницы
        :param per_page: Количество вакансий на странице (макс. 20)
        :param salary_from: Минимальная зарплата
        :param employment: Тип занятости (например, ['full', 'part'])
        :param experience: Опыт работы (например, ['noExperience', 'between1And3'])
        :return: Словарь с данными о вакансиях
        """
        params = {
            "text": search_text,
            "page": page,
            "per_page": per_page,
        }

        if self.area:
            params["area"] = self.area

        if salary_from:
            params["salary"] = salary_from

        if employment:
            params["employment"] = employment

        if experience:
            params["experience"] = experience

        headers = {"User-Agent": self.USER_AGENT}

        try:
            logger.debug(f"Запрос к hh.ru: {params}")
            response = requests.get(self.BASE_URL, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            result = response.json()
            logger.info(f"Найдено вакансий: {result.get('found', 0)}")
            return result
        except requests.RequestException as e:
            logger.error(f"Ошибка при запросе к hh.ru: {e}")
            return {"items": [], "found": 0}

    def get_vacancy_details(self, vacancy_id: str) -> Optional[dict]:
        """
        Получение подробной информации о вакансии.

        :param vacancy_id: ID вакансии
        :return: Данные о вакансии или None
        """
        url = f"https://api.hh.ru/vacancies/{vacancy_id}"
        headers = {"User-Agent": self.USER_AGENT}

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Ошибка при получении деталей вакансии: {e}")
            return None

    def filter_by_date(self, vacancies: list, hours: int = 24) -> list:
        """
        Фильтрация вакансий по дате публикации.

        :param vacancies: Список вакансий
        :param hours: Период в часах
        :return: Отфильтрованный список
        """
        filtered = []
        now = datetime.utcnow()

        for vacancy in vacancies:
            published_at = vacancy.get("published_at")
            if published_at:
                try:
                    pub_date = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                    diff = now - pub_date.replace(tzinfo=None)
                    if diff.total_seconds() / 3600 <= hours:
                        filtered.append(vacancy)
                except (ValueError, TypeError):
                    filtered.append(vacancy)

        return filtered

    def filter_by_exclude_words(self, vacancies: list, exclude_words: List[str]) -> list:
        """
        Фильтрация вакансий по исключающим словам.

        :param vacancies: Список вакансий
        :param exclude_words: Список слов для исключения
        :return: Отфильтрованный список
        """
        if not exclude_words:
            return vacancies

        filtered = []
        exclude_words_lower = [word.lower() for word in exclude_words]

        for vacancy in vacancies:
            name = vacancy.get("name", "").lower()
            description = vacancy.get("description", "").lower() if vacancy.get("description") else ""
            text = f"{name} {description}"

            # Проверяем, содержит ли текст исключающие слова
            if not any(word in text for word in exclude_words_lower):
                filtered.append(vacancy)
            else:
                logger.debug(f"Исключена вакансия: {vacancy.get('name', 'Без названия')}")

        return filtered

    def format_vacancy(self, vacancy: dict) -> str:
        """
        Форматирование информации о вакансии для вывода.

        :param vacancy: Данные вакансии
        :return: Форматированная строка
        """
        name = vacancy.get("name", "Без названия")
        employer = vacancy.get("employer", {}).get("name", "Не указан")
        salary = vacancy.get("salary")
        salary_str = "Не указана"

        if salary:
            from_salary = salary.get("from")
            to_salary = salary.get("to")
            currency = salary.get("currency", "RUR")

            if from_salary and to_salary:
                salary_str = f"{from_salary} - {to_salary} {currency}"
            elif from_salary:
                salary_str = f"от {from_salary} {currency}"
            elif to_salary:
                salary_str = f"до {to_salary} {currency}"

        city = vacancy.get("area", {}).get("name", "Не указан")
        url = vacancy.get("alternate_url", vacancy.get("url", ""))
        published_at = vacancy.get("published_at", "")

        return (
            f"💼 **{name}**\n"
            f"🏢 {employer}\n"
            f"💰 {salary_str}\n"
            f"📍 {city}\n"
            f"🔗 {url}\n"
            f"📅 Опубликовано: {published_at}"
        )
