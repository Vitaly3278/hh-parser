#!/usr/bin/env python3
"""Модуль для работы с базой данных вакансий."""

import sqlite3
from datetime import datetime
from typing import List, Optional


class VacancyDatabase:
    """База данных для хранения отслеживаемых вакансий."""

    def __init__(self, db_path: str):
        """
        Инициализация базы данных.

        :param db_path: Путь к файлу базы данных
        """
        self.db_path = db_path
        self._create_table()

    def _create_table(self):
        """Создание таблицы вакансий."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vacancies (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                employer TEXT,
                salary_from INTEGER,
                salary_to INTEGER,
                currency TEXT,
                area TEXT,
                url TEXT,
                published_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    def vacancy_exists(self, vacancy_id: str) -> bool:
        """
        Проверка существования вакансии в базе.

        :param vacancy_id: ID вакансии
        :return: True если вакансия существует
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT 1 FROM vacancies WHERE id = ?", (vacancy_id,))
        exists = cursor.fetchone() is not None

        conn.close()
        return exists

    def add_vacancy(self, vacancy: dict) -> bool:
        """
        Добавление вакансии в базу.

        :param vacancy: Данные вакансии
        :return: True если успешно добавлено
        """
        if self.vacancy_exists(vacancy.get("id", "")):
            return False

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        salary = vacancy.get("salary", {}) or {}
        employer = vacancy.get("employer", {}) or {}
        area = vacancy.get("area", {}) or {}

        cursor.execute("""
            INSERT INTO vacancies (id, name, employer, salary_from, salary_to, 
                                   currency, area, url, published_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            vacancy.get("id"),
            vacancy.get("name"),
            employer.get("name"),
            salary.get("from"),
            salary.get("to"),
            salary.get("currency"),
            area.get("name"),
            vacancy.get("alternate_url", vacancy.get("url")),
            vacancy.get("published_at"),
        ))

        conn.commit()
        conn.close()
        return True

    def add_vacancies_batch(self, vacancies: List[dict]) -> int:
        """
        Пакетное добавление вакансий.

        :param vacancies: Список вакансий
        :return: Количество добавленных вакансий
        """
        added_count = 0
        for vacancy in vacancies:
            if self.add_vacancy(vacancy):
                added_count += 1
        return added_count

    def get_all_vacancies(self) -> List[dict]:
        """
        Получение всех вакансий из базы.

        :return: Список вакансий
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM vacancies ORDER BY published_at DESC")
        rows = cursor.fetchall()

        conn.close()
        return [dict(row) for row in rows]

    def get_recent_vacancies(self, hours: int = 24) -> List[dict]:
        """
        Получение вакансий за последние N часов.

        :param hours: Период в часах
        :return: Список вакансий
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM vacancies 
            WHERE datetime(created_at) > datetime('now', ?)
            ORDER BY published_at DESC
        """, (f"-{hours} hours",))

        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def clear_old_vacancies(self, days: int = 30) -> int:
        """
        Удаление старых вакансий.

        :param days: Возраст вакансий для удаления в днях
        :return: Количество удаленных записей
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM vacancies 
            WHERE datetime(created_at) < datetime('now', ?)
        """, (f"-{days} days",))

        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        return deleted_count

    def get_stats(self) -> dict:
        """
        Получение статистики по базе.

        :return: Словарь со статистикой
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM vacancies")
        total = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*) FROM vacancies 
            WHERE datetime(created_at) > datetime('now', '-24 hours')
        """)
        today = cursor.fetchone()[0]

        conn.close()
        return {"total": total, "today": today}
