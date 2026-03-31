# HH Tracker — Трекер вакансий hh.ru

[![CI/CD](https://github.com/Vitaly3278/hh-parser/actions/workflows/ci.yml/badge.svg)](https://github.com/Vitaly3278/hh-parser/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Приложение для автоматического отслеживания новых вакансий на hh.ru с отправкой уведомлений в **Telegram** и **Email**.

## 🚀 Возможности

- ✅ Мониторинг вакансий hh.ru по заданным параметрам
- ✅ Уведомления в Telegram и Email
- ✅ Фильтрация по исключающим словам (например, "стажировка")
- ✅ База данных SQLite с миграциями (Alembic)
- ✅ Статистика и отчёты
- ✅ Веб-интерфейс для просмотра вакансий
- ✅ Telegram бот для управления
- ✅ Поддержка Docker и docker-compose
- ✅ Режим для cron (`--once`)
- ✅ Логирование в файл
- ✅ CI/CD с GitHub Actions
- ✅ Асинхронная архитектура (asyncio + aiohttp)
- ✅ Rate limiting для бота
- ✅ Валидация авторизованных пользователей
- ✅ Unit-тесты

## 📁 Структура проекта

```
├── main.py              # Главный скрипт (асинхронный)
├── bot.py               # Telegram бот (python-telegram-bot)
├── hh_parser.py         # Парсер hh.ru API (асинхронный)
├── telegram_bot.py      # Telegram уведомления (aiohttp)
├── email_bot.py         # Email уведомления
├── database.py          # База данных SQLite (SQLAlchemy)
├── web.py               # Веб-интерфейс (FastAPI)
├── config.py            # Конфигурация
├── .env                 # Переменные окружения (не в git!)
├── .env.example         # Шаблон конфигурации
├── alembic.ini          # Alembic конфигурация
├── alembic/             # Миграции БД
├── Dockerfile           # Docker образ
├── docker-compose.yml   # Docker Compose
├── requirements.txt     # Зависимости
├── pytest.ini           # Настройка тестов
├── tests/               # Unit-тесты
└── README.md            # Документация
```

## ⚙️ Установка

### 1. Клонирование репозитория

```bash
git clone https://github.com/Vitaly3278/hh-parser.git
cd hh-parser
```

### 2. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 3. Настройка конфигурации

Скопируйте `.env.example` в `.env` и заполните обязательные поля:

```bash
cp .env.example .env
```

**Обязательные параметры:**
```ini
# Telegram (минимум один нотификатор)
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
ALLOWED_CHAT_IDS=123456789,987654321  # Список разрешённых chat_id (опционально)
```

**Опционально — Email:**
```ini
EMAIL_ENABLED=true
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_RECIPIENT=recipient@example.com
```

**Параметры поиска:**
```ini
HH_SEARCH_TEXT=Python разработчик
HH_AREA=           # 1=Москва, 2=СПб, 104=Россия, пусто=все
HH_SALARY_FROM=    # Минимальная зарплата
HH_EMPLOYMENT=     # full,part,project,internship
HH_EXPERIENCE=     # noExperience,between1And3,between3And6,moreThan6
HH_EXCLUDE_WORDS=стажировка,test,junior  # Исключить по словам
CHECK_INTERVAL=300  # Интервал проверки (секунды)
```

### 4. Миграции базы данных (опционально)

```bash
# Применить миграции
alembic upgrade head

# Откатить миграцию
alembic downgrade -1

# Создать новую миграцию
alembic revision --autogenerate -m "Description"
```

## 🚀 Запуск

### ⚡ Быстрый запуск (всё сразу)

**Linux/Mac:**
```bash
./start.sh
```

**Windows:**
```bash
start.bat
```

Это запустит:
- 📡 Трекер вакансий (мониторинг hh.ru)
- 🤖 Telegram бот
- 🌐 Веб-интерфейс (http://localhost:8000)

---

### Обычный режим (трекер + бот)

```bash
python main.py
```

### Запуск только бота

```bash
python main.py --bot-only
```

### Запуск только трекера (без бота)

```bash
python main.py --tracker-only
```

### Однократная проверка (для cron)

```bash
python main.py --once
```

### Показать статистику

```bash
python main.py --stats
```

### Свой уровень логирования

```bash
python main.py --log-level DEBUG
```

### Запуск Telegram бота (отдельно)

```bash
python bot.py
```

## 🐳 Docker

### Запуск через docker-compose

```bash
docker-compose up -d
```

Это запустит:
- Трекер вакансий
- Веб-интерфейс на http://localhost:8000

Просмотр логов:
```bash
docker-compose logs -f
```

Остановка:
```bash
docker-compose down
```

## 🌐 Веб-интерфейс

Запустите веб-сервер:

```bash
python web.py
```

Откройте http://localhost:8000

**Возможности:**
- 📊 Просмотр статистики вакансий
- 📋 Список всех вакансий с фильтрами
- 🔗 Прямые ссылки на hh.ru
- 📱 Адаптивный дизайн
- 🔄 Автообновление каждые 5 минут

**API endpoints:**
- `GET /` — Главная страница с вакансиями
- `GET /api/stats` — Статистика
- `GET /api/vacancies` — Список вакансий
- `GET /api/vacancies/{id}` — Вакансия по ID
- `DELETE /api/vacancies/clear?days=30` — Очистить старые
- `GET /docs` — Swagger документация API

## 📊 Параметры поиска

| Параметр | Описание | Пример |
|----------|----------|--------|
| `HH_SEARCH_TEXT` | Поисковый запрос | `Python разработчик` |
| `HH_AREA` | Регион | `1`=Москва, `2`=СПб, `104`=Россия |
| `HH_SALARY_FROM` | Мин. зарплата | `100000` |
| `HH_EMPLOYMENT` | Тип занятости | `full,part` |
| `HH_EXPERIENCE` | Опыт работы | `between1And3,between3And6` |
| `HH_EXCLUDE_WORDS` | Исключить слова | `стажировка,junior` |
| `CHECK_INTERVAL` | Интервал (сек) | `300` |

### Типы занятости

- `full` — полная занятость
- `part` — частичная
- `project` — проектная работа
- `internship` — стажировка

### Опыт работы

- `noExperience` — без опыта
- `between1And3` — от 1 до 3 лет
- `between3And6` — от 3 до 6 лет
- `moreThan6` — более 6 лет

## 🧪 Тесты

```bash
# Запуск всех тестов
pytest tests/ -v

# Запуск с покрытием
pytest tests/ -v --cov=. --cov-report=html

# Запуск конкретного теста
pytest tests/test_database.py -v
```

## 🗄 Миграции базы данных

Проект использует Alembic для управления миграциями:

```bash
# Применить все миграции
alembic upgrade head

# Откатить последнюю миграцию
alembic downgrade -1

# Откатить к конкретной ревизии
alembic downgrade <revision_id>

# Создать новую миграцию (автоматически)
alembic revision --autogenerate -m "Описание изменений"

# Создать пустую миграцию
alembic revision -m "Описание"

# Показать текущую ревизию
alembic current

# Показать историю миграций
alembic history
```

## 📝 Пример .env

```ini
# Telegram
TELEGRAM_BOT_TOKEN=1234567890:AABBccDDeeFFggHHiiJJkkLLmmNNooP
TELEGRAM_CHAT_ID=987654321

# HH.ru
HH_SEARCH_TEXT=Python разработчик
HH_AREA=1
HH_SALARY_FROM=150000
HH_EXCLUDE_WORDS=стажировка,test

# Интервал
CHECK_INTERVAL=300
```

## 🔧 Cron пример

```bash
# Запуск каждые 5 минут
*/5 * * * * cd /path/to/hh-parser && /usr/bin/python3 main.py --once >> hh_tracker.log 2>&1
```

## 📄 Лицензия

MIT License

## 🤝 Contributing

1. Fork репозиторий
2. Создайте feature branch (`git checkout -b feature/amazing-feature`)
3. Commit изменений (`git commit -m 'Add amazing feature'`)
4. Push в branch (`git push origin feature/amazing-feature`)
5. Откройте Pull Request
