# HH Tracker — Трекер вакансий hh.ru

[![CI/CD](https://github.com/Vitaly3278/hh-parser/actions/workflows/ci.yml/badge.svg)](https://github.com/Vitaly3278/hh-parser/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Приложение для автоматического отслеживания новых вакансий на hh.ru с отправкой уведомлений в **Telegram**, **Email** и **Slack**.

## 🚀 Возможности

- ✅ Мониторинг вакансий hh.ru по заданным параметрам
- ✅ Уведомления в Telegram, Email и Slack
- ✅ Фильтрация по исключающим словам (например, "стажировка")
- ✅ База данных SQLite с историей вакансий
- ✅ Статистика и отчёты
- ✅ Веб-интерфейс для просмотра вакансий
- ✅ Поддержка Docker и docker-compose
- ✅ Режим для cron (`--once`)
- ✅ Логирование в файл
- ✅ CI/CD с GitHub Actions

## 📁 Структура проекта

```
├── main.py              # Главный скрипт
├── hh_parser.py         # Парсер hh.ru API
├── telegram_bot.py      # Telegram бот
├── email_bot.py         # Email уведомления
├── slack_bot.py         # Slack уведомления
├── database.py          # База данных SQLite
├── web.py               # Веб-интерфейс (FastAPI)
├── config.py            # Конфигурация
├── .env                 # Переменные окружения (не в git!)
├── .env.example         # Шаблон конфигурации
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

**Опционально — Slack:**
```ini
SLACK_ENABLED=true
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
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

## 🚀 Запуск

### Обычный режим

```bash
python main.py
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

## 🐳 Docker

### Запуск через docker-compose

```bash
docker-compose up -d
```

### Запуск только трекера

```bash
docker-compose up -d hh-tracker
```

### Запуск с веб-интерфейсом

```bash
docker-compose --profile web up -d
```

Веб-интерфейс будет доступен по адресу: http://localhost:8001

## 🌐 Веб-интерфейс

Запустите веб-сервер:

```bash
python web.py
```

Откройте http://localhost:8000

**API endpoints:**
- `GET /` — Главная страница с вакансиями
- `GET /api/stats` — Статистика
- `GET /api/vacancies` — Список вакансий
- `GET /api/vacancies/{id}` — Вакансия по ID
- `DELETE /api/vacancies/clear?days=30` — Очистить старые

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
pytest tests/ -v
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
