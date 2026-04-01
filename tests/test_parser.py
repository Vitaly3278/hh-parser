#!/usr/bin/env python3
"""Unit-тесты для hh_parser.py."""

import unittest
from unittest.mock import patch, MagicMock

from parser.hh_client import HHClient


class TestHHParser(unittest.TestCase):
    """Тесты для HHParser."""

    def setUp(self):
        """Настройка перед каждым тестом."""
        self.parser = HHClient(area=None)

    def test_init(self):
        """Тест инициализации."""
        parser = HHClient(area="1")
        self.assertEqual(parser.area, "1")

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

    
if __name__ == "__main__":
    unittest.main()
