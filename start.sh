#!/bin/bash
# Скрипт для одновременного запуска трекера и веб-интерфейса

echo "🚀 Запуск HH Tracker..."

# Убийство старых процессов
echo "🧹 Очистка старых процессов..."
pkill -f "python.*main.py" 2>/dev/null
pkill -f "python.*bot.py" 2>/dev/null
pkill -f "python.*web.py" 2>/dev/null
sleep 1

# Создание виртуального окружения
if [ ! -d "venv" ]; then
    echo "📦 Создание venv..."
    python3 -m venv venv
fi

# Активация
source venv/bin/activate

# Установка зависимостей
echo "📦 Установка зависимостей..."
pip install --quiet --upgrade pip 2>/dev/null
pip install --quiet -r requirements.txt 2>/dev/null

# Проверка .env
if [ ! -f ".env" ]; then
    cp .env.example .env 2>/dev/null
    echo "❗ Создан .env файл. Заполните TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID"
    exit 1
fi

# Создание директорий
mkdir -p data logs 2>/dev/null

# Запуск
echo "📡 Запуск трекера..."
python main.py >/dev/null 2>&1 &
TRACKER_PID=$!

echo "🤖 Запуск Telegram бота..."
python bot.py >/dev/null 2>&1 &
BOT_PID=$!

echo "🌐 Запуск веб-интерфейса..."
python web.py >/dev/null 2>&1 &
WEB_PID=$!

echo ""
echo "✅ Готово!"
echo "   Трекер: PID $TRACKER_PID"
echo "   Бот: PID $BOT_PID"
echo "   Веб: http://localhost:8000 (PID $WEB_PID)"
echo ""
echo "Остановка: Ctrl+C"

trap "kill $TRACKER_PID $BOT_PID $WEB_PID 2>/dev/null; exit" INT TERM EXIT
wait
