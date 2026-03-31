#!/usr/bin/env python3
"""Unit-тесты для parser модуля."""

import unittest
from unittest.mock import patch, MagicMock

from modules.parser.hh_client import HHClient


class TestHHParser(unittest.TestCase):
    """Тесты для HHClient."""

    def setUp(self):
        """Настройка перед каждым тестом."""
        self.parser = HHClient(area=None)

    def test_init(self):
        """Тест инициализации."""
        parser = HHClient(area="1", period=7)
        self.assertEqual(parser.area, "1")
        self.assertEqual(parser.period, 7)

    def test_filter_by_exclude_words_empty(self):
        """Тест фильтрации с пустым списком исключений."""
        vacancies = [
            {"name": "Python Developer", "id": "1"},
            {"name": "Java Developer", "id": "2"},
        ]
        result = self.parser.filter_by_exclude_words(vacancies, [])
        self.assertEqual(len(result), 2)

    def test_filter_by_exclude_words(self):
        """Тест фильтрации по исключающим словам."""
        vacancies = [
            {"name": "Python Developer", "id": "1", "description": ""},
            {"name": "Junior Python Developer", "id": "2", "description": ""},
            {"name": "Senior Developer", "id": "3", "description": ""},
        ]
        result = self.parser.filter_by_exclude_words(vacancies, ["junior", "trainee"])
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["id"], "1")
        self.assertEqual(result[1]["id"], "3")

    def test_filter_by_exclude_words_in_description(self):
        """Тест фильтрации по описанию."""
        vacancies = [
            {"name": "Developer", "id": "1", "description": "Стажировка для начинающих"},
            {"name": "Developer", "id": "2", "description": "Опыт работы от 3 лет"},
        ]
        result = self.parser.filter_by_exclude_words(vacancies, ["стажировка"])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "2")

    def test_format_vacancy(self):
        """Тест форматирования вакансии."""
        vacancy = {
            "name": "Python Developer",
            "employer": {"name": "TechCorp"},
            "salary": {"from": 100000, "to": 200000, "currency": "RUR"},
            "area": {"name": "Москва"},
            "alternate_url": "https://hh.ru/vacancy/123",
            "published_at": "2024-01-01T10:00:00+0300",
        }
        result = self.parser.format_vacancy(vacancy)
        self.assertIn("Python Developer", result)
        self.assertIn("TechCorp", result)
        self.assertIn("100000 - 200000 RUR", result)
        self.assertIn("Москва", result)

    @patch('hh_parser.requests.get')
    def test_search_vacancies(self, mock_get):
        """Тест поиска вакансий (мокированный)."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"items": [], "found": 0}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.parser.search_vacancies("Python")
        self.assertEqual(result["found"], 0)
        self.assertEqual(result["items"], [])


class TestDatabase(unittest.TestCase):
    """Тесты для VacancyDatabase."""

    def setUp(self):
        """Настройка перед каждым тестом."""
        import sys
        sys.path.insert(0, '..')
        from database import VacancyDatabase
        self.db = VacancyDatabase(":memory:")

    def test_add_and_exists(self):
        """Тест добавления и проверки существования."""
        vacancy = {
            "id": "test_123",
            "name": "Test Vacancy",
            "employer": {"name": "Test Corp"},
            "salary": {"from": 100000},
            "area": {"name": "Москва"},
            "url": "https://example.com",
            "published_at": "2024-01-01",
        }
        
        # Добавляем
        result = self.db.add_vacancy(vacancy)
        self.assertTrue(result)
        
        # Проверяем существование
        self.assertTrue(self.db.vacancy_exists("test_123"))
        self.assertFalse(self.db.vacancy_exists("nonexistent"))

    def test_duplicate_add(self):
        """Тест добавления дубликата."""
        vacancy = {
            "id": "dup_123",
            "name": "Duplicate Test",
            "employer": {"name": "Test"},
            "salary": {},
            "area": {},
            "url": "https://example.com",
            "published_at": "2024-01-01",
        }
        
        self.db.add_vacancy(vacancy)
        result = self.db.add_vacancy(vacancy)
        self.assertFalse(result)

    def test_get_stats_empty(self):
        """Тест статистики на пустой базе."""
        stats = self.db.get_stats()
        self.assertEqual(stats["total"], 0)
        self.assertEqual(stats["today"], 0)

    def test_get_stats_with_data(self):
        """Тест статистики с данными."""
        vacancy = {
            "id": "stat_123",
            "name": "Stat Test",
            "employer": {"name": "Stat Corp"},
            "salary": {"from": 150000},
            "area": {"name": "Москва"},
            "url": "https://example.com",
            "published_at": "2024-01-01",
        }
        self.db.add_vacancy(vacancy)
        
        stats = self.db.get_stats()
        self.assertEqual(stats["total"], 1)
        self.assertEqual(stats["avg_salary"], 150000)


if __name__ == "__main__":
    unittest.main()
