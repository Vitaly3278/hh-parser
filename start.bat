@echo off
REM Скрипт для запуска трекера вакансий (Windows)

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

echo.
echo ✅ Запущен трекер вакансий
echo.
echo Для остановки закройте окна терминала
pause
