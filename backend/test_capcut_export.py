import sys
import os
import json
import zipfile
from fastapi.testclient import TestClient

sys.path.append(os.path.dirname(__file__))

from main import app
from app.services.capcut import CapCutExportService

client = TestClient(app)

def test_capcut_export():
    print("=== ТЕСТ 1: Генерация проекта CapCut через сервис CapCutExportService ===")
    sample_timeline = {
        "title": "Тестовый_Проект_CapCut",
        "total_duration": 6.5,
        "timeline": [
            {
                "frame_id": "frame_1",
                "start": 0.0,
                "end": 3.0,
                "duration": 3.0,
                "media_path": "cache/images/test1.png",
                "media_type": "image",
                "audio_path": "cache/audio/test1.mp3",
                "narration_text": "Первый кадр для CapCut"
            },
            {
                "frame_id": "frame_2",
                "start": 3.0,
                "end": 6.5,
                "duration": 3.5,
                "media_path": "cache/videos/test2.mp4",
                "media_type": "video",
                "audio_path": "cache/audio/test2.mp3",
                "narration_text": "Второй кадр для CapCut"
            }
        ]
    }

    res = CapCutExportService.generate_capcut_project(sample_timeline)
    print("Результат сервиса CapCut:", res)

    assert os.path.exists(res["capcut_path"]), "ZIP-файл проекта CapCut должен существовать на диске"
    assert zipfile.is_zipfile(res["capcut_path"]), "Сформированный файл должен быть валидным ZIP-архивом"

    # Проверка содержимого архива
    with zipfile.ZipFile(res["capcut_path"], "r") as z:
        filenames = z.namelist()
        print("Содержимое ZIP-архива CapCut:", filenames)
        assert "draft_content.json" in filenames
        assert "draft_meta_info.json" in filenames

        # Проверка структуры draft_content.json
        with z.open("draft_content.json") as f:
            draft_json = json.loads(f.read().decode("utf-8"))
            print("Параметры драфта CapCut:", draft_json["canvas_config"], "Треков:", len(draft_json["tracks"]))
            assert draft_json["canvas_config"]["width"] == 1280
            assert draft_json["canvas_config"]["height"] == 720
            assert len(draft_json["tracks"]) == 2

    print("\n=== ТЕСТ 2: REST API (POST /api/export/capcut) ===")
    api_res = client.post("/api/export/capcut", json=sample_timeline)
    assert api_res.status_code == 200, f"Ошибка API: {api_res.text}"
    api_data = api_res.json()
    print("Ответ API CapCut:", api_data)
    assert "capcut_url" in api_data

    capcut_url = api_data["capcut_url"]
    print(f"\n=== ТЕСТ 3: Скачивание ZIP проекта (GET {capcut_url}) ===")
    file_stream = client.get(capcut_url)
    assert file_stream.status_code == 200
    assert file_stream.headers["content-type"] == "application/zip"
    print(f"Успешно получен ZIP-архив CapCut размером {len(file_stream.content)} байт!")

    print("\n[SUCCESS] Все тесты модуля экспорта в CapCut успешно пройдены!")

if __name__ == "__main__":
    test_capcut_export()
