#!/bin/bash
# Скрипт для одновременного запуска трекера и веб-интерфейса

# Создание виртуального окружения
if [ ! -d "venv" ]; then
    python3 -m venv venv 2>/dev/null
fi

# Активация
source venv/bin/activate

# Установка зависимостей
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
python main.py >/dev/null 2>&1 &
TRACKER_PID=$!

python web.py >/dev/null 2>&1 &
WEB_PID=$!

echo "✅ Запущено: трекер (PID:$TRACKER_PID), веб http://localhost:8000 (PID:$WEB_PID)"

trap "kill $TRACKER_PID $WEB_PID 2>/dev/null; exit" INT TERM EXIT
wait
