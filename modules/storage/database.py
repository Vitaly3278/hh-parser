"""База данных на SQLAlchemy."""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    create_engine,
    Column,
    String,
    Integer,
    DateTime,
    Index,
    event,
)
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from pathlib import Path

from core import DB_PATH, DATA_DIR


Base = declarative_base()


class VacancyModel(Base):
    """Модель вакансии в БД."""

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


class Database:
    """Управление базой данных."""

    def __init__(self, db_path: Optional[str] = None):
        """
        Инициализация базы данных.

        :param db_path: Путь к файлу БД (по умолчанию из конфига)
        """
        self.db_path = db_path or DB_PATH

        # Создаём абсолютный путь
        db_file = Path(self.db_path)
        if not db_file.is_absolute():
            # Используем абсолютный путь от корня проекта
            project_root = Path(__file__).resolve().parent.parent.parent
            data_dir = project_root / DATA_DIR
            db_file = data_dir / db_file.name

        # Создаём директорию если нужно
        db_file.parent.mkdir(parents=True, exist_ok=True)

        self.engine = create_engine(
            f'sqlite:///{db_file}',
            echo=False,
            connect_args={'check_same_thread': False},
        )

        self.SessionLocal = sessionmaker(bind=self.engine)

        # Создаём таблицы
        self._create_tables()

    def _create_tables(self):
        """Создание таблиц."""
        Base.metadata.create_all(self.engine)

    def get_session(self) -> Session:
        """Получить сессию."""
        return self.SessionLocal()

    def dispose(self):
        """Закрытие соединения."""
        self.engine.dispose()


# Глобальный экземпляр для DI
_database_instance: Optional[Database] = None


def get_database() -> Database:
    """Получить экземпляр Database (Singleton)."""
    global _database_instance
    if _database_instance is None:
        _database_instance = Database()
    return _database_instance


def get_session_factory():
    """Получить фабрику сессий."""
    db = get_database()
    return db.SessionLocal
