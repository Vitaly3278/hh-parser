"""Базовый класс для уведомлений."""

from abc import ABC, abstractmethod
from typing import Any, Dict

from modules.storage.models import Vacancy


class AbstractNotifier(ABC):
    """Абстрактный класс уведомлений (Порт)."""

    @abstractmethod
    async def send(self, message: str, **kwargs: Any) -> bool:
        """
        Отправить сообщение.

        :param message: Текст сообщения
        :param kwargs: Дополнительные параметры
        :return: True если успешно
        """
        pass

    @abstractmethod
    async def send_vacancy(self, vacancy: Vacancy) -> bool:
        """
        Отправить уведомление о вакансии.

        :param vacancy: Вакансия
        :return: True если успешно
        """
        pass

    @abstractmethod
    async def send_stats(self, stats: Dict[str, Any]) -> bool:
        """
        Отправить статистику.

        :param stats: Статистика
        :return: True если успешно
        """
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """
        Проверить соединение.

        :return: True если соединение успешно
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Закрыть соединение."""
        pass
