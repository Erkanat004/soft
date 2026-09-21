import sys
import os
import subprocess

# Принудительная установка UTF-8 для вывода в консоль Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def test_launch_scripts_and_build():
    print("\n--- [ТЕСТ 1] Проверка наличия запускных скриптов ---")
    run_bat = os.path.join(ROOT_DIR, "run_app.bat")
    build_py = os.path.join(ROOT_DIR, "build_portable.py")
    main_js = os.path.join(ROOT_DIR, "frontend", "main.js")

    assert os.path.exists(run_bat), "run_app.bat отсутствует!"
    assert os.path.exists(build_py), "build_portable.py отсутствует!"
    assert os.path.exists(main_js), "frontend/main.js отсутствует!"
    print("✅ Все ключевые скрипты сборки и запуска присутствуют!")

def test_execute_build_portable():
    print("\n--- [ТЕСТ 2] Запуск сборщика build_portable.py ---")
    python_exec = sys.executable
    build_py = os.path.join(ROOT_DIR, "build_portable.py")

    res = subprocess.run([python_exec, build_py], capture_output=True, text=True, encoding="utf-8")
    print(res.stdout)
    assert res.returncode == 0, f"Ошибка выполнения сборщика: {res.stderr}"

    dist_dir = os.path.join(ROOT_DIR, "dist", "YouTubeVideoGenerator-Portable")
    assert os.path.exists(dist_dir), "Папка дистрибутива не создана!"
    assert os.path.exists(os.path.join(dist_dir, "run_app.bat")), "run_app.bat в дистрибутиве отсутствует!"
    assert os.path.exists(os.path.join(dist_dir, "README_PORTABLE.txt")), "README_PORTABLE.txt отсутствует!"
    print("✅ Тест сборки портативного дистрибутива пройден успешно!")

if __name__ == "__main__":
    test_launch_scripts_and_build()
    test_execute_build_portable()
