import sys
import os

# UTF-8 stdout fix for Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def test_user_guide_file_exists():
    print("\n--- [ТЕСТ 1] Проверка наличия и структуры USER_GUIDE.md ---")
    user_guide_path = os.path.join(ROOT_DIR, "USER_GUIDE.md")
    assert os.path.exists(user_guide_path), "Файл USER_GUIDE.md отсутствует в корне!"

    with open(user_guide_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert len(content) > 500, "Файл USER_GUIDE.md слишком короткий!"
    assert "Сцена 1:" in content, "В справке отсутствует пример разметки сцен!"
    assert "FCPXML" in content, "В справке отсутствует упоминание FCPXML!"
    assert "Edge-TTS" in content, "В справке отсутствует упоминание Edge-TTS!"
    print("✅ Файл USER_GUIDE.md содержит всю необходимую документацию!")

if __name__ == "__main__":
    test_user_guide_file_exists()
