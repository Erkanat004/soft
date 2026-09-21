import os
import hashlib
from app.models.timeline import TimelineResult, TimelineFrame

CACHE_DIR = os.path.join(os.getcwd(), "cache", "subtitles")
os.makedirs(CACHE_DIR, exist_ok=True)

class SubtitleService:
    """ Сервис генерации субтитров формата SRT и WebVTT """

    @classmethod
    def generate_subtitles(cls, timeline: TimelineResult) -> dict:
        """
        Формирование файлов .srt и .vtt на основе единого монтажного таймлайна проекта
        """
        raw_key = f"{timeline.title}_{timeline.total_duration}_{len(timeline.timeline)}".encode('utf-8')
        file_hash = hashlib.md5(raw_key).hexdigest()

        srt_filename = f"{file_hash}.srt"
        vtt_filename = f"{file_hash}.vtt"

        srt_path = os.path.join(CACHE_DIR, srt_filename)
        vtt_path = os.path.join(CACHE_DIR, vtt_filename)

        # 1. Сборка текстов субтитров
        srt_content = cls._build_srt(timeline.timeline)
        vtt_content = cls._build_vtt(timeline.timeline)

        # 2. Сохранение в файловую систему
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(srt_content)

        with open(vtt_path, "w", encoding="utf-8") as f:
            f.write(vtt_content)

        return {
            "srt_path": srt_path,
            "vtt_path": vtt_path,
            "srt_filename": srt_filename,
            "vtt_filename": vtt_filename,
            "srt_url": f"/api/subtitles/{srt_filename}",
            "vtt_url": f"/api/subtitles/{vtt_filename}",
            "srt_content": srt_content,
            "vtt_content": vtt_content
        }

    @classmethod
    def _build_srt(cls, frames: list[TimelineFrame]) -> str:
        """ Сборка текста формата SRT ( SubRip ) """
        blocks = []
        for idx, frame in enumerate(frames, start=1):
            if not frame.narration_text.strip():
                continue
            start_tc = cls._format_srt_timecode(frame.start_time)
            end_tc = cls._format_srt_timecode(frame.end_time)
            blocks.append(f"{idx}\n{start_tc} --> {end_tc}\n{frame.narration_text.strip()}\n")
        return "\n".join(blocks)

    @classmethod
    def _build_vtt(cls, frames: list[TimelineFrame]) -> str:
        """ Сборка текста формата WebVTT """
        blocks = ["WEBVTT\n"]
        for idx, frame in enumerate(frames, start=1):
            if not frame.narration_text.strip():
                continue
            start_tc = cls._format_vtt_timecode(frame.start_time)
            end_tc = cls._format_vtt_timecode(frame.end_time)
            blocks.append(f"{idx}\n{start_tc} --> {end_tc}\n{frame.narration_text.strip()}\n")
        return "\n".join(blocks)

    @staticmethod
    def _format_srt_timecode(seconds: float) -> str:
        """ Преобразование секунд в формат SRT (HH:MM:SS,mmm) """
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int(round((seconds - int(seconds)) * 1000))
        return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"

    @staticmethod
    def _format_vtt_timecode(seconds: float) -> str:
        """ Преобразование секунд в формат WebVTT (HH:MM:SS.mmm) """
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int(round((seconds - int(seconds)) * 1000))
        return f"{hrs:02d}:{mins:02d}:{secs:02d}.{millis:03d}"
