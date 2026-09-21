import os
import sys
from fastapi.testclient import TestClient
from main import app
from app.services.parser import ScriptParser
from app.services.sync import SyncService
from app.services.renderer import RenderService

sys.stdout.reconfigure(encoding='utf-8')

client = TestClient(app)

def test_render_module():
    print("=== ТЕСТ 1: Сборка и компиляция локального MP4 роликов через RenderService ===")
    sample_text = """
Сцена 1: Запуск ракеты
[Кадр 1]
Озвучка: Старт космического корабля.
Визуал: Огромная ракета

[Кадр 2]
Озвучка: Ракета устремляется в вышину.
Визуал: Огненный шлейф
"""
    script = ScriptParser.parse_text_to_script(sample_text)
    timeline = SyncService.sync_script(script)
    res = RenderService.render_full_video(timeline)

    print("Результат компиляции:", res)
    assert os.path.exists(res["render_path"]), "Файл финального видео MP4 должен существовать на диске"

    print("\n=== ТЕСТ 2: REST API (POST /api/render/full-video) ===")
    api_res = client.post("/api/render/full-video", json=timeline.model_dump())
    assert api_res.status_code == 200, f"Ошибка API: {api_res.text}"
    data = api_res.json()
    print("Ответ API:", data)
    assert "render_url" in data

    render_url = data["render_url"]
    print(f"\n=== ТЕСТ 3: REST API (GET {render_url}) ===")
    video_stream = client.get(render_url)
    assert video_stream.status_code == 200
    assert video_stream.headers["content-type"] == "video/mp4"
    print(f"Успешно получен финальный скомпилированный фильм MP4 размером {len(video_stream.content)} байт!")

    print("\n[SUCCESS] Все тесты локального рендеринга видео успешно пройдены!")

if __name__ == "__main__":
    test_render_module()
