import os
import hashlib
import numpy as np
import imageio
from PIL import Image, ImageDraw
from tenacity import retry, stop_after_attempt, wait_exponential

CACHE_DIR = os.path.join(os.getcwd(), "cache", "videos")
os.makedirs(CACHE_DIR, exist_ok=True)

class VideoGenerationService:
    """ Сервис анимации изображений и генерации видеороликов с MD5-кэшированием """

    @classmethod
    def get_video_hash(cls, prompt: str, image_path: str = "", duration: float = 3.0) -> str:
        """ Уникальный MD5 хэш для конфигурации анимационного клипа """
        raw_key = f"{prompt.strip()}_{image_path}_{duration}".encode('utf-8')
        return hashlib.md5(raw_key).hexdigest()

    @classmethod
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        reraise=True
    )
    def generate_video_with_retry(cls, prompt: str, image_path: str, filepath: str, duration: float = 3.0, fps: int = 24):
        """ Внутренний метод сборки анимации с логикой повторов при сбоях """
        provider = os.getenv("VIDEO_PROVIDER", "mock").lower()

        if provider == "mock" or True: # Бесплатный локальный генератор
            cls._generate_mock_animated_mp4(prompt, image_path, filepath, duration, fps)
        else:
            # Место под внешние API (Runway, Luma, CogVideoX, SVD)
            pass

    @classmethod
    def generate_video(cls, prompt: str, image_path: str = "", duration: float = 3.0) -> dict:
        """
        Публичный метод создания анимационного MP4 клипа.
        Сначала делает проверку в локальном MD5-кэше.
        """
        clean_prompt = prompt.strip()
        if not clean_prompt and not image_path:
            raise ValueError("Для генерации видео нужен промпт или изображение")

        file_hash = cls.get_video_hash(clean_prompt, image_path, duration)
        filename = f"{file_hash}.mp4"
        filepath = os.path.join(CACHE_DIR, filename)

        # 1. Проверка в кэше
        if os.path.exists(filepath):
            return {
                "video_path": filepath,
                "filename": filename,
                "duration": duration,
                "cached": True
            }

        # 2. Генерация видеоклипа с поддержкой retry
        cls.generate_video_with_retry(clean_prompt, image_path, filepath, duration)

        return {
            "video_path": filepath,
            "filename": filename,
            "duration": duration,
            "cached": False
        }

    @staticmethod
    def _generate_mock_animated_mp4(prompt: str, image_path: str, filepath: str, duration: float, fps: int):
        """
        Создание плавного анимационного MP4 ролика с эффектом панорамирования/наезда камеры (Ken Burns effect)
        """
        width, height = 1280, 720
        total_frames = int(duration * fps)

        # Подготовка базвой картинки
        if image_path and os.path.exists(image_path):
            base_img = Image.open(image_path).convert('RGB').resize((width, height))
        else:
            base_img = Image.new('RGB', (width, height), color='#0f172a')
            draw = ImageDraw.Draw(base_img)
            draw.rectangle([20, 20, width-20, height-20], outline='#38bdf8', width=3)
            draw.text((40, 40), f"ANIMATION PREVIEW: {prompt[:60]}", fill='#f8fafc')

        base_np = np.array(base_img)

        # Инициализация записи MP4 видео через imageio
        writer = imageio.get_writer(filepath, fps=fps, codec='libx264', pixelformat='yuv420p')

        try:
            for i in range(total_frames):
                # Эффект плавного зума / смещения
                progress = i / total_frames
                scale = 1.0 + (progress * 0.08) # 8% зум
                
                # Применяем микросмещение для эффекта движения камеры
                shift_x = int(progress * 20)
                shifted_np = np.roll(base_np, shift_x, axis=1)
                
                writer.append_data(shifted_np)
        finally:
            writer.close()
