"""Email уведомлений."""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any, Dict, Optional

from core import (
    EMAIL_ENABLED,
    EMAIL_HOST,
    EMAIL_PORT,
    EMAIL_USER,
    EMAIL_PASSWORD,
    EMAIL_RECIPIENT,
)
from core.exceptions import NotificationError
from storage.models import Vacancy
from .base import AbstractNotifier


logger = logging.getLogger(__name__)


class EmailNotifier(AbstractNotifier):
    """Email нотификатор."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        recipient: Optional[str] = None,
        use_tls: bool = True,
    ):
        """
        Инициализация нотификатора.

        :param host: SMTP сервер
        :param port: Порт SMTP
        :param user: Логин
        :param password: Пароль
        :param recipient: Получатель
        :param use_tls: Использовать TLS
        """
        self.host = host or EMAIL_HOST
        self.port = port or EMAIL_PORT
        self.user = user or EMAIL_USER
        self.password = password or EMAIL_PASSWORD
        self.recipient = recipient or EMAIL_RECIPIENT
        self.use_tls = use_tls
        self.enabled = EMAIL_ENABLED

    async def send(
        self,
        message: str,
        subject: str = "HH Tracker",
        html: bool = True,
        **kwargs: Any
    ) -> bool:
        """
        Отправить сообщение.

        :param message: Текст сообщения
        :param subject: Тема письма
        :param html: HTML формат
        :param kwargs: Дополнительные параметры
        :return: True если успешно
        """
        if not self.enabled:
            logger.debug("Email уведомления отключены")
            return False

        if not all([self.host, self.port, self.user, self.password, self.recipient]):
            logger.warning("Email параметры не полностью заполнены")
            return False

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.user
        msg["To"] = self.recipient

        mime_type = "html" if html else "plain"
        msg.attach(MIMEText(message, mime_type, "utf-8"))

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

    async def send_vacancy(self, vacancy: Vacancy) -> bool:
        """
        Отправить уведомление о вакансии.

        :param vacancy: Вакансия
        :return: True если успешно
        """
        salary_str = vacancy.formatted_salary()

        # HTML версия
        html_body = f"""
        <html>
        <body>
            <h2>🔔 Новая вакансия!</h2>
            <p><b>{vacancy.name}</b></p>
            <p>🏢 {vacancy.employer or 'Не указан'}</p>
            <p>💰 {salary_str}</p>
            <p>📍 {vacancy.area or 'Не указан'}</p>
            <p><a href="{vacancy.url or '#'}">👉 Смотреть вакансию</a></p>
        </body>
        </html>
        """

        # Текстовая версия
        text_body = f"""
🔔 Новая вакансия!

{vacancy.name}
🏢 {vacancy.employer or 'Не указан'}
💰 {salary_str}
📍 {vacancy.area or 'Не указан'}
👉 {vacancy.url or '#'}
        """.strip()

        subject = f"Новая вакансия: {vacancy.name}"
        return await self.send(text_body, subject=subject, html=False)

    async def send_stats(self, stats: Dict[str, Any]) -> bool:
        """
        Отправить статистику.

        :param stats: Статистика
        :return: True если успешно
        """
        message = f"""
📊 Статистика вакансий

Всего в базе: {stats.get('total', 0)}
За сегодня: {stats.get('today', 0)}
За неделю: {stats.get('week', 0)}
        """.strip()

        if stats.get('avg_salary'):
            message += f"\nСредняя ЗП: {stats['avg_salary']}"

        return await self.send(message, subject="Статистика вакансий", html=False)

    async def test_connection(self) -> bool:
        """
        Проверка соединения с SMTP.

        :return: True если успешно
        """
        if not self.enabled:
            logger.info("Email уведомления отключены")
            return False

        logger.info(f"Проверка соединения с SMTP {self.host}:{self.port}...")
        return await self.send("HH Tracker подключен", subject="Тест подключения", html=False)

    async def close(self) -> None:
        """Закрытие соединения (для совместимости)."""
        pass
