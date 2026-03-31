"""Клиент для API hh.ru."""

import logging
from typing import Optional, List, Dict, Any
import aiohttp

from core import HH_AREA, HH_EXCLUDE_WORDS
from modules.storage.models import Vacancy


logger = logging.getLogger(__name__)


class HHClient:
    """Асинхронный клиент hh.ru API."""

    BASE_URL = "https://api.hh.ru/vacancies"
    USER_AGENT = "Mozilla/5.0 (compatible; HH.ru API client)"

    def __init__(
        self,
        area: Optional[str] = None,
        session: Optional[aiohttp.ClientSession] = None
    ):
        """
        Инициализация клиента.

        :param area: ID региона
        :param session: aiohttp сессия
        """
        self.area = area or HH_AREA
        self._session = session
        self._exclude_words = HH_EXCLUDE_WORDS

    async def _get_session(self) -> aiohttp.ClientSession:
        """Получение или создание сессии."""
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self._session

    async def search(
        self,
        search_text: str,
        page: int = 0,
        per_page: int = 20,
        salary_from: Optional[int] = None,
        employment: Optional[List[str]] = None,
        experience: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Поиск вакансий.

        :param search_text: Поисковый запрос
        :param page: Номер страницы
        :param per_page: Количество на странице
        :param salary_from: Минимальная зарплата
        :param employment: Тип занятости
        :param experience: Опыт работы
        :return: Результат поиска
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
            params["employment"] = ",".join(employment)

        if experience:
            params["experience"] = ",".join(experience)

        headers = {"User-Agent": self.USER_AGENT}
        session = await self._get_session()

        try:
            async with session.get(
                self.BASE_URL,
                params=params,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                response.raise_for_status()
                result = await response.json()
                logger.info(f"Найдено вакансий: {result.get('found', 0)}")
                return result
        except aiohttp.ClientError as e:
            logger.error(f"Ошибка при запросе к hh.ru: {e}")
            return {"items": [], "found": 0}
        except Exception as e:
            logger.error(f"Неожиданная ошибка при запросе к hh.ru: {e}")
            return {"items": [], "found": 0}

    async def get_vacancy_details(self, vacancy_id: str) -> Optional[Dict[str, Any]]:
        """
        Получение подробной информации о вакансии.

        :param vacancy_id: ID вакансии
        :return: Данные о вакансии
        """
        url = f"https://api.hh.ru/vacancies/{vacancy_id}"
        headers = {"User-Agent": self.USER_AGENT}
        session = await self._get_session()

        try:
            async with session.get(
                url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"Ошибка при получении деталей вакансии: {e}")
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка при получении деталей: {e}")
            return None

    def parse_vacancy(self, data: Dict[str, Any]) -> Vacancy:
        """
        Парсинг данных вакансии в модель.

        :param data: Данные вакансии от API
        :return: Модель Vacancy
        """
        salary = data.get("salary", {}) or {}
        employer = data.get("employer", {}) or {}
        area = data.get("area", {}) or {}

        return Vacancy(
            id=data.get("id", ""),
            name=data.get("name", "Без названия"),
            employer=employer.get("name"),
            salary_from=salary.get("from"),
            salary_to=salary.get("to"),
            currency=salary.get("currency", "RUR"),
            area=area.get("name"),
            url=data.get("alternate_url", data.get("url")),
            published_at=data.get("published_at"),
        )

    def format_vacancy(self, vacancy: Dict[str, Any]) -> str:
        """
        Форматирование вакансии в строку.

        :param vacancy: Данные вакансии (словарь)
        :return: Форматированная строка
        """
        name = vacancy.get("name", "Без названия")
        employer = vacancy.get("employer", {}).get("name", "Не указан") if vacancy.get("employer") else "Не указан"
        salary = vacancy.get("salary", {})
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

        city = vacancy.get("area", {}).get("name", "Не указан") if vacancy.get("area") else "Не указан"
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

    def filter_by_exclude_words(self, vacancies: List[Dict[str, Any]], exclude_words: List[str]) -> List[Dict[str, Any]]:
        """
        Фильтрация вакансий по исключающим словам.

        :param vacancies: Список вакансий
        :param exclude_words: Слова для исключения
        :return: Отфильтрованный список
        """
        if not exclude_words:
            return vacancies

        exclude_words_lower = [w.lower() for w in exclude_words]
        filtered = []

        for vacancy in vacancies:
            name = vacancy.get("name", "").lower()
            description = vacancy.get("description", "").lower() if vacancy.get("description") else ""
            text = f"{name} {description}"

            if not any(word in text for word in exclude_words_lower):
                filtered.append(vacancy)

        return filtered

    async def close(self):
        """Закрытие сессии."""
        if self._session and hasattr(self._session, 'close'):
            await self._session.close()
