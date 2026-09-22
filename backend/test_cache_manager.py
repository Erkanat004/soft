import sys
import os
from fastapi.testclient import TestClient

sys.path.append(os.path.dirname(__file__))

from main import app
from app.services.cache_manager import CacheManagerService
from app.services.tts import CACHE_DIR as AUDIO_CACHE_DIR
from app.services.image_gen import CACHE_DIR as IMAGE_CACHE_DIR

client = TestClient(app)

def test_cache_management():
    print("=== ТЕСТ 1: Получение статистики кэша ===")
    stats_res = client.get("/api/cache/stats")
    assert stats_res.status_code == 200
    stats = stats_res.json()
    print("Статистика кэша:", stats)
    assert "audio" in stats
    assert "image" in stats
    assert "video" in stats
    assert "render" in stats

    print("\n=== ТЕСТ 2: Создание тестовых файлов кэша ===")
    dummy_audio = os.path.join(AUDIO_CACHE_DIR, "dummy_test.mp3")
    with open(dummy_audio, "wb") as f:
        f.write(b"AUDIO_DATA_TEST_BYTES" * 100)

    dummy_image = os.path.join(IMAGE_CACHE_DIR, "dummy_test.png")
    with open(dummy_image, "wb") as f:
        f.write(b"IMAGE_DATA_TEST_BYTES" * 100)

    assert os.path.exists(dummy_audio)
    assert os.path.exists(dummy_image)

    print("\n=== ТЕСТ 3: Раздельная очистка только КЭША АУДИО ===")
    clear_audio_res = client.post("/api/cache/clear", json={"cache_type": "audio"})
    assert clear_audio_res.status_code == 200
    audio_data = clear_audio_res.json()
    print("Результат очистки аудио:", audio_data)
    assert not os.path.exists(dummy_audio), "Файл аудио кэша должен быть удален!"
    assert os.path.exists(dummy_image), "Файл картинки НЕ должен быть затронут!"

    print("\n=== ТЕСТ 4: Раздельная очистка только КЭША КАРТИНОК ===")
    clear_img_res = client.post("/api/cache/clear", json={"cache_type": "image"})
    assert clear_img_res.status_code == 200
    img_data = clear_img_res.json()
    print("Результат очистки картинок:", img_data)
    assert not os.path.exists(dummy_image), "Файл картинки должен быть удален!"

    print("\n[SUCCESS] Все тесты раздельной очистки кэша успешно пройдены!")

if __name__ == "__main__":
    test_cache_management()
