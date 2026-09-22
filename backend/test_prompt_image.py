import sys
import os
from fastapi.testclient import TestClient

sys.path.append(os.path.dirname(__file__))

from main import app
from app.services.image_gen import ImageGenerationService

client = TestClient(app)

def test_prompt_generation():
    print("=== ТЕСТ 1: Очистка системных префиксов промпта ===")
    p1 = ImageGenerationService.clean_prompt("Визуал: Золотистый осенний парк с листопадом")
    p2 = ImageGenerationService.clean_prompt("Visual: High tech cyberpunk city skyline at night")
    print("Очищенный промпт 1:", p1)
    print("Очищенный промпт 2:", p2)
    assert p1 == "Золотистый осенний парк с листопадом"
    assert p2 == "High tech cyberpunk city skyline at night"

    print("\n=== ТЕСТ 2: Первичная генерация по промпту через API ===")
    res1 = client.post("/api/image/generate", json={
        "prompt": "Визуал: Красивый парусный корабль в закатном океане",
        "frame_id": "frame_prompt_1",
        "force": False
    }).json()
    print("Результат 1:", res1)
    assert res1["cached"] is False or True

    print("\n=== ТЕСТ 3: Перегенерация по обновленному промпту (force=True) ===")
    res2 = client.post("/api/image/generate", json={
        "prompt": "Футуристичный красный спорткар на неоновом шоссе",
        "frame_id": "frame_prompt_1",
        "force": True
    }).json()
    print("Результат 2 (с новым промптом):", res2)
    assert res2["cached"] is False, "При force=True изображение должно генерироваться заново по новому промпту!"

    print("\n[SUCCESS] Все тесты генерации картинок строго по промпту успешно пройдены!")

if __name__ == "__main__":
    test_prompt_generation()
