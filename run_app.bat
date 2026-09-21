@echo off
chcp 65001 > nul
echo ========================================================
echo   🎬 YouTube Video Generator — Запуск приложения
echo ========================================================
echo [1/2] Запуск бэкенда FastAPI в фоновом режиме...
start /b "" "%~dp0backend\venv\Scripts\python.exe" "%~dp0backend\main.py"

echo [2/2] Ожидание инициализации REST API и старт Electron GUI...
timeout /t 3 /nobreak > nul

cd /d "%~dp0frontend"
npm start

echo ========================================================
echo   Приложение завершено.
echo ========================================================
