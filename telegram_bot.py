#!/usr/bin/env python3
"""Модуль для отправки уведомлений в Telegram."""

import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)


class TelegramBot:
    """Бот для отправки сообщений в Telegram."""

    def __init__(self, token: str, chat_id: str):
        """
        Инициализация бота.

        :param token: Токен бота от @BotFather
        :param chat_id: ID чата для отправки сообщений
        """
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{token}"

    def send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """
        Отправка текстового сообщения.

        :param message: Текст сообщения
        :param parse_mode: Режим парсинга (HTML или Markdown)
        :return: True если успешно
        """
        if not self.token or not self.chat_id:
            logger.warning("Telegram токен или chat_id не указаны")
            return False

        url = f"{self.base_url}/sendMessage"
        data = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": parse_mode,
            "disable_web_page_preview": False,
        }

        try:
            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()
            result = response.json()
            if result.get("ok"):
                logger.debug("Сообщение отправлено в Telegram")
                return True
            else:
                logger.error(f"Telegram API вернул ошибку: {result}")
                return False
        except requests.RequestException as e:
            logger.error(f"Ошибка при отправке сообщения в Telegram: {e}")
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
                salary_str = f"💰 {from_salary} - {to_salary} {currency}"
            elif from_salary:
                salary_str = f"💰 от {from_salary} {currency}"
            elif to_salary:
                salary_str = f"💰 до {to_salary} {currency}"

        # Формируем сообщение
        message = (
            f"🔔 <b>Новая вакансия!</b>\n\n"
            f"<b>{name}</b>\n"
            f"🏢 {employer}\n"
            f"{salary_str}\n"
            f"📍 {city}\n\n"
            f"<a href='{url}'>👉 Смотреть вакансию</a>"
        )

        return self.send_message(message)

    def test_connection(self) -> bool:
        """
        Проверка соединения с Telegram API.

        :return: True если соединение успешно
        """
        logger.info("Проверка соединения с Telegram...")
        return self.send_message("✅ Бот подключен и готов к работе!")
