import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any
from app.services.tts import TTSService
from app.services.image_gen import ImageGenerationService
from app.services.video_gen import VideoGenerationService

class BatchAsyncService:
    @classmethod
    async def generate_tts_batch(
        cls, 
        items: List[Dict[str, Any]], 
        voice: str = "ru-RU-DmitryNeural", 
        max_concurrency: int = 4,
        force: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Параллельная генерация TTS для списка кадров с помощью asyncio.Semaphore.
        Каждый элемент items должен содержать: {"frame_id": str, "text": str}.
        """
        semaphore = asyncio.Semaphore(max_concurrency)

        async def _single_tts(item: Dict[str, Any]) -> Dict[str, Any]:
            async with semaphore:
                frame_id = item.get("frame_id")
                text = item.get("text", "")
                if not text or not text.strip():
                    return {"frame_id": frame_id, "error": "Пустой текст"}
                try:
                    res = await TTSService.generate_speech(text=text, voice=voice, force=force)
                    return {
                        "frame_id": frame_id,
                        "audio_url": f"/api/audio/{res['filename']}",
                        "filename": res["filename"],
                        "duration": res["duration"],
                        "cached": res["cached"]
                    }
                except Exception as e:
                    return {"frame_id": frame_id, "error": str(e)}

        tasks = [_single_tts(item) for item in items]
        results = await asyncio.gather(*tasks)
        return list(results)

    @classmethod
    async def generate_images_batch(
        cls, 
        items: List[Dict[str, Any]], 
        width: int = 1280, 
        height: int = 720, 
        max_concurrency: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Многопоточная параллельная генерация картинок через ThreadPoolExecutor.
        Каждый элемент items должен содержать: {"frame_id": str, "prompt": str}.
        """
        loop = asyncio.get_running_loop()
        semaphore = asyncio.Semaphore(max_concurrency)
        executor = ThreadPoolExecutor(max_workers=max_concurrency)

        async def _single_image(item: Dict[str, Any]) -> Dict[str, Any]:
            async with semaphore:
                frame_id = item.get("frame_id")
                prompt = item.get("prompt", "")
                if not prompt or not prompt.strip():
                    return {"frame_id": frame_id, "error": "Пустой промпт"}
                try:
                    res = await loop.run_in_executor(
                        executor,
                        lambda: ImageGenerationService.generate_image(prompt=prompt, width=width, height=height)
                    )
                    return {
                        "frame_id": frame_id,
                        "image_url": f"/api/images/{res['filename']}",
                        "filename": res["filename"],
                        "cached": res["cached"]
                    }
                except Exception as e:
                    return {"frame_id": frame_id, "error": str(e)}

        tasks = [_single_image(item) for item in items]
        results = await asyncio.gather(*tasks)
        executor.shutdown(wait=False)
        return list(results)

    @classmethod
    async def generate_videos_batch(
        cls, 
        items: List[Dict[str, Any]], 
        duration: float = 3.0, 
        max_concurrency: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Параллельная многопоточная генерация видеоанимации.
        Каждый элемент items должен содержать: {"frame_id": str, "prompt": str}.
        """
        loop = asyncio.get_running_loop()
        semaphore = asyncio.Semaphore(max_concurrency)
        executor = ThreadPoolExecutor(max_workers=max_concurrency)

        async def _single_video(item: Dict[str, Any]) -> Dict[str, Any]:
            async with semaphore:
                frame_id = item.get("frame_id")
                prompt = item.get("prompt", "")
                if not prompt or not prompt.strip():
                    return {"frame_id": frame_id, "error": "Пустой промпт"}
                try:
                    res = await loop.run_in_executor(
                        executor,
                        lambda: VideoGenerationService.generate_video(prompt=prompt, duration=duration)
                    )
                    return {
                        "frame_id": frame_id,
                        "video_url": f"/api/videos/{res['filename']}",
                        "filename": res["filename"],
                        "cached": res["cached"]
                    }
                except Exception as e:
                    return {"frame_id": frame_id, "error": str(e)}

        tasks = [_single_video(item) for item in items]
        results = await asyncio.gather(*tasks)
        executor.shutdown(wait=False)
        return list(results)
