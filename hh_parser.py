#!/usr/bin/env python3
"""Модуль для работы с API hh.ru."""

import requests
from datetime import datetime
from typing import Optional


class HHParser:
    """Парсер вакансий с hh.ru."""

    BASE_URL = "https://api.hh.ru/vacancies"
    USER_AGENT = "hh vacancy tracker (your_email@example.com)"

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
        :param employment: Тип занятости (например, ['full', 'part', 'project'])
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
            response = requests.get(self.BASE_URL, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Ошибка при запросе к hh.ru: {e}")
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
            print(f"Ошибка при получении деталей вакансии: {e}")
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
