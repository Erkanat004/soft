import os
import hashlib
import asyncio
import edge_tts
from mutagen.mp3 import MP3

CACHE_DIR = os.path.join(os.getcwd(), "cache", "audio")
os.makedirs(CACHE_DIR, exist_ok=True)

class TTSService:
    """ Сервис озвучивания текста с использованием Edge-TTS и MD5-кэшированием """

    DEFAULT_VOICE = "ru-RU-DmitryNeural"

    @classmethod
    def get_audio_hash(cls, text: str, voice: str) -> str:
        """ Генерация уникального MD5 хэша для комбинации текста и голоса """
        raw_key = f"{text.strip()}_{voice}".encode('utf-8')
        return hashlib.md5(raw_key).hexdigest()

    @classmethod
    async def generate_speech(cls, text: str, voice: str = DEFAULT_VOICE, force: bool = False) -> dict:
        """
        Генерация аудиофайла речи. 
        Возвращает словарь с путем к файлу, длительностью в секундах и признаком кэширования.
        Параметр force=True форсирует принудительное переозвучивание (байпас кэша).
        """
        clean_text = text.strip()
        if not clean_text:
            raise ValueError("Текст для озвучки не может быть пустым")

        file_hash = cls.get_audio_hash(clean_text, voice)
        filename = f"{file_hash}.mp3"
        filepath = os.path.join(CACHE_DIR, filename)

        # 1. Проверка наличия файла в кэше (если не запрошена принудительная переозвучка)
        if not force and os.path.exists(filepath):
            duration = cls.get_audio_duration(filepath)
            if duration > 0.1:
                return {
                    "audio_path": filepath,
                    "filename": filename,
                    "duration": round(duration, 2),
                    "cached": True
                }

        # 2. Удаляем старый кэшированный файл перед вызовом Edge TTS при принудительной переозвучке
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception as e:
                print(f"[TTS Warning] Ошибка удаления кэша перед переозвучкой: {e}")

        # 3. Вызываем Edge TTS
        communicate = edge_tts.Communicate(clean_text, voice)
        await communicate.save(filepath)

        # 4. Измеряем точную длительность сгенерированного MP3
        duration = cls.get_audio_duration(filepath)

        return {
            "audio_path": filepath,
            "filename": filename,
            "duration": round(duration, 2),
            "cached": False
        }

    @staticmethod
    def get_audio_duration(filepath: str) -> float:
        """ Измерение точной длительности MP3 файла в секундах """
        try:
            audio = MP3(filepath)
            return float(audio.info.length)
        except Exception as e:
            print(f"Ошибка измерения длительности MP3: {e}")
            return 0.0
