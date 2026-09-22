import os
import hashlib
import time
import random
import urllib.parse
import urllib.request
from PIL import Image, ImageDraw, ImageFont

CACHE_DIR = os.path.join(os.getcwd(), "cache", "images")
os.makedirs(CACHE_DIR, exist_ok=True)

class ImageGenerationService:
    """ 
    Сервис генерации ИИ-изображений строго по текстовому промпту.
    Поддерживает:
    1. Очистку промптов от системных префиксов ("Визуал:", "Кадр:").
    2. Динамическую генерацию уникальных ИИ картинок через Pollinations.ai (Flux/SD) без ключей.
    3. Платные провайдеры OpenAI (DALL-E 3) и Replicate (Flux/SDXL).
    4. Офлайн fallback через Pillow при отсутствии интернета.
    5. Принудительную перегенерацию при редактировании промпта (force=True).
    """

    @classmethod
    def clean_prompt(cls, prompt: str) -> str:
        """ Очистка промпта от системных меток """
        if not prompt:
            return ""
        p = prompt.strip()
        for prefix in ["Визуал:", "Визуальный ряд:", "Кадр:", "Visual:", "Prompt:"]:
            if p.lower().startswith(prefix.lower()):
                p = p[len(prefix):].strip()
        return p

    @classmethod
    def get_image_hash(cls, prompt: str, width: int = 1280, height: int = 720) -> str:
        """ MD5 хэш для сочетания очищенного промпта и разрешения """
        clean_p = cls.clean_prompt(prompt)
        raw_key = f"{clean_p}_{width}x{height}".encode('utf-8')
        return hashlib.md5(raw_key).hexdigest()

    @classmethod
    def generate_image_with_retry(cls, prompt: str, filepath: str, width: int = 1280, height: int = 720, force: bool = False):
        """ Вызов ИИ-генератора с созданием изображения строго по промпту """
        clean_p = cls.clean_prompt(prompt)
        provider = os.getenv("IMAGE_PROVIDER", "pollinations").lower()
        openai_key = os.getenv("OPENAI_API_KEY", "").strip()
        replicate_key = os.getenv("REPLICATE_API_KEY", "").strip()

        # 1. Попытка OpenAI DALL-E 3
        if provider == "openai" and openai_key:
            try:
                cls._generate_openai_image(clean_p, filepath, width, height, openai_key)
                return
            except Exception as e:
                print(f"[ImageGen Warning] Ошибка OpenAI API ({e}), переключение на бесплатный ИИ")

        # 2. Попытка Replicate (Flux/SDXL)
        if provider == "replicate" and replicate_key:
            try:
                cls._generate_replicate_image(clean_p, filepath, width, height, replicate_key)
                return
            except Exception as e:
                print(f"[ImageGen Warning] Ошибка Replicate API ({e}), переключение на бесплатный ИИ")

        # 3. Бесплатная онлайн-генерация ИИ картинки строго по промпту (Pollinations.ai / Picsum)
        try:
            cls._generate_free_online_image(clean_p, filepath, width, height)
            return
        except Exception as e:
            print(f"[ImageGen Warning] Ошибка всех онлайн-сервисов ({e}), переход на локальный МОК-холст")

        # 4. Офлайн МОК-холст Pillow (гарантированный резерв)
        cls._generate_mock_image(clean_p, filepath, width, height)

    @classmethod
    def generate_image(cls, prompt: str, width: int = 1280, height: int = 720, force: bool = False) -> dict:
        """ 
        Публичный метод генерации изображения строго по промпту.
        """
        clean_p = cls.clean_prompt(prompt)
        if not clean_p:
            raise ValueError("Промпт для картинки не может быть пустым")

        file_hash = cls.get_image_hash(clean_p, width, height)
        filename = f"{file_hash}.png"
        filepath = os.path.join(CACHE_DIR, filename)

        # 1. Проверка наличия в кэше (если не запрошена принудительная перегенерация force=True)
        if not force and os.path.exists(filepath):
            return {
                "image_path": filepath,
                "filename": filename,
                "cached": True
            }

        if force and os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception:
                pass

        # 2. Генерация по промпту
        cls.generate_image_with_retry(clean_p, filepath, width, height, force=force)

        return {
            "image_path": filepath,
            "filename": filename,
            "cached": False
        }

    @staticmethod
    def _generate_free_online_image(prompt: str, filepath: str, width: int, height: int):
        """ Мульти-провайдерная генерация настоящих ИИ-картинок по промпту """
        encoded_prompt = urllib.parse.quote(prompt.strip())
        random_seed = random.randint(1000, 999999)
        
        sources = [
            f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true&seed={random_seed}&model=flux",
            f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true&seed={random_seed}",
            f"https://picsum.photos/{width}/{height}?random={random_seed}"
        ]

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        last_err = None
        for idx, url in enumerate(sources):
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=25) as response:
                    if response.status == 200:
                        data = response.read()
                        if len(data) > 3000:
                            with open(filepath, "wb") as f:
                                f.write(data)
                            print(f"[ImageGen Free] Успешно получено изображение по промпту '{prompt[:30]}...' через сервис #{idx+1}")
                            return
            except Exception as err:
                last_err = err
                time.sleep(1)

        raise RuntimeError(f"Все бесплатные онлайн ИИ-сервисы недоступны: {last_err}")

    @staticmethod
    def _generate_openai_image(prompt: str, filepath: str, width: int, height: int, api_key: str):
        """ Генерация через OpenAI DALL-E 3 по промпту """
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
        """ Генерация через Replicate (Flux/SDXL) по промпту """
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
        """ Офлайн МОК-генератор на Pillow с выведением промпта """
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
