@echo off
REM Скрипт для одновременного запуска трекера, бота и веб-интерфейса (Windows)

echo 🚀 Запуск HH Tracker...

REM Проверка .env
if not exist ".env" (
    echo ⚠️ Файл .env не найден! Копирую из .env.example...
    copy .env.example .env
    echo ❗ Отредактируйте .env и запустите скрипт снова
    pause
    exit /b 1
)

REM Создание директорий
if not exist "data" mkdir data
if not exist "logs" mkdir logs

REM Запуск в фоне
echo 📡 Запуск трекера вакансий...
start /B python main.py
echo 🤖 Запуск Telegram бота...
start /B python bot.py
echo 🌐 Запуск веб-интерфейса...
start /B python web.py

echo.
echo ✅ Запущено:
echo    - Трекер вакансий
echo    - Telegram бот
echo    - Веб-интерфейс: http://localhost:8000
echo.
echo Для остановки закройте окна терминала
pause
