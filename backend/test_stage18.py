import sys
import os

# Принудительная установка UTF-8 для вывода в консоль Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient
from main import app
from app.services.logger import AppLogger, APP_LOG_PATH, ERROR_LOG_PATH

client = TestClient(app)

def test_file_logger_service():
    print("\n--- [ТЕСТ 1] Прямая проверка AppLogger ---")
    AppLogger.info("ТЕСТ_ИНФО_СООБЩЕНИЕ: Системная проверка логгера.")
    AppLogger.warning("ТЕСТ_ПРЕДУПРЕЖДЕНИЕ: Проверка записи предупреждения.")
    AppLogger.error("ТЕСТ_ОШИБКА: Проверка трекинга ошибки.", exc_info=False)

    assert os.path.exists(APP_LOG_PATH), "Файл app.log не создан!"
    assert os.path.exists(ERROR_LOG_PATH), "Файл error.log не создан!"

    logs = AppLogger.read_file_logs(limit=10)
    print(f"Записей в app.log: {len(logs['app_log'])}, в error.log: {len(logs['error_log'])}")
    assert len(logs["app_log"]) > 0
    assert len(logs["error_log"]) > 0
    print("✅ Файловый логгер работает корректно!")

def test_file_logs_api_endpoint():
    print("\n--- [ТЕСТ 2] Проверка REST API /api/system/file-logs ---")
    response = client.get("/api/system/file-logs?limit=50")
    assert response.status_code == 200, f"Ошибка API: {response.text}"
    data = response.json()
    assert "app_log" in data
    assert "error_log" in data
    print(f"Получены логи через REST API: {len(data['app_log'])} строк app.log")
    print("✅ REST API /api/system/file-logs работает успешно!")

if __name__ == "__main__":
    test_file_logger_service()
    test_file_logs_api_endpoint()
