import asyncio
import sys
from app.services.tts import TTSService

sys.stdout.reconfigure(encoding='utf-8')

async def main():
    test_phrase = "Тестирование модуля озвучки генератора видео. Проверка кэширования речи."
    
    print("=== ТЕСТ 1: Первичная генерация озвучки ===")
    res1 = await TTSService.generate_speech(test_phrase)
    print(f"Путь: {res1['audio_path']}")
    print(f"Файл: {res1['filename']}")
    print(f"Длительность: {res1['duration']} сек.")
    print(f"Из кэша: {res1['cached']}")

    assert res1['duration'] > 0, "Длительность аудио должна быть больше 0"
    assert res1['cached'] is False, "Первый запуск должен быть без кэша"

    print("\n=== ТЕСТ 2: Повторный запуск (Проверка кэша) ===")
    res2 = await TTSService.generate_speech(test_phrase)
    print(f"Путь: {res2['audio_path']}")
    print(f"Длительность: {res2['duration']} сек.")
    print(f"Из кэша: {res2['cached']}")

    assert res2['cached'] is True, "Второй запуск должен быть из кэша"
    assert res1['filename'] == res2['filename'], "Хэши и имена файлов должны совпадать"
    assert res1['duration'] == res2['duration'], "Длительность должна совпадать"

    print("\n[SUCCESS] Все тесты модуля TTS и MD5-кэширования успешно пройдены!")

if __name__ == "__main__":
    asyncio.run(main())
