import sys
import os
import xml.etree.ElementTree as ET

# Принудительная установка UTF-8 для вывода в консоль Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient
from main import app
from app.services.fcpxml import FCPXMLExportService

client = TestClient(app)

def test_fcpxml_service():
    print("\n--- [ТЕСТ 1] Прямая проверка FCPXMLExportService ---")
    mock_timeline = {
        "title": "Тест_FCPXML_Проекта",
        "total_duration": 10.5,
        "formatted_total_duration": "00:10.5",
        "total_scenes": 1,
        "total_frames": 2,
        "timeline": [
            {
                "frame_id": "scene_1_frame_1",
                "scene_number": 1,
                "frame_number": 1,
                "start_time": 0.0,
                "end_time": 5.0,
                "duration": 5.0,
                "formatted_start": "00:00.0",
                "formatted_end": "00:05.0",
                "narration_text": "Первый кадр сценария.",
                "visual_prompt": "Горный пейзаж",
                "audio_path": "cache/audio/test_audio_1.mp3",
                "media_path": "cache/images/test_img_1.png",
                "media_type": "image"
            },
            {
                "frame_id": "scene_1_frame_2",
                "scene_number": 1,
                "frame_number": 2,
                "start_time": 5.0,
                "end_time": 10.5,
                "duration": 5.5,
                "formatted_start": "00:05.0",
                "formatted_end": "00:10.5",
                "narration_text": "Второй кадр сценария.",
                "visual_prompt": "Космический корабль",
                "audio_path": "cache/audio/test_audio_2.mp3",
                "media_path": "cache/videos/test_vid_2.mp4",
                "media_type": "video"
            }
        ]
    }

    res = FCPXMLExportService.generate_fcpxml(mock_timeline)
    print(f"Сформирован FCPXML: {res['filename']} ({res['fcpxml_path']})")
    assert os.path.exists(res["fcpxml_path"])
    
    # Проверка валидности структуры XML
    tree = ET.parse(res["fcpxml_path"])
    root = tree.getroot()
    assert root.tag == "fcpxml"
    assert root.attrib["version"] == "1.8"
    print("✅ Валидация XML дерева FCPXML прошла успешно!")

def test_fcpxml_api_endpoints():
    print("\n--- [ТЕСТ 2] Проверка REST API POST /api/export/fcpxml ---")
    mock_timeline = {
        "title": "API_FCPXML_Test",
        "total_duration": 4.0,
        "formatted_total_duration": "00:04.0",
        "total_scenes": 1,
        "total_frames": 1,
        "timeline": [
            {
                "frame_id": "frame_1",
                "duration": 4.0,
                "narration_text": "Тест API",
                "visual_prompt": "Тест"
            }
        ]
    }

    response = client.post("/api/export/fcpxml", json=mock_timeline)
    assert response.status_code == 200, f"Ошибка API: {response.text}"
    data = response.json()
    assert "fcpxml_url" in data
    assert "filename" in data

    file_resp = client.get(data["fcpxml_url"])
    assert file_resp.status_code == 200
    assert "fcpxml" in file_resp.text
    print("✅ REST API экспорта FCPXML работает успешно!")

if __name__ == "__main__":
    test_fcpxml_service()
    test_fcpxml_api_endpoints()
