"""Исключения приложения."""


class AppError(Exception):
    """Базовое исключение приложения."""
    pass


class ConfigError(AppError):
    """Ошибка конфигурации."""
    pass


class DatabaseError(AppError):
    """Ошибка базы данных."""
    pass


class ParserError(AppError):
    """Ошибка парсера."""
    pass


class NotificationError(AppError):
    """Ошибка отправки уведомления."""
    pass


class VacancyNotFoundError(DatabaseError):
    """Вакансия не найдена."""
    pass


class UnauthorizedError(AppError):
    """Пользователь не авторизован."""
    pass


class RateLimitError(AppError):
    """Превышен лимит запросов."""
    def __init__(self, wait_time: float):
        self.wait_time = wait_time
        super().__init__(f"Rate limit exceeded. Wait {wait_time:.0f} seconds")
