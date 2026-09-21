import os
import json
import logging
from typing import Callable, Any

STATE_FILE = os.path.join(os.getcwd(), "cache", "project_state.json")
os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("StateManager")

class StateManager:
    """ Сервис автосохранения состояний проекта и защиты от повторной оплаты при сбоях """

    @classmethod
    def save_state(cls, project_data: dict) -> str:
        """ Сохранение текущей структуры проекта в JSON """
        try:
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(project_data, f, ensure_ascii=False, indent=2)
            logger.info("Состояние проекта успешно сохранено в project_state.json")
            return STATE_FILE
        except Exception as e:
            logger.error(f"Ошибка сохранения состояния проекта: {e}")
            raise

    @classmethod
    def load_state(cls) -> dict:
        """ Восстановление сохраненного состояния проекта из JSON """
        if not os.path.exists(STATE_FILE):
            return {"title": "Новый Сценарий", "scenes": [], "total_scenes": 0, "total_frames": 0}

        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.info("Состояние проекта успешно восстановлено из файла")
            return data
        except Exception as e:
            logger.error(f"Ошибка выгрузки состояния проекта: {e}")
            return {"title": "Новый Сценарий", "scenes": [], "total_scenes": 0, "total_frames": 0}

    @classmethod
    def execute_with_fallback(cls, primary_fn: Callable[[], Any], fallback_fn: Callable[[], Any], provider_name: str = "Primary API") -> Any:
        """
        Паттерн Fallback: Попытка выполнения первичной (например, платной API) функции.
        В случае сбоя или исчерпания лимитов бесшовно переключается на резервный провайдер.
        """
        try:
            logger.info(f"Запуск первичного провайдера: {provider_name}")
            return primary_fn()
        except Exception as err:
            logger.warning(f"⚠️ [FALLBACK ACTIVATED] Ошибка в {provider_name}: {err}. Переключение на резервный генератор.")
            return fallback_fn()
