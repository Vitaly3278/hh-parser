"""Репозиторий для работы с вакансиями."""

import logging
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from .models import Vacancy

logger = logging.getLogger(__name__)


class AbstractVacancyRepository(ABC):
    """Абстрактный репозиторий вакансий (Порт)."""

    @abstractmethod
    def get_by_id(self, vacancy_id: str) -> Optional[Vacancy]:
        """Получить вакансию по ID."""
        pass

    @abstractmethod
    def exists(self, vacancy_id: str) -> bool:
        """Проверить существование вакансии."""
        pass

    @abstractmethod
    def add(self, vacancy: Vacancy) -> bool:
        """Добавить вакансию."""
        pass

    @abstractmethod
    def add_batch(self, vacancies: List[Vacancy]) -> int:
        """Пакетное добавление вакансий."""
        pass

    @abstractmethod
    def get_all(self, limit: Optional[int] = None, offset: int = 0) -> List[Vacancy]:
        """Получить все вакансии."""
        pass

    @abstractmethod
    def get_recent(self, hours: int = 24) -> List[Vacancy]:
        """Получить вакансии за последние N часов."""
        pass

    @abstractmethod
    def clear_old(self, days: int = 30) -> int:
        """Удалить старые вакансии."""
        pass

    @abstractmethod
    def get_stats(self) -> dict:
        """Получить статистику."""
        pass

    @abstractmethod
    def get_salary_stats(self) -> dict:
        """Получить статистику по зарплатам."""
        pass

    @abstractmethod
    def count(self) -> int:
        """Получить общее количество вакансий."""
        pass


class VacancyRepository(AbstractVacancyRepository):
    """Реализация репозитория на SQLAlchemy."""

    def __init__(self, session_factory):
        """
        Инициализация репозитория.

        :param session_factory: Фабрика сессий SQLAlchemy
        """
        self.session_factory = session_factory

    def _get_session(self):
        """Получение сессии."""
        return self.session_factory()

    def get_by_id(self, vacancy_id: str) -> Optional[Vacancy]:
        """Получить вакансию по ID."""
        from sqlalchemy import select
        from .database import VacancyModel

        session = self._get_session()
        try:
            stmt = select(VacancyModel).where(VacancyModel.id == vacancy_id)
            result = session.execute(stmt).scalar_one_or_none()
            if result:
                return Vacancy.from_dict(result.to_dict())
            return None
        finally:
            session.close()

    def exists(self, vacancy_id: str) -> bool:
        """Проверить существование вакансии."""
        return self.get_by_id(vacancy_id) is not None

    def add(self, vacancy: Vacancy) -> bool:
        """Добавить вакансию."""
        from sqlalchemy import select
        from .database import VacancyModel
        from datetime import datetime

        session = self._get_session()
        try:
            # Проверяем существование в той же сессии
            stmt = select(VacancyModel).where(VacancyModel.id == vacancy.id)
            exists = session.execute(stmt).scalar_one_or_none() is not None
            
            if exists:
                return False

            # Преобразуем данные для модели
            data = vacancy.to_dict()
            # created_at должен быть datetime объектом
            if isinstance(data.get('created_at'), str):
                try:
                    data['created_at'] = datetime.fromisoformat(data['created_at'])
                except (ValueError, TypeError):
                    data['created_at'] = datetime.utcnow()

            model = VacancyModel(**data)
            session.add(model)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Ошибка при добавлении вакансии: {e}")
            return False
        finally:
            session.close()

    def add_batch(self, vacancies: List[Vacancy]) -> int:
        """Пакетное добавление вакансий."""
        added_count = 0
        for vacancy in vacancies:
            if self.add(vacancy):
                added_count += 1
        return added_count

    def get_all(self, limit: Optional[int] = None, offset: int = 0) -> List[Vacancy]:
        """Получить все вакансии."""
        from sqlalchemy import select, desc
        from .database import VacancyModel

        session = self._get_session()
        try:
            stmt = select(VacancyModel).order_by(desc(VacancyModel.published_at))
            if limit:
                stmt = stmt.limit(limit).offset(offset)
            results = session.execute(stmt).scalars().all()
            return [Vacancy.from_dict(v.to_dict()) for v in results]
        finally:
            session.close()

    def get_recent(self, hours: int = 24) -> List[Vacancy]:
        """Получить вакансии за последние N часов."""
        from sqlalchemy import select, desc
        from .database import VacancyModel
        from datetime import timedelta

        session = self._get_session()
        try:
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            stmt = (
                select(VacancyModel)
                .where(VacancyModel.created_at > cutoff)
                .order_by(desc(VacancyModel.published_at))
            )
            results = session.execute(stmt).scalars().all()
            return [Vacancy.from_dict(v.to_dict()) for v in results]
        finally:
            session.close()

    def clear_old(self, days: int = 30) -> int:
        """Удалить старые вакансии."""
        from sqlalchemy import delete
        from .database import VacancyModel
        from datetime import timedelta

        session = self._get_session()
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            stmt = delete(VacancyModel).where(VacancyModel.created_at < cutoff)
            result = session.execute(stmt)
            deleted_count = result.rowcount
            session.commit()
            return deleted_count
        except Exception:
            session.rollback()
            return 0
        finally:
            session.close()

    def get_stats(self) -> dict:
        """Получить статистику."""
        from sqlalchemy import func, select
        from .database import VacancyModel
        from datetime import timedelta

        session = self._get_session()
        try:
            now = datetime.utcnow()
            today_cutoff = now - timedelta(hours=24)
            week_cutoff = now - timedelta(days=7)

            # Общее количество
            total = session.execute(
                select(func.count()).select_from(VacancyModel)
            ).scalar() or 0

            # За последние 24 часа
            today = session.execute(
                select(func.count())
                .select_from(VacancyModel)
                .where(VacancyModel.created_at > today_cutoff)
            ).scalar() or 0

            # За последние 7 дней
            week = session.execute(
                select(func.count())
                .select_from(VacancyModel)
                .where(VacancyModel.created_at > week_cutoff)
            ).scalar() or 0

            # Средняя зарплата
            avg_salary = session.execute(
                select(func.avg(VacancyModel.salary_from))
                .where(VacancyModel.salary_from.isnot(None))
            ).scalar()

            # Топ работодателей
            employers_stmt = (
                select(VacancyModel.employer, func.count().label('count'))
                .where(VacancyModel.employer.isnot(None))
                .group_by(VacancyModel.employer)
                .order_by(func.count().desc())
                .limit(5)
            )
            top_employers = session.execute(employers_stmt).all()

            return {
                "total": total,
                "today": today,
                "week": week,
                "avg_salary": round(avg_salary, 0) if avg_salary else None,
                "top_employers": [{"employer": row[0], "count": row[1]} for row in top_employers],
            }
        finally:
            session.close()

    def get_salary_stats(self) -> dict:
        """Получить статистику по зарплатам."""
        from sqlalchemy import func, select
        from .database import VacancyModel

        session = self._get_session()
        try:
            stmt = select(
                func.min(VacancyModel.salary_from),
                func.max(VacancyModel.salary_to),
                func.avg(VacancyModel.salary_from),
                func.avg(VacancyModel.salary_to),
                func.count(),
            ).where(
                (VacancyModel.salary_from.isnot(None)) | (VacancyModel.salary_to.isnot(None))
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

    def count(self) -> int:
        """Получить общее количество вакансий."""
        from sqlalchemy import func, select
        from .database import VacancyModel

        session = self._get_session()
        try:
            return session.execute(
                select(func.count()).select_from(VacancyModel)
            ).scalar() or 0
        finally:
            session.close()
