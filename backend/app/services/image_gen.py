import os
import hashlib
import time
import urllib.parse
import urllib.request
from PIL import Image, ImageDraw, ImageFont

CACHE_DIR = os.path.join(os.getcwd(), "cache", "images")
os.makedirs(CACHE_DIR, exist_ok=True)

class ImageGenerationService:
    """ 
    Сервис генерации ИИ-изображений.
    Поддерживает:
    1. Бесплатную онлайн-генерацию настоящих ИИ картинок (Pollinations.ai / Picsum Real Photos) — 0 API ключей, аналогично Edge-TTS.
    2. Платные провайдеры OpenAI (DALL-E 3) и Replicate (Flux/SDXL) при наличии ключей.
    3. Офлайн fallback через Pillow при полном отсутствии сети.
    4. Кэширование по MD5.
    """

    @classmethod
    def get_image_hash(cls, prompt: str, width: int = 1280, height: int = 720) -> str:
        """ MD5 хэш для сочетания промпта и разрешения """
        raw_key = f"{prompt.strip()}_{width}x{height}".encode('utf-8')
        return hashlib.md5(raw_key).hexdigest()

    @classmethod
    def generate_image_with_retry(cls, prompt: str, filepath: str, width: int = 1280, height: int = 720):
        """ Вызов онлайн ИИ-генератора с автоматическим переходом по цепочке провайдеров """
        provider = os.getenv("IMAGE_PROVIDER", "pollinations").lower()
        openai_key = os.getenv("OPENAI_API_KEY", "").strip()
        replicate_key = os.getenv("REPLICATE_API_KEY", "").strip()

        # 1. Попытка OpenAI DALL-E (если задан платный ключ)
        if provider == "openai" and openai_key:
            try:
                cls._generate_openai_image(prompt, filepath, width, height, openai_key)
                return
            except Exception as e:
                print(f"[ImageGen Warning] Ошибка OpenAI API ({e}), переключение на бесплатную ИИ-цепочку")

        # 2. Попытка Replicate (если задан платный ключ)
        if provider == "replicate" and replicate_key:
            try:
                cls._generate_replicate_image(prompt, filepath, width, height, replicate_key)
                return
            except Exception as e:
                print(f"[ImageGen Warning] Ошибка Replicate API ({e}), переключение на бесплатную ИИ-цепочку")

        # 3. Бесплатная ИИ-генерация онлайн (Pollinations.ai + Picsum HD Photos — без ключей, как edge-tts)
        try:
            cls._generate_free_online_image(prompt, filepath, width, height)
            return
        except Exception as e:
            print(f"[ImageGen Warning] Ошибка всех онлайн-сервисов ({e}), переход на локальный офлайн МОК-холст")

        # 4. Офлайн МОК-холст Pillow (гарантированный резерв)
        cls._generate_mock_image(prompt, filepath, width, height)

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

        # 2. Генерация
        cls.generate_image_with_retry(clean_prompt, filepath, width, height)

        return {
            "image_path": filepath,
            "filename": filename,
            "cached": False
        }

    @staticmethod
    def _generate_free_online_image(prompt: str, filepath: str, width: int, height: int):
        """ Мульти-провайдерная бесплатная генерация ИИ и HD-фотографий без ключей """
        encoded_prompt = urllib.parse.quote(prompt.strip())
        
        sources = [
            f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true&model=flux",
            f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true",
            f"https://picsum.photos/{width}/{height}?random={abs(hash(prompt)) % 1000}"
        ]

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        last_err = None
        for idx, url in enumerate(sources):
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=20) as response:
                    if response.status == 200:
                        data = response.read()
                        if len(data) > 3000:
                            with open(filepath, "wb") as f:
                                f.write(data)
                            print(f"[ImageGen Free] Успешно получено изображение через бесплатный онлайн-сервис #{idx+1}")
                            return
            except Exception as err:
                last_err = err
                time.sleep(1)

        raise RuntimeError(f"Все бесплатные онлайн ИИ-сервисы недоступны: {last_err}")

    @staticmethod
    def _generate_openai_image(prompt: str, filepath: str, width: int, height: int, api_key: str):
        """ Генерация через OpenAI DALL-E 3 """
        import openai
        client = openai.OpenAI(api_key=api_key)
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=f"{width}x{height}" if width in [1024, 1792] else "1024x1024",
            quality="standard",
            n=1,
        )
        image_url = response.data[0].url
        req = urllib.request.Request(image_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = resp.read()
            with open(filepath, "wb") as f:
                f.write(data)

    @staticmethod
    def _generate_replicate_image(prompt: str, filepath: str, width: int, height: int, api_key: str):
        """ Генерация через Replicate (Flux/SDXL) """
        import replicate
        os.environ["REPLICATE_API_TOKEN"] = api_key
        output = replicate.run(
            "black-forest-labs/flux-schnell",
            input={"prompt": prompt, "width": width, "height": height}
        )
        if output and len(output) > 0:
            img_url = str(output[0])
            req = urllib.request.Request(img_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=25) as resp:
                data = resp.read()
                with open(filepath, "wb") as f:
                    f.write(data)

    @staticmethod
    def _generate_mock_image(prompt: str, filepath: str, width: int, height: int):
        """ Офлайн МОК-генератор на Pillow """
        img = Image.new('RGB', (width, height), color='#1e293b')
        draw = ImageDraw.Draw(img)

        draw.rectangle([20, 20, width - 20, height - 20], outline='#38bdf8', width=4)

        title_text = "AI GENERATED PREVIEW (OFFLINE)"
        draw.text((40, 40), title_text, fill='#38bdf8')

        max_chars = 45
        wrapped_lines = [prompt[i:i+max_chars] for i in range(0, len(prompt), max_chars)]
        text_y = 120
        for line in wrapped_lines[:10]:
            draw.text((40, text_y), line, fill='#f8fafc')
            text_y += 35

        img.save(filepath, format="PNG")
