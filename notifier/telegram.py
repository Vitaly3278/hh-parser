"""Telegram уведомлений на aiohttp."""

import logging
from typing import Any, Dict, Optional

import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from core import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from core.exceptions import NotificationError
from storage.models import Vacancy
from .base import AbstractNotifier


logger = logging.getLogger(__name__)


class TelegramNotifier(AbstractNotifier):
    """Telegram бот для отправки уведомлений."""

    def __init__(
        self,
        token: Optional[str] = None,
        chat_id: Optional[str] = None,
        session: Optional[aiohttp.ClientSession] = None
    ):
        """
        Инициализация нотификатора.

        :param token: Токен бота
        :param chat_id: ID чата
        :param session: aiohttp сессия
        """
        self.token = token or TELEGRAM_BOT_TOKEN
        self.chat_id = chat_id or TELEGRAM_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self._session = session

    async def _get_session(self) -> aiohttp.ClientSession:
        """Получение или создание сессии."""
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self._session

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((aiohttp.ClientError, NotificationError)),
        reraise=True
    )
    async def _make_request(self, method: str, data: dict) -> dict:
        """
        Вызов API Telegram с retry логикой.

        :param method: Метод API
        :param data: Данные запроса
        :return: Результат
        """
        session = await self._get_session()
        url = f"{self.base_url}/{method}"

        try:
            async with session.post(
                url,
                data=data,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                result = await response.json()

                if not result.get("ok"):
                    error_desc = result.get("description", "Unknown error")
                    raise NotificationError(f"Telegram API error: {error_desc}")

                return result

        except aiohttp.ClientError as e:
            logger.warning(f"Client error, will retry: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise NotificationError(f"Unexpected error: {e}")

    async def send(
        self,
        message: str,
        parse_mode: str = "HTML",
        **kwargs: Any
    ) -> bool:
        """
        Отправить текстовое сообщение.

        :param message: Текст сообщения
        :param parse_mode: Режим парсинга
        :param kwargs: Дополнительные параметры
        :return: True если успешно
        """
        if not self.token or not self.chat_id:
            logger.warning("Telegram токен или chat_id не указаны")
            return False

        data = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": parse_mode,
        }

        try:
            await self._make_request("sendMessage", data)
            logger.debug("Сообщение отправлено в Telegram")
            return True
        except NotificationError as e:
            # Пробуем без parse_mode
            logger.debug(f"Повторная отправка без {parse_mode}...")
            data.pop("parse_mode", None)
            try:
                await self._make_request("sendMessage", data)
                return True
            except NotificationError as e:
                logger.error(f"Не удалось отправить сообщение: {e}")
                return False

    async def send_vacancy(self, vacancy: Vacancy) -> bool:
        """
        Отправить уведомление о вакансии.

        :param vacancy: Вакансия
        :return: True если успешно
        """
        message = (
            f"🔔 <b>Новая вакансия!</b>\n\n"
            f"<b>{vacancy.name}</b>\n"
            f"🏢 {vacancy.employer or 'Не указан'}\n"
            f"{vacancy.formatted_salary()}\n"
            f"📍 {vacancy.area or 'Не указан'}\n\n"
            f"🔗 <a href='{vacancy.url or '#'}'>Ссылка на вакансию</a>"
        )

        return await self.send(message)

    async def send_stats(self, stats: Dict[str, Any]) -> bool:
        """
        Отправить статистику.

        :param stats: Статистика
        :return: True если успешно
        """
        message = (
            f"📊 <b>Статистика вакансий</b>\n\n"
            f"Всего в базе: <b>{stats.get('total', 0)}</b>\n"
            f"За сегодня: <b>{stats.get('today', 0)}</b>\n"
            f"За неделю: <b>{stats.get('week', 0)}</b>\n"
        )

        if stats.get('avg_salary'):
            message += f"Средняя ЗП: <b>{stats['avg_salary']}</b>\n"

        return await self.send(message)

    async def test_connection(self) -> bool:
        """
        Проверка соединения с Telegram API.

        :return: True если успешно
        """
        logger.info("Проверка соединения с Telegram...")
        try:
            return await self.send(
                "✅ <b>HH Tracker подключен!</b>\n\n"
                "Бот готов к работе и отправке уведомлений."
            )
        except Exception as e:
            logger.error(f"Ошибка подключения к Telegram: {e}")
            return False

    async def close(self) -> None:
        """Закрытие сессии."""
        if self._session and hasattr(self._session, 'close'):
            await self._session.close()
