import sys
import os

# Принудительная установка UTF-8 для вывода в консоль Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient
from main import app
from app.services.cost_tracker import CostTrackerService

client = TestClient(app)

def test_cost_tracker_service():
    print("\n--- [ТЕСТ 1] Прямая проверка CostTrackerService ---")
    mock_script = {
        "title": "Тестовый ролик",
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
                        "narration_text": "Привет всем зрителям нашего замечательного канала!", # 51 char
                        "visual_prompt": "Красивый вид на заснеженные горы",
                        "audio_path": None,
                        "image_path": None,
                        "video_path": None
                    },
                    {
                        "frame_id": "scene_1_frame_2",
                        "scene_number": 1,
                        "frame_number": 2,
                        "narration_text": "Сегодня мы поговорим об искусственном интеллекте.", # 52 char
                        "visual_prompt": "Робот за компьютером пишет код",
                        "audio_path": None,
                        "image_path": None,
                        "video_path": None
                    }
                ]
            }
        ]
    }

    res = CostTrackerService.calculate_script_cost(mock_script)
    print(f"Результат расчета: {res}")
    assert res["total_chars"] == 99
    assert res["total_images"] == 2
    assert res["total_videos"] == 2
    assert res["tts_cost"] > 0
    assert res["image_cost"] == 0.02
    assert res["video_cost"] == 0.10
    assert res["total_estimated_cost"] == round(res["tts_cost"] + res["image_cost"] + res["video_cost"], 4)
    print("✅ Тест CostTrackerService пройден успешно!")

def test_cost_calculate_api():
    print("\n--- [ТЕСТ 2] Проверка REST API POST /api/cost/calculate ---")
    mock_script = {
        "title": "Тест API Сметы",
        "scenes": [
            {
                "scene_id": "scene_1",
                "scene_number": 1,
                "title": "Интро",
                "frames": [
                    {
                        "frame_id": "scene_1_frame_1",
                        "scene_number": 1,
                        "frame_number": 1,
                        "narration_text": "Проверка API расчета сметы.",
                        "visual_prompt": "Футуристический город в неоновом свете"
                    }
                ]
            }
        ]
    }

    response = client.post("/api/cost/calculate", json=mock_script)
    assert response.status_code == 200, f"Ошибка API: {response.text}"
    data = response.json()
    print(f"Ответ API /api/cost/calculate: {data}")
    assert "total_estimated_cost" in data
    assert "actual_cost" in data
    assert "cache_savings" in data
    print("✅ REST API /api/cost/calculate работает корректно!")

if __name__ == "__main__":
    test_cost_tracker_service()
    test_cost_calculate_api()
