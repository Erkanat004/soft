import sys
from fastapi.testclient import TestClient
from main import app
from app.services.state import StateManager

sys.stdout.reconfigure(encoding='utf-8')

client = TestClient(app)

def test_state_and_fallback():
    print("=== ТЕСТ 1: Сохранение и загрузка состояния проекта ===")
    sample_state = {
        "title": "Тестовый Космический Проект",
        "total_scenes": 1,
        "total_frames": 2,
        "scenes": [
            {
                "scene_id": "scene_1",
                "scene_number": 1,
                "title": "Сцена 1",
                "frames": [
                    {
                        "frame_id": "scene_1_frame_1",
                        "scene_number": 1,
                        "frame_number": 1,
                        "narration_text": "Привет мир!",
                        "visual_prompt": "Космос",
                        "duration": 3.0
                    }
                ]
            }
        ]
    }
    
    saved_path = StateManager.save_state(sample_state)
    print("Сохранено в:", saved_path)
    
    loaded_state = StateManager.load_state()
    print("Загружен заголовок:", loaded_state.get("title"))
    assert loaded_state["title"] == "Тестовый Космический Проект"

    print("\n=== ТЕСТ 2: Отработка Паттерна Fallback при сбое первичного API ===")
    def failing_primary():
        raise RuntimeError("OpenAI / Replicate Rate Limit Exceeded (HTTP 429)")

    def working_fallback():
        return {"status": "success", "provider": "Local Offline Backup Engine"}

    res = StateManager.execute_with_fallback(failing_primary, working_fallback, "Failing Primary API")
    print("Результат работы Fallback:", res)
    assert res["provider"] == "Local Offline Backup Engine"

    print("\n=== ТЕСТ 3: REST API (GET /api/project/state) ===")
    api_res = client.get("/api/project/state")
    assert api_res.status_code == 200
    data = api_res.json()
    print("Состояние через REST API:", data["title"])
    assert data["title"] == "Тестовый Космический Проект"

    print("\n[SUCCESS] Все тесты модуля обработки ошибок, Fallback и восстановления пройдены!")

if __name__ == "__main__":
    test_state_and_fallback()
