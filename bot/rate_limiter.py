"""Ограничитель частоты запросов."""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from core import BOT_RATE_LIMIT, BOT_RATE_WINDOW
from core.exceptions import RateLimitError


logger = logging.getLogger(__name__)


class RateLimiter:
    """Ограничитель частоты запросов от пользователя."""

    def __init__(
        self,
        max_requests: Optional[int] = None,
        window_seconds: Optional[int] = None
    ):
        """
        Инициализация ограничителя.

        :param max_requests: Максимум запросов
        :param window_seconds: Окно времени в секундах
        """
        self.max_requests = max_requests or BOT_RATE_LIMIT
        self.window_seconds = window_seconds or BOT_RATE_WINDOW
        self.requests: Dict[int, List[float]] = {}

    def is_allowed(self, user_id: int) -> bool:
        """
        Проверка, разрешён ли запрос от пользователя.

        :param user_id: ID пользователя
        :return: True если разрешено
        """
        now = datetime.now().timestamp()

        if user_id not in self.requests:
            self.requests[user_id] = []

        # Удаляем старые запросы
        self.requests[user_id] = [
            ts for ts in self.requests[user_id]
            if now - ts < self.window_seconds
        ]

        # Проверяем лимит
        if len(self.requests[user_id]) >= self.max_requests:
            return False

        self.requests[user_id].append(now)
        return True

    def get_wait_time(self, user_id: int) -> float:
        """
        Время ожидания до следующего запроса.

        :param user_id: ID пользователя
        :return: Время ожидания в секундах
        """
        if user_id not in self.requests or not self.requests[user_id]:
            return 0

        oldest = min(self.requests[user_id])
        wait = self.window_seconds - (datetime.now().timestamp() - oldest)
        return max(0, wait)

    def check_rate_limit(self, user_id: int) -> None:
        """
        Проверка лимита с выбрасыванием исключения.

        :param user_id: ID пользователя
        :raises RateLimitError: Если лимит превышен
        """
        if not self.is_allowed(user_id):
            wait_time = self.get_wait_time(user_id)
            raise RateLimitError(wait_time)
