#!/bin/bash
# Скрипт для одновременного запуска трекера и веб-интерфейса

echo "🚀 Запуск HH Tracker..."

# Проверка зависимостей
if ! python3 -c "import fastapi, uvicorn, requests, dotenv" 2>/dev/null; then
    echo "⚠️ Установка зависимостей..."
    pip3 install -r requirements.txt
fi

# Проверка .env
if [ ! -f ".env" ]; then
    echo "⚠️ Файл .env не найден! Копирую из .env.example..."
    cp .env.example .env
    echo "❗ Отредактируйте .env и запустите скрипт снова"
    exit 1
fi

# Создание директорий
mkdir -p data logs

# Запуск в фоне
echo "📡 Запуск трекера вакансий..."
python3 main.py &
TRACKER_PID=$!

echo "🌐 Запуск веб-интерфейса..."
python3 web.py &
WEB_PID=$!

echo ""
echo "✅ Запущено:"
echo "   - Трекер вакансий (PID: $TRACKER_PID)"
echo "   - Веб-интерфейс: http://localhost:8000 (PID: $WEB_PID)"
echo ""
echo "Для остановки нажмите Ctrl+C или выполните:"
echo "   kill $TRACKER_PID $WEB_PID"

# Обработка Ctrl+C
trap "kill $TRACKER_PID $WEB_PID 2>/dev/null; exit" INT TERM EXIT

# Ожидание
wait
