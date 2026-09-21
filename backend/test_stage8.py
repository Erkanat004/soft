import sys
from fastapi.testclient import TestClient
from main import app
from app.services.parser import ScriptParser
from app.services.sync import SyncService
from app.services.subtitles import SubtitleService

sys.stdout.reconfigure(encoding='utf-8')

client = TestClient(app)

def test_subtitles_module():
    print("=== ТЕСТ 1: Форматирование SRT и VTT в SubtitleService ===")
    sample_text = """
Сцена 1: Запуск
[Кадр 1]
Озвучка: Привет мир! Это первое тестовое предложение для субтитров.
Визуал: Космос

[Кадр 2]
Озвучка: Второе предложение идет следом на временной шкале.
Визуал: Звезды
"""
    script = ScriptParser.parse_text_to_script(sample_text)
    timeline = SyncService.sync_script(script)
    res = SubtitleService.generate_subtitles(timeline)

    print("--- СОДЕРЖИМОЕ SRT ---")
    print(res["srt_content"])

    print("--- СОДЕРЖИМОЕ VTT ---")
    print(res["vtt_content"])

    assert "-->" in res["srt_content"]
    assert "WEBVTT" in res["vtt_content"]
    assert "00:00:00,000" in res["srt_content"]

    print("\n=== ТЕСТ 2: REST API (POST /api/subtitles/generate) ===")
    api_res = client.post("/api/subtitles/generate", json=timeline.model_dump())
    assert api_res.status_code == 200, f"Ошибка API: {api_res.text}"
    data = api_res.json()
    print("Ответ API:", data["srt_filename"], data["vtt_filename"])
    assert "srt_url" in data

    srt_url = data["srt_url"]
    print(f"\n=== ТЕСТ 3: REST API (GET {srt_url}) ===")
    srt_stream = client.get(srt_url)
    assert srt_stream.status_code == 200
    print("Текст получен через HTTP:\n", srt_stream.text[:150])

    print("\n[SUCCESS] Все тесты модуля субтитров успешно пройдены!")

if __name__ == "__main__":
    test_subtitles_module()
