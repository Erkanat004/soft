import os
import sys
from fastapi.testclient import TestClient
from main import app
from app.services.image_gen import ImageGenerationService

sys.stdout.reconfigure(encoding='utf-8')

client = TestClient(app)

def test_image_module():
    print("=== ТЕСТ 1: Первичная генерация картинки ===")
    prompt = "Огромная космическая станция на фоне гигантской туманности"
    res1 = ImageGenerationService.generate_image(prompt)
    print("Результат:", res1)
    
    assert os.path.exists(res1["image_path"]), "Файл картинки должен быть создан на диске"
    assert res1["cached"] is False, "Первый запуск должен быть без кэша"

    print("\n=== ТЕСТ 2: Повторная генерация (Проверка MD5 кэша) ===")
    res2 = ImageGenerationService.generate_image(prompt)
    print("Результат из кэша:", res2)

    assert res2["cached"] is True, "Второй запуск должен быть из кэша"
    assert res1["filename"] == res2["filename"]

    print("\n=== ТЕСТ 3: REST API (POST /api/image/generate) ===")
    api_res = client.post("/api/image/generate", json={
        "prompt": "Футуристичный робот собирает кубик Рубика",
        "frame_id": "frame_200"
    })
    assert api_res.status_code == 200, f"Ошибка API: {api_res.text}"
    data = api_res.json()
    print("Ответ API:", data)
    assert data["frame_id"] == "frame_200"
    assert "image_url" in data

    image_url = data["image_url"]
    print(f"\n=== ТЕСТ 4: REST API (GET {image_url}) ===")
    img_stream = client.get(image_url)
    assert img_stream.status_code == 200
    assert img_stream.headers["content-type"] == "image/png"
    print(f"Успешно получено изображение PNG размером {len(img_stream.content)} байт!")

    print("\n[SUCCESS] Все тесты модуля генерации картинок и кэша успешно пройдены!")

if __name__ == "__main__":
    test_image_module()
