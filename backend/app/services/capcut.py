import os
import json
import hashlib
import time
import zipfile
from typing import Dict, Any

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "cache", "capcut")
os.makedirs(CACHE_DIR, exist_ok=True)

class CapCutExportService:
    """ Сервис экспорта проекта в родной формат черновика CapCut (draft_content.json + draft_meta_info.json) """

    @classmethod
    def generate_capcut_project(cls, timeline_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Генерирует файлы проекта CapCut (.json / .zip), 
        готовые к импорту в CapCut Desktop или мобильный редактор.
        """
        title = timeline_data.get("title", "YouTube_CapCut_Project")
        total_duration = timeline_data.get("total_duration", 0.0)
        timeline = timeline_data.get("timeline", [])

        hash_input = f"{title}_{total_duration}_{len(timeline)}"
        file_hash = hashlib.md5(hash_input.encode("utf-8")).hexdigest()
        
        json_filename = f"capcut_draft_{file_hash}.json"
        json_filepath = os.path.join(CACHE_DIR, json_filename)
        
        zip_filename = f"capcut_project_{file_hash}.zip"
        zip_filepath = os.path.join(CACHE_DIR, zip_filename)

        # В CapCut временная шкала измеряется в микросекундах (1 секунда = 1 000 000 микросекунд)
        total_us = int(total_duration * 1_000_000)

        audios_materials = []
        videos_materials = []
        texts_materials = []

        video_segments = []
        audio_segments = []

        current_offset_us = 0

        for idx, tf in enumerate(timeline):
            dur = tf.get("duration", 3.0)
            dur_us = int(dur * 1_000_000)
            frame_id = tf.get("frame_id", f"frame_{idx}")

            media_p = tf.get("media_path", "")
            audio_p = tf.get("audio_path", "")

            # 1. Видео / Картинка
            v_mat_id = f"mat_video_{idx}"
            abs_media = os.path.abspath(media_p).replace("\\", "/") if media_p else ""
            
            videos_materials.append({
                "id": v_mat_id,
                "path": abs_media,
                "duration": dur_us,
                "height": 720,
                "width": 1280,
                "type": "photo" if tf.get("media_type") == "image" else "video"
            })

            video_segments.append({
                "id": f"seg_v_{idx}",
                "material_id": v_mat_id,
                "target_timerange": {
                    "start": current_offset_us,
                    "duration": dur_us
                },
                "source_timerange": {
                    "start": 0,
                    "duration": dur_us
                }
            })

            # 2. Озвучка речи (Аудио)
            if audio_p:
                a_mat_id = f"mat_audio_{idx}"
                abs_audio = os.path.abspath(audio_p).replace("\\", "/")
                audios_materials.append({
                    "id": a_mat_id,
                    "path": abs_audio,
                    "duration": dur_us,
                    "type": "extract"
                })

                audio_segments.append({
                    "id": f"seg_a_{idx}",
                    "material_id": a_mat_id,
                    "target_timerange": {
                        "start": current_offset_us,
                        "duration": dur_us
                    },
                    "source_timerange": {
                        "start": 0,
                        "duration": dur_us
                    }
                })

            current_offset_us += dur_us

        # Формат CapCut draft_content.json
        draft_content = {
            "canvas_config": {
                "height": 720,
                "ratio": "16:9",
                "width": 1280
            },
            "color_space": 0,
            "config": {
                "adjust_max_index": 1,
                "extract_audio_index": len(audios_materials),
                "fps": 30.0,
                "gif_max_index": 1,
                "sticker_max_index": 1,
                "subtitle_keywords_config": None,
                "video_mute": False
            },
            "duration": total_us,
            "fps": 30.0,
            "id": f"capcut_draft_{file_hash}",
            "materials": {
                "audios": audios_materials,
                "videos": videos_materials,
                "texts": texts_materials
            },
            "tracks": [
                {
                    "id": "track_video_main",
                    "type": "video",
                    "segments": video_segments
                },
                {
                    "id": "track_audio_main",
                    "type": "audio",
                    "segments": audio_segments
                }
            ]
        }

        # Запись JSON файла проекта
        with open(json_filepath, "w", encoding="utf-8") as f:
            json.dump(draft_content, f, ensure_ascii=False, indent=2)

        # Метаданные проекта CapCut
        draft_meta = {
            "draft_id": f"capcut_draft_{file_hash}",
            "draft_name": title,
            "draft_timeline_materials_size": len(timeline),
            "tm_draft_create": int(time.time() * 1000),
            "tm_draft_modified": int(time.time() * 1000)
        }
        meta_filepath = os.path.join(CACHE_DIR, f"capcut_meta_{file_hash}.json")
        with open(meta_filepath, "w", encoding="utf-8") as f:
            json.dump(draft_meta, f, ensure_ascii=False, indent=2)

        # Формирование готового ZIP-пакета проекта CapCut
        with zipfile.ZipFile(zip_filepath, "w", zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(json_filepath, arcname="draft_content.json")
            zipf.write(meta_filepath, arcname="draft_meta_info.json")

        return {
            "filename": zip_filename,
            "json_filename": json_filename,
            "capcut_url": f"/api/capcut/{zip_filename}",
            "capcut_json_url": f"/api/capcut/{json_filename}",
            "capcut_path": zip_filepath
        }
