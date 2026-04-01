"""Сервис для работы с вакансиями."""

import logging
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

import aiohttp

from core import (
    HH_SEARCH_TEXT,
    HH_AREA,
    HH_SALARY_FROM,
    HH_EMPLOYMENT,
    HH_EXPERIENCE,
    HH_EXCLUDE_WORDS,
    CHECK_INTERVAL,
)
from core.logger import get_logger
from modules.parser import HHClient, VacancyFilter
from modules.storage import Vacancy, VacancyRepository
from modules.notifier import AbstractNotifier

if TYPE_CHECKING:
    from modules.storage.repository import VacancyRepository


logger = get_logger(__name__)


class VacancyService:
    """Сервис для управления вакансиями."""

    def __init__(
        self,
        repository: 'VacancyRepository',
        http_session: Optional[aiohttp.ClientSession] = None
    ):
        """
        Инициализация сервиса.

        :param repository: Репозиторий вакансий
        :param http_session: aiohttp сессия
        """
        self.repository = repository
        self.http_session = http_session

        # Инициализация компонентов
        area = HH_AREA if HH_AREA else None
        self.parser = HHClient(area=area, session=http_session)
        self.filter = VacancyFilter(exclude_words=HH_EXCLUDE_WORDS if HH_EXCLUDE_WORDS else None)

        # Статистика
        self.stats = {
            'checks_count': 0,
            'new_vacancies_count': 0,
            'errors_count': 0,
            'last_check': None,
        }

    async def check_vacancies(self) -> int:
        """
        Проверка новых вакансий.

        :return: Количество новых вакансий
        """
        logger.info(f"Проверка вакансий... (запрос: {HH_SEARCH_TEXT})")
        self.stats['checks_count'] += 1
        self.stats['last_check'] = datetime.now().isoformat()

        try:
            # Поиск вакансий
            result = await self.parser.search(
                search_text=HH_SEARCH_TEXT,
                salary_from=HH_SALARY_FROM,
                employment=HH_EMPLOYMENT,
                experience=HH_EXPERIENCE,
            )

            items = result.get("items", [])
            found = result.get("found", 0)

            logger.info(f"Найдено вакансий: {found}, получено: {len(items)}")

            # Парсинг вакансий в модели
            vacancies = [self.parser.parse_vacancy(item) for item in items]

            # Фильтрация по исключающим словам
            if HH_EXCLUDE_WORDS:
                vacancies = self.filter.filter_by_exclude_words(vacancies)
                logger.info(f"После фильтрации: {len(vacancies)} вакансий")

            # Фильтрация новых вакансий
            new_vacancies = [
                v for v in vacancies
                if not self.repository.exists(v.id)
            ]

            logger.info(f"Новых вакансий: {len(new_vacancies)}")

            # Добавление в базу
            for vacancy in new_vacancies:
                self.repository.add(vacancy)
                self.stats['new_vacancies_count'] += 1

            # Сохраняем новые вакансии для уведомлений
            self._last_new_vacancies = new_vacancies

            # Очистка старых записей (раз в час)
            if datetime.now().minute == 0:
                deleted = self.repository.clear_old(days=30)
                if deleted:
                    logger.info(f"Удалено старых записей: {deleted}")

            return len(new_vacancies)

        except Exception as e:
            logger.error(f"Ошибка при проверке вакансий: {e}", exc_info=True)
            self.stats['errors_count'] += 1
            return 0

    async def notify_new_vacancies(
        self,
        notifiers: List[AbstractNotifier]
    ) -> None:
        """
        Отправка уведомлений о новых вакансиях.

        :param notifiers: Список нотификаторов
        """
        new_vacancies = getattr(self, '_last_new_vacancies', [])
        for vacancy in new_vacancies:
            try:
                await self.notify_vacancy(vacancy, notifiers)
            except Exception as e:
                logger.error(f"Ошибка отправки уведомления: {e}")
        # Очищаем список после отправки
        self._last_new_vacancies = []

    async def notify_vacancy(
        self,
        vacancy: Vacancy,
        notifiers: List[AbstractNotifier]
    ) -> None:
        """
        Отправка уведомления о вакансии.

        :param vacancy: Вакансия
        :param notifiers: Список нотификаторов
        """
        for notifier in notifiers:
            try:
                await notifier.send_vacancy(vacancy)
            except Exception as e:
                logger.error(f"Ошибка отправки уведомления: {e}")

    def get_stats(self) -> dict:
        """Получение статистики сервиса."""
        repo_stats = self.repository.get_stats()
        return {**self.stats, **repo_stats}

    async def close(self):
        """Закрытие соединений."""
        await self.parser.close()
