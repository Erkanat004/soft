import os
from typing import Dict, Any, List
from app.models.script import ScriptParseResult, Frame

class CostTrackerService:
    # Базовые тарифные расценки (в USD)
    TTS_PRICE_PER_1K_CHARS = 0.015  # ~$0.015 за 1000 символов озвучки
    IMAGE_PRICE_PER_ITEM = 0.01     # ~$0.01 за уникальную иллюстрацию
    VIDEO_PRICE_PER_ITEM = 0.05     # ~$0.05 за видеоанимацию

    @classmethod
    def calculate_script_cost(cls, script_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Рассчитывает смету генерации медиа для сценария, включая затраты
        и сэкономленные средства благодаря локальному MD5 кэшу.
        """
        scenes = script_data.get("scenes", [])
        
        total_chars = 0
        total_images = 0
        total_videos = 0

        cached_audio_count = 0
        cached_image_count = 0
        cached_video_count = 0
        total_items_count = 0

        for scene in scenes:
            frames = scene.get("frames", [])
            for frame in frames:
                total_items_count += 1
                
                # Текст для TTS
                text = frame.get("narration_text", "")
                total_chars += len(text)
                if frame.get("audio_path") and os.path.exists(frame.get("audio_path")):
                    cached_audio_count += 1

                # Картинки
                visual_prompt = frame.get("visual_prompt", "")
                if visual_prompt:
                    total_images += 1
                if frame.get("image_path") and os.path.exists(frame.get("image_path")):
                    cached_image_count += 1

                # Видео
                if visual_prompt:
                    total_videos += 1
                if frame.get("video_path") and os.path.exists(frame.get("video_path")):
                    cached_video_count += 1

        # Расчет полной потенциальной стоимости
        tts_cost = round((total_chars / 1000.0) * cls.TTS_PRICE_PER_1K_CHARS, 4)
        image_cost = round(total_images * cls.IMAGE_PRICE_PER_ITEM, 4)
        video_cost = round(total_videos * cls.VIDEO_PRICE_PER_ITEM, 4)
        total_estimated_cost = round(tts_cost + image_cost + video_cost, 4)

        # Расчет фактической стоимости с учетом кэша
        actual_tts_cost = round(((total_chars if cached_audio_count == 0 else 0) / 1000.0) * cls.TTS_PRICE_PER_1K_CHARS, 4)
        actual_image_cost = round((max(0, total_images - cached_image_count)) * cls.IMAGE_PRICE_PER_ITEM, 4)
        actual_video_cost = round((max(0, total_videos - cached_video_count)) * cls.VIDEO_PRICE_PER_ITEM, 4)
        actual_cost = round(actual_tts_cost + actual_image_cost + actual_video_cost, 4)

        # Экономия от кэша
        cache_savings = round(total_estimated_cost - actual_cost, 4)
        cached_count = cached_audio_count + cached_image_count + cached_video_count

        return {
            "total_chars": total_chars,
            "total_images": total_images,
            "total_videos": total_videos,
            "tts_cost": tts_cost,
            "image_cost": image_cost,
            "video_cost": video_cost,
            "total_estimated_cost": total_estimated_cost,
            "actual_cost": actual_cost,
            "cache_savings": cache_savings,
            "cached_count": cached_count,
            "total_items_count": total_items_count
        }
