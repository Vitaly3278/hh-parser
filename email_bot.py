#!/usr/bin/env python3
"""Модуль для отправки Email уведомлений."""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

logger = logging.getLogger(__name__)


class EmailNotifier:
    """Отправка уведомлений по Email."""

    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        recipient: str,
        use_tls: bool = True,
    ):
        """
        Инициализация Email нотификатора.

        :param host: SMTP сервер
        :param port: Порт SMTP
        :param user: Логин
        :param password: Пароль
        :param recipient: Получатель
        :param use_tls: Использовать TLS
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.recipient = recipient
        self.use_tls = use_tls

    def send_message(self, subject: str, body: str, html: bool = False) -> bool:
        """
        Отправка сообщения.

        :param subject: Тема письма
        :param body: Текст сообщения
        :param html: Формат HTML
        :return: True если успешно
        """
        if not all([self.host, self.port, self.user, self.password, self.recipient]):
            logger.warning("Email параметры не полностью заполнены")
            return False

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.user
        msg["To"] = self.recipient

        # Добавляем контент в нужном формате
        mime_type = "html" if html else "plain"
        msg.attach(MIMEText(body, mime_type, "utf-8"))

        try:
            logger.debug(f"Подключение к SMTP: {self.host}:{self.port}")
            server = smtplib.SMTP(self.host, self.port)

            if self.use_tls:
                server.starttls()

            server.login(self.user, self.password)
            server.sendmail(self.user, self.recipient, msg.as_string())
            server.quit()

            logger.info(f"Email отправлен: {subject}")
            return True

        except smtplib.SMTPException as e:
            logger.error(f"SMTP ошибка при отправке Email: {e}")
            return False
        except Exception as e:
            logger.error(f"Ошибка при отправке Email: {e}")
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
        salary_parts = []
        if salary:
            from_salary = salary.get("from")
            to_salary = salary.get("to")
            currency = salary.get("currency", "RUR")

            if from_salary and to_salary:
                salary_parts.append(f"{from_salary} - {to_salary} {currency}")
            elif from_salary:
                salary_parts.append(f"от {from_salary} {currency}")
            elif to_salary:
                salary_parts.append(f"до {to_salary} {currency}")

        salary_str = "Зарплата не указана"
        if salary_parts:
            salary_str = salary_parts[0]

        # HTML версия
        html_body = f"""
        <html>
        <body>
            <h2>🔔 Новая вакансия!</h2>
            <p><b>{name}</b></p>
            <p>🏢 {employer}</p>
            <p>💰 {salary_str}</p>
            <p>📍 {city}</p>
            <p><a href="{url}">👉 Смотреть вакансию</a></p>
        </body>
        </html>
        """

        # Текстовая версия
        text_body = f"""
🔔 Новая вакансия!

{name}
🏢 {employer}
💰 {salary_str}
📍 {city}
👉 {url}
        """.strip()

        subject = f"Новая вакансия: {name}"
        return self.send_message(subject, html_body, html=True)

    def test_connection(self) -> bool:
        """
        Проверка соединения с SMTP.

        :return: True если соединение успешно
        """
        logger.info(f"Проверка соединения с SMTP {self.host}:{self.port}...")
        return self.send_message("HH Tracker подключен", "Бот подключен и готов к работе!")
