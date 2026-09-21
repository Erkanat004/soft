import sys
import os
from fastapi.testclient import TestClient

sys.path.append(os.path.dirname(__file__))

from main import app
from app.services.tts import TTSService

client = TestClient(app)

def test_revoice_functionality():
    print("=== ТЕСТ 1: Первичная озвучка ===")
    text = "Тестовая озвучка сцены номер один"
    res1 = client.post("/api/tts/generate", json={
        "text": text,
        "frame_id": "frame_test_101",
        "force": False
    }).json()
    print("Результат 1:", res1)
    
    print("\n=== ТЕСТ 2: Озвучка из кэша (force=False) ===")
    res2 = client.post("/api/tts/generate", json={
        "text": text,
        "frame_id": "frame_test_101",
        "force": False
    }).json()
    print("Результат 2:", res2)
    assert res2["cached"] is True, "Второй запуск должен быть из кэша"

    print("\n=== ТЕСТ 3: Принудительное переозвучивание (force=True) ===")
    res3 = client.post("/api/tts/generate", json={
        "text": text,
        "frame_id": "frame_test_101",
        "force": True
    }).json()
    print("Результат 3:", res3)
    assert res3["cached"] is False, "При force=True кэш должен быть сброшен!"

    print("\n=== ТЕСТ 4: Пакетное переозвучивание сцены (/api/batch/tts с force=True) ===")
    batch_res = client.post("/api/batch/tts", json={
        "items": [
            {"frame_id": "f1", "text": "Кадр один из сцены"},
            {"frame_id": "f2", "text": "Кадр два из сцены"}
        ],
        "voice": "ru-RU-DmitryNeural",
        "force": True
    }).json()
    print("Результат пакетной переозвучки:", batch_res)
    assert len(batch_res) == 2
    for item in batch_res:
        assert item["cached"] is False, f"Элемент {item['frame_id']} должен быть переозвучен заново!"

    print("\n[SUCCESS] Все тесты кнопки переозвучивания сцены успешно пройдены!")

if __name__ == "__main__":
    test_revoice_functionality()
