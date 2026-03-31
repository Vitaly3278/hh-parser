"""Модуль веб-интерфейса."""

from .routes import create_router
from .app import create_web_app


__all__ = [
    'create_router',
    'create_web_app',
]
