import os
import hashlib
from PIL import Image, ImageDraw, ImageFont
from tenacity import retry, stop_after_attempt, wait_exponential

CACHE_DIR = os.path.join(os.getcwd(), "cache", "images")
os.makedirs(CACHE_DIR, exist_ok=True)

class ImageGenerationService:
    """ Сервис генерации изображений с поддержкой кэша и повторных попыток (Retry) """

    @classmethod
    def get_image_hash(cls, prompt: str, width: int = 1280, height: int = 720) -> str:
        """ MD5 хэш для сочетания промпта и разрешения """
        raw_key = f"{prompt.strip()}_{width}x{height}".encode('utf-8')
        return hashlib.md5(raw_key).hexdigest()

    @classmethod
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        reraise=True
    )
    def generate_image_with_retry(cls, prompt: str, filepath: str, width: int = 1280, height: int = 720):
        """ Внутренняя функция генерации с логикой повторов при ошибках """
        provider = os.getenv("IMAGE_PROVIDER", "mock").lower()

        if provider == "mock" or True: # Дефолтный надежный офлайн генератор
            cls._generate_mock_image(prompt, filepath, width, height)
        else:
            # Место под внешний API провайдер (например, Replicate / OpenAI DALL-E)
            pass

    @classmethod
    def generate_image(cls, prompt: str, width: int = 1280, height: int = 720) -> dict:
        """ 
        Публичный метод генерации изображения.
        Проверяет кэш перед вызовом генератора.
        """
        clean_prompt = prompt.strip()
        if not clean_prompt:
            raise ValueError("Промпт для картинки не может быть пустым")

        file_hash = cls.get_image_hash(clean_prompt, width, height)
        filename = f"{file_hash}.png"
        filepath = os.path.join(CACHE_DIR, filename)

        # 1. Проверка наличия в кэше
        if os.path.exists(filepath):
            return {
                "image_path": filepath,
                "filename": filename,
                "cached": True
            }

        # 2. Генерация с логикой retry
        cls.generate_image_with_retry(clean_prompt, filepath, width, height)

        return {
            "image_path": filepath,
            "filename": filename,
            "cached": False
        }

    @staticmethod
    def _generate_mock_image(prompt: str, filepath: str, width: int, height: int):
        """ Создание стильного карточного превью для визуального промпта """
        # Создаем изображение в 16:9
        img = Image.new('RGB', (width, height), color='#1e293b')
        draw = ImageDraw.Draw(img)

        # Декоративный рамка
        draw.rectangle([20, 20, width - 20, height - 20], outline='#38bdf8', width=4)

        # Вывод названия и промпта
        title_text = "AI GENERATED PREVIEW"
        draw.text((40, 40), title_text, fill='#38bdf8')

        # Форматирование и перенос текста промпта
        max_chars = 45
        wrapped_lines = [prompt[i:i+max_chars] for i in range(0, len(prompt), max_chars)]
        text_y = 120
        for line in wrapped_lines[:10]:
            draw.text((40, text_y), line, fill='#f8fafc')
            text_y += 35

        # Сохранение в PNG
        img.save(filepath, format="PNG")
