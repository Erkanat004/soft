import sys
import os
import time

# Принудительная установка UTF-8 для вывода в консоль Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_batch_tts_api():
    print("\n--- [ТЕСТ 1] Пакетный асинхронный TTS /api/batch/tts ---")
    items = [
        {"frame_id": f"frame_{i}", "text": f"Кадр номер {i}. Проверка работы асинхронного сервиса."}
        for i in range(1, 5)
    ]
    
    start_t = time.time()
    response = client.post("/api/batch/tts", json={"items": items, "max_concurrency": 4})
    elapsed = time.time() - start_t

    assert response.status_code == 200, f"Ошибка API: {response.text}"
    results = response.json()
    print(f"Ответ batch/tts ({len(results)} результатов, время {elapsed:.2f}s): {results}")
    assert len(results) == 4
    for res in results:
        assert "audio_url" in res
        assert "filename" in res
    print("✅ Тест параллельного TTS пройден!")

def test_batch_images_api():
    print("\n--- [ТЕСТ 2] Пакетная многопоточная генерация картинок /api/batch/images ---")
    items = [
        {"frame_id": f"frame_{i}", "prompt": f"Тестовая иллюстрация кадра {i}"}
        for i in range(1, 4)
    ]

    start_t = time.time()
    response = client.post("/api/batch/images", json={"items": items, "max_concurrency": 3})
    elapsed = time.time() - start_t

    assert response.status_code == 200, f"Ошибка API: {response.text}"
    results = response.json()
    print(f"Ответ batch/images ({len(results)} результатов, время {elapsed:.2f}s): {results}")
    assert len(results) == 3
    for res in results:
        assert "image_url" in res
    print("✅ Тест параллельной генерации картинок пройден!")

def test_batch_videos_api():
    print("\n--- [ТЕСТ 3] Пакетная параллельная генерация клипов /api/batch/videos ---")
    items = [
        {"frame_id": f"frame_{i}", "prompt": f"Тестовая анимация кадра {i}"}
        for i in range(1, 3)
    ]

    start_t = time.time()
    response = client.post("/api/batch/videos", json={"items": items, "duration": 2.0, "max_concurrency": 2})
    elapsed = time.time() - start_t

    assert response.status_code == 200, f"Ошибка API: {response.text}"
    results = response.json()
    print(f"Ответ batch/videos ({len(results)} результатов, время {elapsed:.2f}s): {results}")
    assert len(results) == 2
    for res in results:
        assert "video_url" in res
    print("✅ Тест параллельного рендеринга видео пройден!")

if __name__ == "__main__":
    test_batch_tts_api()
    test_batch_images_api()
    test_batch_videos_api()
