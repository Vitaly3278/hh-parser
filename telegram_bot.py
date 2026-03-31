#!/usr/bin/env python3
"""Асинхронный модуль для отправки уведомлений в Telegram на aiohttp."""

import logging
from typing import Optional

import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


class TelegramError(Exception):
    """Исключение для ошибок Telegram API."""
    pass


class TelegramBot:
    """Асинхронный бот для отправки сообщений в Telegram."""

    def __init__(self, token: str, chat_id: str, session: Optional[aiohttp.ClientSession] = None):
        """
        Инициализация бота.

        :param token: Токен бота от @BotFather
        :param chat_id: ID чата для отправки сообщений
        :param session: aiohttp сессия (опционально)
        """
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{token}"
        self._session = session
        self._owned_session = False

    async def _get_session(self) -> aiohttp.ClientSession:
        """Получение или создание сессии."""
        if self._session is None:
            self._session = aiohttp.ClientSession()
            self._owned_session = True
        return self._session

    async def close(self):
        """Закрытие сессии."""
        if self._owned_session and self._session:
            await self._session.close()
            self._session = None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((aiohttp.ClientError, TelegramError)),
        reraise=True
    )
    async def _make_request(self, method: str, data: dict) -> dict:
        """
        Вызов API Telegram с retry логикой.

        :param method: Метод API
        :param data: Данные запроса
        :return: Результат запроса
        """
        session = await self._get_session()
        url = f"{self.base_url}/{method}"
        
        try:
            async with session.post(url, data=data, timeout=aiohttp.ClientTimeout(total=30)) as response:
                result = await response.json()
                
                if not result.get("ok"):
                    error_desc = result.get("description", "Unknown error")
                    raise TelegramError(f"Telegram API error: {error_desc}")
                
                return result
                
        except aiohttp.ClientError as e:
            logger.warning(f"Client error, will retry: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise TelegramError(f"Unexpected error: {e}")

    async def send_message(
        self,
        message: str,
        parse_mode: str = "HTML",
        disable_web_page_preview: bool = False
    ) -> bool:
        """
        Отправка текстового сообщения.

        :param message: Текст сообщения
        :param parse_mode: Режим парсинга (HTML или Markdown)
        :param disable_web_page_preview: Отключить предпросмотр ссылок
        :return: True если успешно
        """
        if not self.token or not self.chat_id:
            logger.warning("Telegram токен или chat_id не указаны")
            return False

        data = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_web_page_preview,
        }

        try:
            result = await self._make_request("sendMessage", data)
            logger.debug("Сообщение отправлено в Telegram")
            return True
        except TelegramError as e:
            # Пробуем отправить без parse_mode
            logger.debug(f"Повторная отправка без {parse_mode}...")
            data["parse_mode"] = None
            try:
                result = await self._make_request("sendMessage", data)
                return True
            except TelegramError as e:
                logger.error(f"Не удалось отправить сообщение: {e}")
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
                salary_str = f"💰 {from_salary} - {to_salary} {currency}"
            elif from_salary:
                salary_str = f"💰 от {from_salary} {currency}"
            elif to_salary:
                salary_str = f"💰 до {to_salary} {currency}"

        message = (
            f"🔔 <b>Новая вакансия!</b>\n\n"
            f"<b>{name}</b>\n"
            f"🏢 {employer}\n"
            f"{salary_str}\n"
            f"📍 {city}\n\n"
            f"🔗 <a href='{url}'>Ссылка на вакансию</a>"
        )

        return await self.send_message(message)

    async def send_stats(self, stats: dict) -> bool:
        """
        Отправка статистики.

        :param stats: Словарь со статистикой
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

        return await self.send_message(message)

    async def send_vacancies_list(self, vacancies: list, page: int = 0) -> bool:
        """
        Отправка списка вакансий.

        :param vacancies: Список вакансий
        :param page: Номер страницы
        :return: True если успешно
        """
        if not vacancies:
            return await self.send_message("📭 Вакансий не найдено")

        per_page = 5
        start = page * per_page
        end = start + per_page
        page_vacancies = vacancies[start:end]

        message = f"📋 <b>Вакансии ({start+1}-{min(end, len(vacancies))} из {len(vacancies)})</b>\n\n"

        for i, v in enumerate(page_vacancies, start):
            salary = ""
            if v.get('salary_from') or v.get('salary_to'):
                from_s = v.get('salary_from', '')
                to_s = v.get('salary_to', '')
                curr = v.get('currency', 'RUR')
                if from_s and to_s:
                    salary = f" | 💰 {from_s}-{to_s} {curr}"
                elif from_s:
                    salary = f" | 💰 от {from_s} {curr}"
                elif to_s:
                    salary = f" | 💰 до {to_s} {curr}"

            message += f"{i}. <b>{v.get('name', 'Б/н')}</b>\n"
            message += f"   🏢 {v.get('employer', 'Б/н')}{salary}\n"
            message += f"   📍 {v.get('area', 'Б/н')}\n"
            message += f"   🔗 <a href='{v.get('url', '#')}'>Ссылка</a>\n\n"

        return await self.send_message(message)

    async def test_connection(self) -> bool:
        """
        Проверка соединения с Telegram API.

        :return: True если соединение успешно
        """
        logger.info("Проверка соединения с Telegram...")
        try:
            return await self.send_message(
                "✅ <b>HH Tracker подключен!</b>\n\n"
                "Бот готов к работе и отправке уведомлений."
            )
        except Exception as e:
            logger.error(f"Ошибка подключения к Telegram: {e}")
            return False
