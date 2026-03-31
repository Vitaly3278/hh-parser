#!/usr/bin/env python3
"""Модуль для работы с базой данных вакансий на SQLAlchemy."""

import logging
from datetime import datetime
from typing import List, Optional, Dict

from sqlalchemy import (
    create_engine,
    Column,
    String,
    Integer,
    DateTime,
    Index,
    func,
    select,
    delete,
)
from sqlalchemy.orm import sessionmaker, declarative_base

logger = logging.getLogger(__name__)

Base = declarative_base()


class Vacancy(Base):
    """Модель вакансии."""
    __tablename__ = 'vacancies'

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    employer = Column(String)
    salary_from = Column(Integer)
    salary_to = Column(Integer)
    currency = Column(String, default='RUR')
    area = Column(String)
    url = Column(String)
    published_at = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_created_at', 'created_at'),
        Index('idx_published_at', 'published_at'),
    )

    def to_dict(self) -> dict:
        """Преобразование в словарь."""
        return {
            'id': self.id,
            'name': self.name,
            'employer': self.employer,
            'salary_from': self.salary_from,
            'salary_to': self.salary_to,
            'currency': self.currency,
            'area': self.area,
            'url': self.url,
            'published_at': self.published_at,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class VacancyDatabase:
    """База данных для хранения отслеживаемых вакансий."""

    def __init__(self, db_path: str):
        """
        Инициализация базы данных.

        :param db_path: Путь к файлу базы данных
        """
        self.engine = create_engine(
            f'sqlite:///{db_path}',
            echo=False,
            connect_args={'check_same_thread': False}
        )
        self.SessionLocal = sessionmaker(bind=self.engine)
        self._create_tables()
        logger.debug(f"База данных инициализирована: {db_path}")

    def _create_tables(self):
        """Создание таблиц."""
        Base.metadata.create_all(self.engine)

    def vacancy_exists(self, vacancy_id: str) -> bool:
        """
        Проверка существования вакансии в базе.

        :param vacancy_id: ID вакансии
        :return: True если вакансия существует
        """
        session = self.SessionLocal()
        try:
            stmt = select(Vacancy).where(Vacancy.id == vacancy_id)
            result = session.execute(stmt).scalar_one_or_none()
            return result is not None
        finally:
            session.close()

    def add_vacancy(self, vacancy: dict) -> bool:
        """
        Добавление вакансии в базу.

        :param vacancy: Данные вакансии
        :return: True если успешно добавлено
        """
        if self.vacancy_exists(vacancy.get("id", "")):
            return False

        session = self.SessionLocal()
        try:
            salary = vacancy.get("salary", {}) or {}
            employer = vacancy.get("employer", {}) or {}
            area = vacancy.get("area", {}) or {}

            new_vacancy = Vacancy(
                id=vacancy.get("id"),
                name=vacancy.get("name"),
                employer=employer.get("name"),
                salary_from=salary.get("from"),
                salary_to=salary.get("to"),
                currency=salary.get("currency"),
                area=area.get("name"),
                url=vacancy.get("alternate_url", vacancy.get("url")),
                published_at=vacancy.get("published_at"),
            )
            session.add(new_vacancy)
            session.commit()
            logger.debug(f"Вакансия добавлена: {vacancy.get('name', 'Без названия')}")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Ошибка при добавлении вакансии: {e}")
            return False
        finally:
            session.close()

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

        if added_count > 0:
            logger.info(f"Добавлено вакансий: {added_count}")
        return added_count

    def get_all_vacancies(self) -> List[dict]:
        """
        Получение всех вакансий из базы.

        :return: Список вакансий
        """
        session = self.SessionLocal()
        try:
            stmt = select(Vacancy).order_by(Vacancy.published_at.desc())
            results = session.execute(stmt).scalars().all()
            return [v.to_dict() for v in results]
        finally:
            session.close()

    def get_recent_vacancies(self, hours: int = 24) -> List[dict]:
        """
        Получение вакансий за последние N часов.

        :param hours: Период в часах
        :return: Список вакансий
        """
        session = self.SessionLocal()
        try:
            cutoff = datetime.utcnow()
            from datetime import timedelta
            cutoff = cutoff - timedelta(hours=hours)
            
            stmt = select(Vacancy).where(Vacancy.created_at > cutoff).order_by(Vacancy.published_at.desc())
            results = session.execute(stmt).scalars().all()
            return [v.to_dict() for v in results]
        finally:
            session.close()

    def clear_old_vacancies(self, days: int = 30) -> int:
        """
        Удаление старых вакансий.

        :param days: Возраст вакансий для удаления в днях
        :return: Количество удаленных записей
        """
        session = self.SessionLocal()
        try:
            from datetime import timedelta
            cutoff = datetime.utcnow() - timedelta(days=days)
            
            stmt = delete(Vacancy).where(Vacancy.created_at < cutoff)
            result = session.execute(stmt)
            deleted_count = result.rowcount
            session.commit()

            if deleted_count > 0:
                logger.info(f"Удалено старых записей: {deleted_count}")
            return deleted_count
        except Exception as e:
            session.rollback()
            logger.error(f"Ошибка при удалении старых вакансий: {e}")
            return 0
        finally:
            session.close()

    def get_stats(self) -> dict:
        """
        Получение статистики по базе.

        :return: Словарь со статистикой
        """
        session = self.SessionLocal()
        try:
            from datetime import timedelta
            now = datetime.utcnow()
            today_cutoff = now - timedelta(hours=24)
            week_cutoff = now - timedelta(days=7)

            # Общее количество
            total_stmt = select(func.count()).select_from(Vacancy)
            total = session.execute(total_stmt).scalar()

            # За последние 24 часа
            today_stmt = select(func.count()).select_from(Vacancy).where(Vacancy.created_at > today_cutoff)
            today = session.execute(today_stmt).scalar()

            # За последние 7 дней
            week_stmt = select(func.count()).select_from(Vacancy).where(Vacancy.created_at > week_cutoff)
            week = session.execute(week_stmt).scalar()

            # Средняя зарплата
            avg_stmt = select(func.avg(Vacancy.salary_from)).where(Vacancy.salary_from.isnot(None))
            avg_salary = session.execute(avg_stmt).scalar()

            # Топ работодателей
            employers_stmt = select(
                Vacancy.employer,
                func.count().label('count')
            ).where(
                Vacancy.employer.isnot(None)
            ).group_by(
                Vacancy.employer
            ).order_by(
                func.count().desc()
            ).limit(5)
            top_employers = session.execute(employers_stmt).all()

            return {
                "total": total or 0,
                "today": today or 0,
                "week": week or 0,
                "avg_salary": round(avg_salary, 0) if avg_salary else None,
                "top_employers": [{"employer": row[0], "count": row[1]} for row in top_employers],
            }
        finally:
            session.close()

    def get_salary_stats(self) -> dict:
        """
        Статистика по зарплатам.

        :return: Словарь со статистикой зарплат
        """
        session = self.SessionLocal()
        try:
            stmt = select(
                func.min(Vacancy.salary_from),
                func.max(Vacancy.salary_to),
                func.avg(Vacancy.salary_from),
                func.avg(Vacancy.salary_to),
                func.count(),
            ).where(
                (Vacancy.salary_from.isnot(None)) | (Vacancy.salary_to.isnot(None))
            )
            row = session.execute(stmt).one()

            return {
                "min_from": row[0],
                "max_to": row[1],
                "avg_from": round(row[2], 0) if row[2] else None,
                "avg_to": round(row[3], 0) if row[3] else None,
                "with_salary": row[4],
            }
        finally:
            session.close()
