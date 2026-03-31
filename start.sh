#!/bin/bash
# Скрипт для одновременного запуска трекера, бота и веб-интерфейса

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
    echo "📦 Установка зависимостей..."
    source venv/bin/activate
    pip install --quiet --upgrade pip
    pip install --quiet -r requirements.txt
fi

# Активация
source venv/bin/activate

# Проверка .env
if [ ! -f ".env" ]; then
    cp .env.example .env 2>/dev/null
    echo "❗ Создан .env файл. Заполните TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID"
    exit 1
fi

# Создание директорий
mkdir -p data logs 2>/dev/null

# Запуск
echo "🚀 Запуск HH Tracker (трекер + бот + веб)..."
python main.py >/dev/null 2>&1 &
MAIN_PID=$!

echo ""
echo "✅ Готово!"
echo "   Запущено:"
echo "   - Трекер вакансий"
echo "   - Telegram бот"
echo "   - Веб-интерфейс: http://localhost:8000"
echo "   PID: $MAIN_PID"
echo ""
echo "Остановка: Ctrl+C или kill $MAIN_PID"

trap "kill $MAIN_PID 2>/dev/null; exit" INT TERM EXIT
wait
