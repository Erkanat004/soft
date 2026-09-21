import sys
from fastapi.testclient import TestClient
from main import app
from app.services.parser import ScriptParser
from app.services.sync import SyncService

sys.stdout.reconfigure(encoding='utf-8')

client = TestClient(app)

def test_sync_module():
    print("=== ТЕСТ 1: Расчет таймлайна в SyncService ===")
    sample_text = """
Сцена 1: Запуск
[Кадр 1]
Озвучка: Первое короткое предложение для теста.
Визуал: Ракета на старте

[Кадр 2]
Озвучка: Второе более длинное предложение, предназначенное для проверки аккуратности сквозной синхронизации кадров.
Визуал: Пламя из двигателей

Сцена 2: Космос
[Кадр 1]
Озвучка: Финальное резюме видеоролика.
Визуал: Вид на Землю
"""
    script = ScriptParser.parse_text_to_script(sample_text)
    timeline = SyncService.sync_script(script)

    print(f"Название проекта: {timeline.title}")
    print(f"Общий хронометраж: {timeline.formatted_total_duration} ({timeline.total_duration}s)")
    print(f"Кадров на таймлайне: {len(timeline.timeline)}")

    for tf in timeline.timeline:
        print(f"  - [{tf.formatted_start} -> {tf.formatted_end}] ({tf.duration}s) | {tf.frame_id} | {tf.media_type}")

    # Проверки целостности временной шкалы
    assert timeline.timeline[0].start_time == 0.0
    assert timeline.timeline[1].start_time == timeline.timeline[0].end_time, "Время начала кадра 2 должно выравниваться по концу кадра 1"
    assert timeline.timeline[2].start_time == timeline.timeline[1].end_time, "Время начала кадра 3 должно выравниваться по концу кадра 2"
    assert timeline.total_duration == timeline.timeline[2].end_time

    print("\n=== ТЕСТ 2: REST API (POST /api/timeline/sync) ===")
    res = client.post("/api/timeline/sync", json=script.model_dump())
    assert res.status_code == 200, f"Ошибка API: {res.text}"
    data = res.json()
    print("Ответ API:", data["formatted_total_duration"], "сек:", data["total_duration"])
    assert data["total_frames"] == 3

    print("\n[SUCCESS] Все тесты модуля синхронизации таймлайнов успешно пройдены!")

if __name__ == "__main__":
    test_sync_module()
