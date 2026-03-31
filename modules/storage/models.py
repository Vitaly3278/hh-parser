"""Модель вакансии."""

from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class Vacancy:
    """
    Сущность вакансии.

    Атрибуты:
        id: Уникальный идентификатор вакансии
        name: Название вакансии
        employer: Название работодателя
        salary_from: Минимальная зарплата
        salary_to: Максимальная зарплата
        currency: Валюта зарплаты
        area: Регион/город
        url: Ссылка на вакансию
        published_at: Дата публикации
        created_at: Дата добавления в базу
    """
    id: str
    name: str
    employer: Optional[str] = None
    salary_from: Optional[int] = None
    salary_to: Optional[int] = None
    currency: str = "RUR"
    area: Optional[str] = None
    url: Optional[str] = None
    published_at: Optional[str] = None
    created_at: Optional[datetime] = field(default_factory=datetime.utcnow)

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

    @classmethod
    def from_dict(cls, data: dict) -> 'Vacancy':
        """Создание из словаря."""
        created_at = None
        if data.get('created_at'):
            if isinstance(data['created_at'], str):
                created_at = datetime.fromisoformat(data['created_at'])
            else:
                created_at = data['created_at']

        return cls(
            id=data.get('id', ''),
            name=data.get('name', ''),
            employer=data.get('employer'),
            salary_from=data.get('salary_from'),
            salary_to=data.get('salary_to'),
            currency=data.get('currency', 'RUR'),
            area=data.get('area'),
            url=data.get('url'),
            published_at=data.get('published_at'),
            created_at=created_at,
        )

    def has_salary(self) -> bool:
        """Есть ли указанная зарплата."""
        return self.salary_from is not None or self.salary_to is not None

    def formatted_salary(self) -> str:
        """Форматированная зарплата."""
        if not self.has_salary():
            return "Зарплата не указана"

        if self.salary_from and self.salary_to:
            return f"{self.salary_from} - {self.salary_to} {self.currency}"
        elif self.salary_from:
            return f"от {self.salary_from} {self.currency}"
        else:
            return f"до {self.salary_to} {self.currency}"
