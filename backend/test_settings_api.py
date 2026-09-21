import sys
import os

# UTF-8 stdout fix for Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient
from main import app
from app.services.settings import SettingsService

client = TestClient(app)

def test_settings_service_and_api():
    print("\n--- [ТЕСТ] Проверка работы SettingsService и REST API /api/system/settings ---")
    
    # 1. Получение настроек
    resp = client.get("/api/system/settings")
    assert resp.status_code == 200
    data = resp.json()
    print(f"Старт настроек: {data}")

    # 2. Сохранение тестового ключа OpenAI
    save_resp = client.post("/api/system/settings", json={
        "openai_api_key": "sk-proj-test1234567890abcdef"
    })
    assert save_resp.status_code == 200
    saved_data = save_resp.json()
    print(f"После сохранения ключа OpenAI: {saved_data}")
    assert saved_data["mock_disabled"] == True
    assert saved_data["image_provider"] == "openai"
    assert "🟢" in saved_data["status_label"]

    print("✅ Тест управления API-ключами и авто-отключения МОК прошел успешно!")

if __name__ == "__main__":
    test_settings_service_and_api()
