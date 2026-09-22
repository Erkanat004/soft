import os
import json
import hashlib
import time
import shutil
import zipfile
import urllib.parse
from typing import Dict, Any
from app.services.fcpxml import FCPXMLExportService

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "cache", "capcut")
os.makedirs(CACHE_DIR, exist_ok=True)

class CapCutExportService:
    """ 
    Сервис экспорта проекта в родной формат черновика CapCut (draft_content.json + draft_meta_info.json) 
    и универсальный FCPXML. Упаковывает ассеты без проблем с кириллицей в путях ("неприемлемый адрес").
    """

    @classmethod
    def clean_path(cls, path_str: str) -> str:
        """ Очистка и нормализация путей для C++ парсера CapCut """
        if not path_str:
            return ""
        norm = os.path.abspath(path_str).replace("\\", "/")
        return norm

    @classmethod
    def generate_capcut_project(cls, timeline_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Генерирует готовый проект CapCut (.zip драфт с ресурсами и .fcpxml),
        полностью защищенный от ошибок пути 'неприемлемый адрес'.
        """
        title = timeline_data.get("title", "YouTube_CapCut_Project")
        total_duration = timeline_data.get("total_duration", 0.0)
        timeline = timeline_data.get("timeline", [])

        # Сначала также генерируем FCPXML для универсального импорта в CapCut
        fcpxml_res = FCPXMLExportService.generate_fcpxml(timeline_data)

        hash_input = f"{title}_{total_duration}_{len(timeline)}"
        file_hash = hashlib.md5(hash_input.encode("utf-8")).hexdigest()
        
        json_filename = f"capcut_draft_{file_hash}.json"
        json_filepath = os.path.join(CACHE_DIR, json_filename)
        
        zip_filename = f"capcut_project_{file_hash}.zip"
        zip_filepath = os.path.join(CACHE_DIR, zip_filename)

        # Создаем временную директорию сборки проекта CapCut
        project_dir = os.path.join(CACHE_DIR, f"draft_{file_hash}")
        resources_dir = os.path.join(project_dir, "resources")
        os.makedirs(resources_dir, exist_ok=True)

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

            # 1. Добавление Видео / Изображения
            v_mat_id = f"mat_video_{idx}"
            media_rel_path = ""

            if media_p and os.path.exists(media_p):
                ext = os.path.splitext(media_p)[1] or ".png"
                local_media_name = f"media_{idx}{ext}"
                local_media_path = os.path.join(resources_dir, local_media_name)
                try:
                    shutil.copy2(media_p, local_media_path)
                    media_rel_path = f"resources/{local_media_name}"
                except Exception:
                    media_rel_path = cls.clean_path(media_p)
            else:
                media_rel_path = cls.clean_path(media_p)

            videos_materials.append({
                "id": v_mat_id,
                "path": media_rel_path,
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

            # 2. Добавление Аудио озвучки
            if audio_p:
                a_mat_id = f"mat_audio_{idx}"
                audio_rel_path = ""
                if os.path.exists(audio_p):
                    ext = os.path.splitext(audio_p)[1] or ".mp3"
                    local_audio_name = f"audio_{idx}{ext}"
                    local_audio_path = os.path.join(resources_dir, local_audio_name)
                    try:
                        shutil.copy2(audio_p, local_audio_path)
                        audio_rel_path = f"resources/{local_audio_name}"
                    except Exception:
                        audio_rel_path = cls.clean_path(audio_p)
                else:
                    audio_rel_path = cls.clean_path(audio_p)

                audios_materials.append({
                    "id": a_mat_id,
                    "path": audio_rel_path,
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

        # Структура CapCut draft_content.json
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

        # Запись файлов драфта в папку проекта
        proj_json_path = os.path.join(project_dir, "draft_content.json")
        with open(proj_json_path, "w", encoding="utf-8") as f:
            json.dump(draft_content, f, ensure_ascii=False, indent=2)

        # Сохраняем также резервную копию в CACHE_DIR
        with open(json_filepath, "w", encoding="utf-8") as f:
            json.dump(draft_content, f, ensure_ascii=False, indent=2)

        draft_meta = {
            "draft_id": f"capcut_draft_{file_hash}",
            "draft_name": title,
            "draft_timeline_materials_size": len(timeline),
            "tm_draft_create": int(time.time() * 1000),
            "tm_draft_modified": int(time.time() * 1000)
        }
        proj_meta_path = os.path.join(project_dir, "draft_meta_info.json")
        with open(proj_meta_path, "w", encoding="utf-8") as f:
            json.dump(draft_meta, f, ensure_ascii=False, indent=2)

        # Создание финального ZIP архива с вложенными ассетами
        with zipfile.ZipFile(zip_filepath, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(project_dir):
                for file in files:
                    full_p = os.path.join(root, file)
                    rel_p = os.path.relpath(full_p, project_dir)
                    zipf.write(full_p, arcname=rel_p)

        # Очистка временной директории сборки
        try:
            shutil.rmtree(project_dir)
        except Exception:
            pass

        return {
            "filename": zip_filename,
            "json_filename": json_filename,
            "capcut_url": f"/api/capcut/{zip_filename}",
            "capcut_json_url": f"/api/capcut/{json_filename}",
            "fcpxml_url": fcpxml_res["fcpxml_url"],
            "capcut_path": zip_filepath
        }
