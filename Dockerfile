FROM python:3.11-slim

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY . .

# Создание директории для логов
RUN mkdir -p /app/logs

# Переменные окружения
ENV PYTHONUNBUFFERED=1
ENV DB_PATH=/app/data/vacancies.db
ENV LOG_FILE=/app/logs/hh_tracker.log

# Том для данных
VOLUME ["/app/data", "/app/logs"]

# Запуск приложения
CMD ["python", "main.py"]
