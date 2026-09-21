import os
from typing import List
from app.models.script import ScriptParseResult, Frame
from app.models.timeline import TimelineFrame, TimelineResult
from app.services.tts import TTSService, CACHE_DIR as AUDIO_CACHE_DIR
from app.services.image_gen import ImageGenerationService, CACHE_DIR as IMAGE_CACHE_DIR
from app.services.video_gen import VideoGenerationService, CACHE_DIR as VIDEO_CACHE_DIR

class SyncService:
    """ Сервис автоматической синхронизации звука с визукалом и расчета монтажной шкалы """

    @classmethod
    def sync_script(cls, script: ScriptParseResult) -> TimelineResult:
        """
        Расчет точно сбалансированного таймлайна проекта.
        Длительность визуала кадра приравнивается к длительности озвучки речи (TTS).
        """
        timeline_frames: List[TimelineFrame] = []
        current_cursor = 0.0

        for scene in script.scenes:
            for frame in scene.frames:
                # 1. Определение файла и длительности озвучки
                audio_hash = TTSService.get_audio_hash(frame.narration_text, TTSService.DEFAULT_VOICE)
                audio_filename = f"{audio_hash}.mp3"
                audio_filepath = os.path.join(AUDIO_CACHE_DIR, audio_filename)

                if os.path.exists(audio_filepath):
                    duration = TTSService.get_audio_duration(audio_filepath)
                    audio_path = audio_filepath
                else:
                    # Если озвучка еще не была сгенерирована, вычисляем приближенную длительность (14 символов/сек)
                    char_count = len(frame.narration_text.strip())
                    duration = max(2.5, round(char_count / 14.0, 2))
                    audio_path = None

                # 2. Определение наличия визуала (видео клип приоритетнее статичной картинки)
                video_hash = VideoGenerationService.get_video_hash(frame.visual_prompt, duration=duration)
                video_filename = f"{video_hash}.mp4"
                video_filepath = os.path.join(VIDEO_CACHE_DIR, video_filename)

                image_hash = ImageGenerationService.get_image_hash(frame.visual_prompt)
                image_filename = f"{image_hash}.png"
                image_filepath = os.path.join(IMAGE_CACHE_DIR, image_filename)

                if os.path.exists(video_filepath):
                    media_path = video_filepath
                    media_type = "video"
                elif os.path.exists(image_filepath):
                    media_path = image_filepath
                    media_type = "image"
                else:
                    media_path = None
                    media_type = "image"

                # 3. Вычисление временных меток
                start_time = round(current_cursor, 2)
                end_time = round(current_cursor + duration, 2)
                current_cursor += duration

                timeline_frames.append(TimelineFrame(
                    frame_id=frame.frame_id,
                    scene_number=scene.scene_number,
                    frame_number=frame.frame_number,
                    start_time=start_time,
                    end_time=end_time,
                    duration=round(duration, 2),
                    formatted_start=cls._format_timecode(start_time),
                    formatted_end=cls._format_timecode(end_time),
                    narration_text=frame.narration_text,
                    visual_prompt=frame.visual_prompt,
                    audio_path=audio_path,
                    media_path=media_path,
                    media_type=media_type
                ))

        total_duration = round(current_cursor, 2)
        return TimelineResult(
            title=script.title,
            total_duration=total_duration,
            formatted_total_duration=cls._format_timecode(total_duration),
            total_scenes=script.total_scenes,
            total_frames=script.total_frames,
            timeline=timeline_frames
        )

    @staticmethod
    def _format_timecode(seconds: float) -> str:
        """ Преобразование секунд в формат MM:SS.S (например 01:14.5) """
        mins = int(seconds // 60)
        secs = seconds % 60
        return f"{mins:02d}:{secs:04.1f}"
