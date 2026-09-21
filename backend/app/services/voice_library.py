from typing import List, Dict, Any

class VoiceLibraryService:
    DEFAULT_VOICE = "ru-RU-DmitryNeural"

    VOICES_CATALOG: List[Dict[str, Any]] = [
        {
            "id": "ru-RU-DmitryNeural",
            "name": "Дмитрий (Русский - Мужской)",
            "lang": "ru-RU",
            "gender": "Male",
            "default": True
        },
        {
            "id": "ru-RU-SvetlanaNeural",
            "name": "Светлана (Русский - Женский)",
            "lang": "ru-RU",
            "gender": "Female",
            "default": False
        },
        {
            "id": "ru-RU-DariyaNeural",
            "name": "Дарья (Русский - Женский)",
            "lang": "ru-RU",
            "gender": "Female",
            "default": False
        },
        {
            "id": "en-US-GuyNeural",
            "name": "Guy (English US - Male)",
            "lang": "en-US",
            "gender": "Male",
            "default": False
        },
        {
            "id": "en-US-JennyNeural",
            "name": "Jenny (English US - Female)",
            "lang": "en-US",
            "gender": "Female",
            "default": False
        }
    ]

    @classmethod
    def get_available_voices(cls) -> List[Dict[str, Any]]:
        """ Возвращает полный список доступных голосов дикторов """
        return cls.VOICES_CATALOG

    @classmethod
    def validate_voice(cls, voice_id: str) -> str:
        """ Проверяет существование голоса, иначе возвращает голос по умолчанию """
        valid_ids = {v["id"] for v in cls.VOICES_CATALOG}
        if voice_id in valid_ids:
            return voice_id
        return cls.DEFAULT_VOICE
