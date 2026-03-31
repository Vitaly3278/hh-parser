"""Unit тесты для модуля bot.py (RateLimiter)."""

import pytest
import time
from modules.bot.rate_limiter import RateLimiter


class TestRateLimiter:
    """Тесты для RateLimiter."""

    def test_is_allowed_first_request(self):
        """Тест первого запроса."""
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        assert limiter.is_allowed(123) is True

    def test_is_allowed_within_limit(self):
        """Тест запросов в пределах лимита."""
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        
        assert limiter.is_allowed(123) is True
        assert limiter.is_allowed(123) is True
        assert limiter.is_allowed(123) is True

    def test_is_allowed_exceeds_limit(self):
        """Тест превышения лимита."""
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        
        # Делаем 3 запроса
        limiter.is_allowed(123)
        limiter.is_allowed(123)
        limiter.is_allowed(123)
        
        # 4-й должен быть заблокирован
        assert limiter.is_allowed(123) is False

    def test_is_allowed_different_users(self):
        """Тест разных пользователей."""
        limiter = RateLimiter(max_requests=1, window_seconds=60)
        
        assert limiter.is_allowed(123) is True
        assert limiter.is_allowed(456) is True
        assert limiter.is_allowed(123) is False  # Превышен лимит для 123

    def test_get_wait_time_no_requests(self):
        """Тест времени ожидания без запросов."""
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        assert limiter.get_wait_time(123) == 0

    def test_get_wait_time_after_limit(self):
        """Тест времени ожидания после превышения лимита."""
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        
        limiter.is_allowed(123)
        limiter.is_allowed(123)
        limiter.is_allowed(123)  # Превышение
        
        wait_time = limiter.get_wait_time(123)
        assert wait_time > 0
        assert wait_time <= 60

    def test_window_expiration(self):
        """Тест истечения временного окна."""
        # Используем очень короткое окно для теста
        limiter = RateLimiter(max_requests=2, window_seconds=1)
        
        limiter.is_allowed(123)
        limiter.is_allowed(123)
        assert limiter.is_allowed(123) is False
        
        # Ждём истечения окна
        time.sleep(1.1)
        
        assert limiter.is_allowed(123) is True
