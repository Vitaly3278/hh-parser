"""Unit тесты для модуля parser."""

import pytest
import aiohttp
from unittest.mock import AsyncMock, patch, MagicMock

from parser.hh_client import HHClient


@pytest.fixture
async def http_session():
    """Фикстура для aiohttp сессии."""
    session = aiohttp.ClientSession()
    yield session
    await session.close()


@pytest.fixture
def parser(http_session):
    """Фикстура для HHClient."""
    return HHClient(area="1", session=http_session)


@pytest.fixture
def sample_vacancy():
    """Фикстура с тестовой вакансией."""
    return {
        "id": "test_123",
        "name": "Python Developer",
        "employer": {"name": "Test Company"},
        "salary": {"from": 100000, "to": 150000, "currency": "RUR"},
        "area": {"name": "Москва"},
        "alternate_url": "https://hh.ru/vacancy/123",
        "published_at": "2026-04-01T10:00:00Z",
        "description": "Мы ищем Python разработчика",
    }


class TestHHParser:
    """Тесты для HHParser."""

    @pytest.mark.asyncio
    async def test_search_vacancies_success(self, parser):
        """Тест успешного поиска вакансий."""
        mock_response = {
            "items": [{"id": "1", "name": "Vacancy 1"}],
            "found": 1
        }
        
        with patch.object(parser, '_get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_response_obj = AsyncMock()
            mock_response_obj.json.return_value = mock_response
            mock_response_obj.raise_for_status.return_value = None
            mock_session.get.return_value.__aenter__.return_value = mock_response_obj
            mock_get_session.return_value = mock_session
            
            result = await parser.search_vacancies("Python")
            
            assert result["found"] == 1
            assert len(result["items"]) == 1

    @pytest.mark.asyncio
    async def test_search_vacancies_error(self, parser):
        """Тест обработки ошибки при поиске."""
        with patch.object(parser, '_get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_session.get.side_effect = aiohttp.ClientError("Connection error")
            mock_get_session.return_value = mock_session
            
            result = await parser.search_vacancies("Python")
            
            assert result == {"items": [], "found": 0}

    @pytest.mark.asyncio
    async def test_get_vacancy_details(self, parser):
        """Тест получения деталей вакансии."""
        mock_details = {"id": "123", "name": "Detailed Vacancy"}
        
        with patch.object(parser, '_get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_response_obj = AsyncMock()
            mock_response_obj.json.return_value = mock_details
            mock_response_obj.raise_for_status.return_value = None
            mock_session.get.return_value.__aenter__.return_value = mock_response_obj
            mock_get_session.return_value = mock_session
            
            result = await parser.get_vacancy_details("123")
            
            assert result["name"] == "Detailed Vacancy"

    def test_filter_by_date(self, parser, sample_vacancy):
        """Тест фильтрации по дате."""
        vacancies = [sample_vacancy]
        filtered = parser.filter_by_date(vacancies, hours=24)
        assert len(filtered) == 1

    def test_filter_by_date_old(self, parser):
        """Тест фильтрации старых вакансий."""
        old_vacancy = {
            "id": "old_123",
            "name": "Old Vacancy",
            "published_at": "2020-01-01T10:00:00Z",
        }
        vacancies = [old_vacancy]
        filtered = parser.filter_by_date(vacancies, hours=24)
        assert len(filtered) == 0

    def test_filter_by_exclude_words(self, parser, sample_vacancy):
        """Тест фильтрации по исключающим словам."""
        vacancies = [sample_vacancy]
        exclude_words = ["стажировка", "test"]
        filtered = parser.filter_by_exclude_words(vacancies, exclude_words)
        assert len(filtered) == 1

    def test_filter_by_exclude_words_match(self, parser):
        """Тест фильтрации с совпадением исключающих слов."""
        vacancy = {
            "id": "test_123",
            "name": "Стажировка Python Developer",
            "description": "Учебный проект",
        }
        vacancies = [vacancy]
        exclude_words = ["стажировка"]
        filtered = parser.filter_by_exclude_words(vacancies, exclude_words)
        assert len(filtered) == 0

    def test_filter_by_exclude_words_empty(self, parser, sample_vacancy):
        """Тест фильтрации с пустым списком исключений."""
        vacancies = [sample_vacancy]
        filtered = parser.filter_by_exclude_words(vacancies, [])
        assert len(filtered) == 1

    def test_format_vacancy(self, parser, sample_vacancy):
        """Тест форматирования вакансии."""
        formatted = parser.format_vacancy(sample_vacancy)
        
        assert "Python Developer" in formatted
        assert "Test Company" in formatted
        assert "100000" in formatted
        assert "Москва" in formatted

    def test_format_vacancy_no_salary(self, parser):
        """Тест форматирования вакансии без зарплаты."""
        vacancy = {
            "id": "test_123",
            "name": "Vacancy",
            "employer": {"name": "Company"},
            "salary": None,
            "area": {"name": "Москва"},
            "alternate_url": "https://hh.ru/vacancy/123",
            "published_at": "2026-04-01T10:00:00Z",
        }
        formatted = parser.format_vacancy(vacancy)
        assert "Не указана" in formatted
