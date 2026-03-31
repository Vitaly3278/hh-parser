#!/usr/bin/env python3
"""Модуль для отправки уведомлений в Slack."""

import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)


class SlackBot:
    """Бот для отправки сообщений в Slack."""

    def __init__(self, webhook_url: str):
        """
        Инициализация бота.

        :param webhook_url: URL вебхука от Slack
        """
        self.webhook_url = webhook_url

    def send_message(self, message: str, blocks: Optional[list] = None) -> bool:
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

        try:
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()

            if response.text == "ok":
                logger.debug("Сообщение отправлено в Slack")
                return True
            else:
                logger.error(f"Slack вернул ошибку: {response.text}")
                return False

        except requests.RequestException as e:
            logger.error(f"Ошибка при отправке сообщения в Slack: {e}")
            return False

    def send_vacancy(self, vacancy_data: dict) -> bool:
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
        return self.send_message(message, blocks)

    def test_connection(self) -> bool:
        """
        Проверка соединения с Slack.

        :return: True если соединение успешно
        """
        logger.info("Проверка соединения с Slack...")
        return self.send_message("✅ HH Tracker подключен и готов к работе!")
