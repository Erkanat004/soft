import os
from typing import Dict, Any, Optional

ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")

class SettingsService:
    @classmethod
    def get_settings(cls) -> Dict[str, Any]:
        """ Возвращает текущее состояние настроек и статус ключей """
        openai_key = os.getenv("OPENAI_API_KEY", "")
        replicate_key = os.getenv("REPLICATE_API_KEY", "")
        elevenlabs_key = os.getenv("ELEVENLABS_API_KEY", "")

        has_keys = bool(openai_key.strip() or replicate_key.strip() or elevenlabs_key.strip())
        current_provider = os.getenv("IMAGE_PROVIDER", "pollinations")

        if has_keys:
            if openai_key.strip():
                current_provider = "openai"
                os.environ["IMAGE_PROVIDER"] = "openai"
            elif replicate_key.strip():
                current_provider = "replicate"
                os.environ["IMAGE_PROVIDER"] = "replicate"

        if has_keys:
            status_label = "🟢 Платные ИИ активны (OpenAI / Replicate)"
            is_active = True
        elif current_provider == "mock":
            status_label = "🟡 Офлайн МОК-режим (Локальный холст)"
            is_active = False
        else:
            status_label = "🟢 Бесплатный онлайн ИИ активен (Pollinations.ai - без ключей)"
            is_active = True

        return {
            "openai_api_key_set": bool(openai_key.strip()),
            "replicate_api_key_set": bool(replicate_key.strip()),
            "elevenlabs_api_key_set": bool(elevenlabs_key.strip()),
            "openai_api_key_masked": f"{openai_key[:6]}...{openai_key[-4:]}" if len(openai_key) > 10 else "",
            "replicate_api_key_masked": f"{replicate_key[:4]}...{replicate_key[-4:]}" if len(replicate_key) > 8 else "",
            "image_provider": current_provider,
            "mock_disabled": is_active,
            "status_label": status_label
        }

    @classmethod
    def save_settings(
        cls, 
        openai_key: Optional[str] = None, 
        replicate_key: Optional[str] = None, 
        elevenlabs_key: Optional[str] = None,
        image_provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """ Сохраняет ключи в окружение и записывает в файл .env """
        if openai_key is not None and openai_key.strip():
            os.environ["OPENAI_API_KEY"] = openai_key.strip()
        if replicate_key is not None and replicate_key.strip():
            os.environ["REPLICATE_API_KEY"] = replicate_key.strip()
        if elevenlabs_key is not None and elevenlabs_key.strip():
            os.environ["ELEVENLABS_API_KEY"] = elevenlabs_key.strip()

        # Автоматическое переключение провайдера при наличии ключей
        if image_provider and image_provider.strip():
            os.environ["IMAGE_PROVIDER"] = image_provider.strip()
        elif os.getenv("OPENAI_API_KEY"):
            os.environ["IMAGE_PROVIDER"] = "openai"
        elif os.getenv("REPLICATE_API_KEY"):
            os.environ["IMAGE_PROVIDER"] = "replicate"
        else:
            os.environ["IMAGE_PROVIDER"] = "pollinations"

        env_dict = {}
        if os.path.exists(ENV_PATH):
            with open(ENV_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    line_str = line.strip()
                    if line_str and not line_str.startswith("#") and "=" in line_str:
                        k, v = line_str.split("=", 1)
                        env_dict[k.strip()] = v.strip()

        if os.getenv("OPENAI_API_KEY"): env_dict["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
        if os.getenv("REPLICATE_API_KEY"): env_dict["REPLICATE_API_KEY"] = os.getenv("REPLICATE_API_KEY")
        if os.getenv("ELEVENLABS_API_KEY"): env_dict["ELEVENLABS_API_KEY"] = os.getenv("ELEVENLABS_API_KEY")
        env_dict["IMAGE_PROVIDER"] = os.getenv("IMAGE_PROVIDER", "pollinations")

        with open(ENV_PATH, "w", encoding="utf-8") as f:
            f.write("# Настройки приложения и API Ключи\n")
            for k, v in env_dict.items():
                f.write(f"{k}={v}\n")

        return cls.get_settings()
