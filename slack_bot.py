#!/usr/bin/env python3
"""Асинхронный модуль для отправки уведомлений в Slack на aiohttp."""

import logging
from typing import Optional

import aiohttp

logger = logging.getLogger(__name__)


class SlackBot:
    """Асинхронный бот для отправки сообщений в Slack."""

    def __init__(self, webhook_url: str, session: Optional[aiohttp.ClientSession] = None):
        """
        Инициализация бота.

        :param webhook_url: URL вебхука от Slack
        :param session: aiohttp сессия (опционально)
        """
        self.webhook_url = webhook_url
        self._session = session

    async def _get_session(self) -> aiohttp.ClientSession:
        """Получение или создание сессии."""
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self._session

    async def send_message(self, message: str, blocks: Optional[list] = None) -> bool:
        """
        Отправка сообщения.

        :param message: Текст сообщения
        :param blocks: Блоки Slack (опционально)
        :return: True если успешно
        """
        if not self.webhook_url:
            logger.warning("Slack webhook URL не указан")
            return False

        payload = {"text": message}
        if blocks:
            payload["blocks"] = blocks

        session = await self._get_session()

        try:
            async with session.post(self.webhook_url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as response:
                response.raise_for_status()
                result = await response.text()

                if result == "ok":
                    logger.debug("Сообщение отправлено в Slack")
                    return True
                else:
                    logger.error(f"Slack вернул ошибку: {result}")
                    return False

        except aiohttp.ClientError as e:
            logger.error(f"Ошибка при отправке сообщения в Slack: {e}")
            return False
        except Exception as e:
            logger.error(f"Неожиданная ошибка при отправке в Slack: {e}")
            return False

    async def send_vacancy(self, vacancy_data: dict) -> bool:
        """
        Отправка информации о вакансии.

        :param vacancy_data: Словарь с данными вакансии
        :return: True если успешно
        """
        name = vacancy_data.get("name", "Без названия")
        employer = vacancy_data.get("employer", {}).get("name", "Не указан")
        salary = vacancy_data.get("salary", {})
        city = vacancy_data.get("area", {}).get("name", "Не указан")
        url = vacancy_data.get("alternate_url", vacancy_data.get("url", ""))

        # Формируем зарплату
        salary_str = "Зарплата не указана"
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

        # Формируем блоки Slack
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "🔔 Новая вакансия!", "emoji": True}
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Вакансия*\n{name}"},
                    {"type": "mrkdwn", "text": f"*Компания*\n{employer}"},
                ]
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Зарплата*\n{salary_str}"},
                    {"type": "mrkdwn", "text": f"*Город*\n{city}"},
                ]
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "👉 Смотреть вакансию", "emoji": True},
                        "url": url,
                        "action_id": "view_vacancy",
                    }
                ]
            },
        ]

        message = f"🔔 Новая вакансия: {name} в {employer}"
        return await self.send_message(message, blocks)

    async def test_connection(self) -> bool:
        """
        Проверка соединения с Slack.

        :return: True если соединение успешно
        """
        logger.info("Проверка соединения с Slack...")
        return await self.send_message("✅ HH Tracker подключен и готов к работе!")
