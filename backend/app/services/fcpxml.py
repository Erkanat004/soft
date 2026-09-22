import os
import hashlib
import urllib.parse
import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import Dict, Any

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "cache", "fcpxml")
os.makedirs(CACHE_DIR, exist_ok=True)

class FCPXMLExportService:
    @classmethod
    def clean_file_uri(cls, filepath: str) -> str:
        """ Формирует валидный URI формата file:///C:/path со сбеганием кириллицы и спецсимволов """
        abs_p = os.path.abspath(filepath).replace("\\", "/")
        encoded_p = urllib.parse.quote(abs_p, safe="/:")
        return f"file:///{encoded_p}"

    @classmethod
    def generate_fcpxml(cls, timeline_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Формирует профессиональный документ FCPXML (v1.8) для импорта 
        в CapCut, DaVinci Resolve, Adobe Premiere Pro или Final Cut Pro X.
        """
        title = timeline_data.get("title", "YouTube_Project")
        total_duration = timeline_data.get("total_duration", 0.0)
        timeline = timeline_data.get("timeline", [])

        # Хэш содержимого для кэширования файла экспорта
        hash_input = f"{title}_{total_duration}_{len(timeline)}"
        file_hash = hashlib.md5(hash_input.encode("utf-8")).hexdigest()
        filename = f"export_{file_hash}.fcpxml"
        file_path = os.path.join(CACHE_DIR, filename)

        fcpxml = ET.Element("fcpxml", version="1.8")
        
        # Ресурсы
        resources = ET.SubElement(fcpxml, "resources")
        ET.SubElement(
            resources, "format", 
            id="r1", 
            name="FFVideoFormat1080p24", 
            frameDuration="100/2400s", 
            width="1920", 
            height="1080"
        )

        asset_counter = 1
        asset_map = {}

        # Создаем ресурсы ассетов для файлов
        for tf in timeline:
            audio_p = tf.get("audio_path")
            media_p = tf.get("media_path")
            
            if audio_p and audio_p not in asset_map and os.path.exists(audio_p):
                aid = f"a{asset_counter}"
                asset_counter += 1
                asset_map[audio_p] = aid
                src_uri = cls.clean_file_uri(audio_p)
                ET.SubElement(
                    resources, "asset",
                    id=aid,
                    name=os.path.basename(audio_p),
                    src=src_uri,
                    duration=f"{tf.get('duration', 3.0):.2f}s",
                    hasAudio="1"
                )

            if media_p and media_p not in asset_map and os.path.exists(media_p):
                aid = f"a{asset_counter}"
                asset_counter += 1
                asset_map[media_p] = aid
                src_uri = cls.clean_file_uri(media_p)
                is_video = "1" if tf.get("media_type") == "video" else "0"
                ET.SubElement(
                    resources, "asset",
                    id=aid,
                    name=os.path.basename(media_p),
                    src=src_uri,
                    duration=f"{tf.get('duration', 3.0):.2f}s",
                    hasVideo="1",
                    hasAudio=is_video
                )

        # Иерархия проектов Library / Event / Project / Sequence / Spine
        library = ET.SubElement(fcpxml, "library")
        event = ET.SubElement(library, "event", name=title)
        project = ET.SubElement(event, "project", name=title)
        sequence = ET.SubElement(
            project, "sequence", 
            format="r1", 
            duration=f"{total_duration:.2f}s",
            tcStart="0s"
        )
        spine = ET.SubElement(sequence, "spine")

        # Добавляем элементы таймлайна
        current_offset = 0.0
        for tf in timeline:
            dur = tf.get("duration", 3.0)
            offset_str = f"{current_offset:.2f}s"
            dur_str = f"{dur:.2f}s"

            frame_id = tf.get("frame_id", "frame")
            media_p = tf.get("media_path")
            audio_p = tf.get("audio_path")

            if media_p and media_p in asset_map:
                asset_clip = ET.SubElement(
                    spine, "asset-clip",
                    name=f"Clip_{frame_id}",
                    ref=asset_map[media_p],
                    offset=offset_str,
                    duration=dur_str,
                    start="0s"
                )
            else:
                asset_clip = ET.SubElement(
                    spine, "gap",
                    name=f"Gap_{frame_id}",
                    offset=offset_str,
                    duration=dur_str,
                    start="0s"
                )

            # Вложенный звуковой трек речи
            if audio_p and audio_p in asset_map:
                ET.SubElement(
                    asset_clip, "asset-clip",
                    name=f"Audio_{frame_id}",
                    ref=asset_map[audio_p],
                    offset="0s",
                    duration=dur_str,
                    start="0s",
                    lane="-1"
                )

            current_offset += dur

        # Сериализация XML с красивыми отступами
        xml_str = ET.tostring(fcpxml, encoding="utf-8")
        parsed_xml = minidom.parseString(xml_str)
        pretty_xml = parsed_xml.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(pretty_xml)

        return {
            "filename": filename,
            "fcpxml_path": file_path,
            "fcpxml_url": f"/api/fcpxml/{filename}",
            "xml_content": pretty_xml
        }
