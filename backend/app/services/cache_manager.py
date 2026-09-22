import os
from typing import Dict, Any

from app.services.tts import CACHE_DIR as AUDIO_CACHE_DIR
from app.services.image_gen import CACHE_DIR as IMAGE_CACHE_DIR
from app.services.video_gen import CACHE_DIR as VIDEO_CACHE_DIR
from app.services.subtitles import CACHE_DIR as SUBTITLE_CACHE_DIR
from app.services.renderer import OUTPUT_DIR as RENDER_OUTPUT_DIR

class CacheManagerService:
    """ Сервис раздельного и полного управления/очистки кэша приложения """

    @classmethod
    def get_cache_stats(cls) -> Dict[str, Any]:
        """ Возвращает статистику файлов и занимаемого места по категориям """
        dirs = {
            "audio": AUDIO_CACHE_DIR,
            "image": IMAGE_CACHE_DIR,
            "video": VIDEO_CACHE_DIR,
            "subtitles": SUBTITLE_CACHE_DIR,
            "render": RENDER_OUTPUT_DIR
        }

        stats = {}
        for key, path in dirs.items():
            count = 0
            total_size = 0
            if os.path.exists(path):
                for fname in os.listdir(path):
                    fpath = os.path.join(path, fname)
                    if os.path.isfile(fpath):
                        count += 1
                        total_size += os.path.getsize(fpath)
            stats[key] = {
                "count": count,
                "bytes": total_size,
                "mb": round(total_size / (1024 * 1024), 2)
            }

        return stats

    @classmethod
    def clear_cache(cls, cache_type: str) -> Dict[str, Any]:
        """ Очищает выбранную категорию кэша или все кэши сразу """
        target_dirs = {}
        type_clean = cache_type.lower().strip()

        if type_clean == "audio":
            target_dirs["audio"] = AUDIO_CACHE_DIR
        elif type_clean == "image":
            target_dirs["image"] = IMAGE_CACHE_DIR
        elif type_clean == "video":
            target_dirs["video"] = VIDEO_CACHE_DIR
        elif type_clean == "subtitles":
            target_dirs["subtitles"] = SUBTITLE_CACHE_DIR
        elif type_clean == "render":
            target_dirs["render"] = RENDER_OUTPUT_DIR
        elif type_clean == "all":
            target_dirs = {
                "audio": AUDIO_CACHE_DIR,
                "image": IMAGE_CACHE_DIR,
                "video": VIDEO_CACHE_DIR,
                "subtitles": SUBTITLE_CACHE_DIR,
                "render": RENDER_OUTPUT_DIR
            }
        else:
            raise ValueError(f"Неизвестный тип кэша: {cache_type}")

        cleared_files = 0
        freed_bytes = 0

        for key, path in target_dirs.items():
            if os.path.exists(path):
                for fname in os.listdir(path):
                    fpath = os.path.join(path, fname)
                    try:
                        if os.path.isfile(fpath):
                            freed_bytes += os.path.getsize(fpath)
                            os.remove(fpath)
                            cleared_files += 1
                    except Exception as e:
                        print(f"[CacheManager Error] Не удалось удалить {fpath}: {e}")

        return {
            "status": "ok",
            "cache_type": type_clean,
            "cleared_files": cleared_files,
            "freed_bytes": freed_bytes,
            "freed_mb": round(freed_bytes / (1024 * 1024), 2),
            "stats": cls.get_cache_stats()
        }
