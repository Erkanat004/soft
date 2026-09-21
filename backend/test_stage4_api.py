import sys
from fastapi.testclient import TestClient
from main import app

sys.stdout.reconfigure(encoding='utf-8')

client = TestClient(app)

def test_api():
    print("=== ТЕСТ API: POST /api/tts/generate ===")
    response = client.post("/api/tts/generate", json={
        "text": "Проверка REST API эндпоинта озвучки",
        "voice": "ru-RU-DmitryNeural",
        "frame_id": "frame_100"
    })
    
    assert response.status_code == 200, f"Ошибка API: {response.status_code} - {response.text}"
    data = response.json()
    print("Ответ сервера:", data)
    assert data["frame_id"] == "frame_100"
    assert data["duration"] > 0
    assert "audio_url" in data

    audio_url = data["audio_url"]
    print(f"\n=== ТЕСТ API: GET {audio_url} ===")
    audio_res = client.get(audio_url)
    assert audio_res.status_code == 200
    assert audio_res.headers["content-type"] == "audio/mpeg"
    print(f"Успешно получен аудиофайл размером {len(audio_res.content)} байт!")

    print("\n[SUCCESS] Все REST API тесты озвучки пройдены отлично!")

if __name__ == "__main__":
    test_api()
