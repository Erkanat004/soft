import sys
import os

# Принудительная установка UTF-8 для вывода в консоль Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient
from main import app
from app.services.voice_library import VoiceLibraryService

client = TestClient(app)

def test_voice_library_service():
    print("\n--- [ТЕСТ 1] Прямая проверка VoiceLibraryService ---")
    voices = VoiceLibraryService.get_available_voices()
    print(f"Каталог голосов ({len(voices)}): {[v['id'] for v in voices]}")
    assert len(voices) >= 5
    assert VoiceLibraryService.validate_voice("ru-RU-DmitryNeural") == "ru-RU-DmitryNeural"
    assert VoiceLibraryService.validate_voice("non_existent_voice") == VoiceLibraryService.DEFAULT_VOICE
    print("✅ Тест VoiceLibraryService пройден успешно!")

def test_voice_api_endpoints():
    print("\n--- [ТЕСТ 2] Проверка REST API /api/voices и /api/voice/preset ---")
    response = client.get("/api/voices")
    assert response.status_code == 200
    data = response.json()
    assert "voices" in data
    assert len(data["voices"]) >= 5
    print(f"Ответ API /api/voices: {data['voices'][0]}")

    preset_resp = client.post("/api/voice/preset", json={"voice_id": "ru-RU-SvetlanaNeural"})
    assert preset_resp.status_code == 200
    assert preset_resp.json()["selected_voice"] == "ru-RU-SvetlanaNeural"
    print("✅ REST API /api/voices и /api/voice/preset работают корректно!")

if __name__ == "__main__":
    test_voice_library_service()
    test_voice_api_endpoints()
