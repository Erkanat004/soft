import os
import logging
from logging.handlers import RotatingFileHandler
from typing import Dict, Any

LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

APP_LOG_PATH = os.path.join(LOGS_DIR, "app.log")
ERROR_LOG_PATH = os.path.join(LOGS_DIR, "error.log")

# Настройка форматера логов
formatter = logging.Formatter(
    "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Главный логгер приложения
logger = logging.getLogger("YouTubeGenerator")
logger.setLevel(logging.INFO)
logger.propagate = False

if not logger.handlers:
    # 1. Файловый обработчик всех событий (app.log - до 5МБ, 3 бэкапа)
    app_handler = RotatingFileHandler(
        APP_LOG_PATH, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    app_handler.setLevel(logging.INFO)
    app_handler.setFormatter(formatter)
    logger.addHandler(app_handler)

    # 2. Файловый обработчик ошибок (error.log - до 5МБ, 3 бэкапа)
    error_handler = RotatingFileHandler(
        ERROR_LOG_PATH, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    error_handler.setLevel(logging.WARNING)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)

    # 3. Консольный обработчик
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

class AppLogger:
    @staticmethod
    def info(msg: str):
        logger.info(msg)

    @staticmethod
    def warning(msg: str):
        logger.warning(msg)

    @staticmethod
    def error(msg: str, exc_info: bool = True):
        logger.error(msg, exc_info=exc_info)

    @staticmethod
    def read_file_logs(limit: int = 100) -> Dict[str, Any]:
        """ Возвращает последние строки файлов логов """
        app_lines = []
        error_lines = []

        if os.path.exists(APP_LOG_PATH):
            with open(APP_LOG_PATH, "r", encoding="utf-8", errors="ignore") as f:
                app_lines = f.readlines()[-limit:]

        if os.path.exists(ERROR_LOG_PATH):
            with open(ERROR_LOG_PATH, "r", encoding="utf-8", errors="ignore") as f:
                error_lines = f.readlines()[-limit:]

        return {
            "app_log": [line.strip() for line in app_lines],
            "error_log": [line.strip() for line in error_lines],
            "app_log_path": APP_LOG_PATH,
            "error_log_path": ERROR_LOG_PATH
        }
