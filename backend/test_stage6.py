import os
import sys
from fastapi.testclient import TestClient
from main import app
from app.services.video_gen import VideoGenerationService

sys.stdout.reconfigure(encoding='utf-8')

client = TestClient(app)

def test_video_module():
    print("=== ТЕСТ 1: Первичная генерация анимации MP4 ===")
    prompt = "Запуск ракеты с клубами дыма и пламени"
    res1 = VideoGenerationService.generate_video(prompt, duration=2.0)
    print("Результат генерации:", res1)
    
    assert os.path.exists(res1["video_path"]), "Файл видео MP4 должен быть создан на диске"
    assert res1["cached"] is False, "Первый запуск должен быть без кэша"

    print("\n=== ТЕСТ 2: Повторная генерация (Проверка MD5 кэша) ===")
    res2 = VideoGenerationService.generate_video(prompt, duration=2.0)
    print("Результат из кэша:", res2)

    assert res2["cached"] is True, "Второй запуск должен быть из кэша"
    assert res1["filename"] == res2["filename"]

    print("\n=== ТЕСТ 3: REST API (POST /api/video/generate) ===")
    api_res = client.post("/api/video/generate", json={
        "prompt": "Полет над футуристическим городом",
        "frame_id": "frame_300",
        "duration": 2.0
    })
    assert api_res.status_code == 200, f"Ошибка API: {api_res.text}"
    data = api_res.json()
    print("Ответ API:", data)
    assert data["frame_id"] == "frame_300"
    assert "video_url" in data

    video_url = data["video_url"]
    print(f"\n=== ТЕСТ 4: REST API (GET {video_url}) ===")
    video_stream = client.get(video_url)
    assert video_stream.status_code == 200
    assert video_stream.headers["content-type"] == "video/mp4"
    print(f"Успешно получен поток видео MP4 размером {len(video_stream.content)} байт!")

    print("\n[SUCCESS] Все тесты модуля анимации видеоклипов успешно пройдены!")

if __name__ == "__main__":
    test_video_module()
