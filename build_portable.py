import os
import shutil
import sys

# UTF-8 stdout fix for Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(ROOT_DIR, "dist", "YouTubeVideoGenerator-Portable")

def build_portable_package():
    print("========================================================")
    print(" 📦 Сборка Портативного Дистрибутива (Windows Portable)")
    print("========================================================")

    if os.path.exists(DIST_DIR):
        print(f"Очистка предыдущей сборки: {DIST_DIR}...")
        shutil.rmtree(DIST_DIR)

    os.makedirs(DIST_DIR, exist_ok=True)

    # 1. Копирование структуры backend
    print("[1/4] Копирование модуля Backend...")
    target_backend = os.path.join(DIST_DIR, "backend")
    shutil.copytree(
        os.path.join(ROOT_DIR, "backend"), 
        target_backend,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache")
    )

    # 2. Копирование структуры frontend
    print("[2/4] Копирование модуля Frontend...")
    target_frontend = os.path.join(DIST_DIR, "frontend")
    shutil.copytree(
        os.path.join(ROOT_DIR, "frontend"),
        target_frontend,
        ignore=shutil.ignore_patterns("node_modules", ".git")
    )

    # 3. Копирование запускного батника run_app.bat
    print("[3/4] Копирование управляющих запускных скриптов...")
    shutil.copy(os.path.join(ROOT_DIR, "run_app.bat"), os.path.join(DIST_DIR, "run_app.bat"))

    # 4. Создание файла инструкции портативной версии
    readme_content = """========================================================
 🎬 YouTube Video Generator — Portable Edition
========================================================

Как запустить приложение:
1. Дважды кликните по файлу 'run_app.bat'.
2. Скрипт автоматически запустит фоновый сервер FastAPI и 
   откроет графическую десктопную оболочку.

Структура папок:
- backend/ : REST API бэкенд и локальный кэш
- frontend/ : Электрон графический интерфейс
- run_app.bat : Исполняемый файл запуска проекта
"""
    with open(os.path.join(DIST_DIR, "README_PORTABLE.txt"), "w", encoding="utf-8") as f:
        f.write(readme_content)

    print("========================================================")
    print(f" ✅ Портативный пакет успешно собран в: {DIST_DIR}")
    print("========================================================")

if __name__ == "__main__":
    build_portable_package()
