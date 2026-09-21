import os
import hashlib
import subprocess
import numpy as np
import imageio
from PIL import Image, ImageDraw
import imageio_ffmpeg
from app.models.timeline import TimelineResult

OUTPUT_DIR = os.path.join(os.getcwd(), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

class RenderService:
    """ Сервис компиляции и локального рендеринга финального MP4 видеоролика """

    @classmethod
    def render_full_video(cls, timeline: TimelineResult) -> dict:
        """
        Полная сборка фильма из с синхронизированных кадров (визуал + аудио речи)
        """
        raw_key = f"{timeline.title}_{timeline.total_duration}_{len(timeline.timeline)}".encode('utf-8')
        file_hash = hashlib.md5(raw_key).hexdigest()

        filename = f"final_video_{file_hash}.mp4"
        final_filepath = os.path.join(OUTPUT_DIR, filename)

        # 1. Проверка существования уже отрендеренного ролика
        if os.path.exists(final_filepath):
            return {
                "render_path": final_filepath,
                "filename": filename,
                "render_url": f"/api/renders/{filename}",
                "duration": timeline.total_duration,
                "cached": True
            }

        # 2. Временные рабочие файлы
        temp_video = os.path.join(OUTPUT_DIR, f"temp_video_{file_hash}.mp4")
        temp_audio = os.path.join(OUTPUT_DIR, f"temp_audio_{file_hash}.mp3")

        width, height = 1280, 720
        fps = 24

        # 3. Сборка видеоряда (Visual Stream)
        writer = imageio.get_writer(temp_video, fps=fps, codec='libx264', pixelformat='yuv420p')

        try:
            for frame in timeline.timeline:
                total_frames_for_segment = int(frame.duration * fps)
                
                # Подгрузка визуального ассета
                if frame.media_path and os.path.exists(frame.media_path):
                    if frame.media_type == "video":
                        try:
                            reader = imageio.get_reader(frame.media_path)
                            video_frames = [f for f in reader]
                            reader.close()
                        except Exception:
                            video_frames = []
                    else:
                        video_frames = []

                    if video_frames:
                        # Если видео короткое, зацикливаем его на нужную длительность
                        for i in range(total_frames_for_segment):
                            img_frame = video_frames[i % len(video_frames)]
                            img_pil = Image.fromarray(img_frame).resize((width, height))
                            writer.append_data(np.array(img_pil))
                    else:
                        base_img = Image.open(frame.media_path).convert('RGB').resize((width, height))
                        base_np = np.array(base_img)
                        for i in range(total_frames_for_segment):
                            writer.append_data(base_np)
                else:
                    # Резервный кадр с версткой текста
                    base_img = Image.new('RGB', (width, height), color='#0f172a')
                    draw = ImageDraw.Draw(base_img)
                    draw.rectangle([20, 20, width-20, height-20], outline='#38bdf8', width=3)
                    draw.text((40, 40), f"SCENE {frame.scene_number} - FRAME {frame.frame_number}", fill='#38bdf8')
                    draw.text((40, 100), f"NARRATION: {frame.narration_text[:60]}", fill='#f8fafc')
                    base_np = np.array(base_img)
                    for i in range(total_frames_for_segment):
                        writer.append_data(base_np)
        finally:
            writer.close()

        # 4. Сборка единой аудиодорожки (Audio Stream)
        audio_files = [f.audio_path for f in timeline.timeline if f.audio_path and os.path.exists(f.audio_path)]
        
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

        if audio_files:
            # Создаем список файлов для concat в FFmpeg
            concat_list_file = os.path.join(OUTPUT_DIR, f"concat_{file_hash}.txt")
            with open(concat_list_file, "w", encoding="utf-8") as f:
                for a_file in audio_files:
                    escaped_path = a_file.replace("\\", "/")
                    f.write(f"file '{escaped_path}'\n")

            # Склеиваем аудиофайлы через FFmpeg
            cmd_audio = [
                ffmpeg_exe, "-y", "-f", "concat", "-safe", "0", 
                "-i", concat_list_file, "-c", "copy", temp_audio
            ]
            subprocess.run(cmd_audio, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # Объединяем готовое видео и аудио в финальный файл
            cmd_merge = [
                ffmpeg_exe, "-y", "-i", temp_video, "-i", temp_audio,
                "-c:v", "copy", "-c:a", "aac", "-shortest", final_filepath
            ]
            subprocess.run(cmd_merge, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # Очистка временных файлов
            if os.path.exists(concat_list_file): os.remove(concat_list_file)
            if os.path.exists(temp_audio): os.remove(temp_audio)
        else:
            # Если звука нет, просто переименовываем сгенерированное видео
            os.replace(temp_video, final_filepath)

        if os.path.exists(temp_video): os.remove(temp_video)

        return {
            "render_path": final_filepath,
            "filename": filename,
            "render_url": f"/api/renders/{filename}",
            "duration": timeline.total_duration,
            "cached": False
        }
