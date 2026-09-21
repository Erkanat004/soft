import os
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from app.models.script import ScriptParseResult
from app.models.timeline import TimelineResult, CostSummaryResponse
from app.services.parser import ScriptParser
from app.services.tts import TTSService, CACHE_DIR as AUDIO_CACHE_DIR
from app.services.image_gen import ImageGenerationService, CACHE_DIR as IMAGE_CACHE_DIR
from app.services.video_gen import VideoGenerationService, CACHE_DIR as VIDEO_CACHE_DIR
from app.services.sync import SyncService
from app.services.subtitles import SubtitleService, CACHE_DIR as SUBTITLE_CACHE_DIR
from app.services.renderer import RenderService, OUTPUT_DIR as RENDER_OUTPUT_DIR
from app.services.state import StateManager
from app.services.cost_tracker import CostTrackerService
from app.services.batch_async import BatchAsyncService
from app.services.voice_library import VoiceLibraryService
from app.services.fcpxml import FCPXMLExportService, CACHE_DIR as FCPXML_CACHE_DIR
from app.services.logger import AppLogger
from app.services.settings import SettingsService

router = APIRouter(prefix="/api", tags=["API Endpoints"])

class TextParseRequest(BaseModel):
    text: str
    title: Optional[str] = "Сценарий"

class TTSGenerateRequest(BaseModel):
    text: str
    voice: Optional[str] = "ru-RU-DmitryNeural"
    frame_id: Optional[str] = None
    force: Optional[bool] = False

class TTSGenerateResponse(BaseModel):
    frame_id: Optional[str] = None
    audio_url: str
    filename: str
    duration: float
    cached: bool

class ImageGenerateRequest(BaseModel):
    prompt: str
    frame_id: Optional[str] = None
    width: Optional[int] = 1280
    height: Optional[int] = 720

class ImageGenerateResponse(BaseModel):
    frame_id: Optional[str] = None
    image_url: str
    filename: str
    cached: bool

class VideoGenerateRequest(BaseModel):
    prompt: str
    image_path: Optional[str] = ""
    frame_id: Optional[str] = None
    duration: Optional[float] = 3.0

class VideoGenerateResponse(BaseModel):
    frame_id: Optional[str] = None
    video_url: str
    filename: str
    duration: float
    cached: bool

class SubtitleGenerateResponse(BaseModel):
    srt_url: str
    vtt_url: str
    srt_filename: str
    vtt_filename: str
    srt_content: str
    vtt_content: str

class FullVideoRenderResponse(BaseModel):
    render_url: str
    filename: str
    duration: float
    cached: bool

@router.post("/parse-text", response_model=ScriptParseResult)
def parse_raw_text(request: TextParseRequest):
    """ Разбор сырого текста сценария """
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Текст сценария не может быть пустым")
    
    parsed = ScriptParser.parse_text_to_script(
        raw_text=request.text, 
        default_title=request.title or "Сценарий"
    )
    StateManager.save_state(parsed.model_dump())
    return parsed

@router.post("/upload-script", response_model=ScriptParseResult)
async def upload_script_file(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None)
):
    """ Загрузка и парсинг файлов .txt или .docx """
    filename = file.filename or "script.txt"
    content_bytes = await file.read()

    if filename.endswith(".docx"):
        text = ScriptParser.parse_docx_bytes(content_bytes)
    elif filename.endswith(".txt") or filename.endswith(".md"):
        text = ScriptParser.parse_txt_bytes(content_bytes)
    else:
        raise HTTPException(
            status_code=400, 
            detail=f"Неподдерживаемый формат файла '{filename}'. Разрешены файлы .txt и .docx"
        )

    script_title = title or filename.rsplit(".", 1)[0]
    parsed = ScriptParser.parse_text_to_script(raw_text=text, default_title=script_title)
    StateManager.save_state(parsed.model_dump())
    return parsed

@router.post("/tts/generate", response_model=TTSGenerateResponse)
async def generate_tts_audio(request: TTSGenerateRequest):
    """ Генерация речи для фрагмента текста с использованием кэша """
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Текст для озвучки не может быть пустым")

    try:
        res = await TTSService.generate_speech(
            text=request.text, 
            voice=request.voice or TTSService.DEFAULT_VOICE,
            force=bool(request.force)
        )
        return TTSGenerateResponse(
            frame_id=request.frame_id,
            audio_url=f"/api/audio/{res['filename']}",
            filename=res["filename"],
            duration=res["duration"],
            cached=res["cached"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка генерации TTS: {str(e)}")

@router.get("/audio/{filename}")
def get_audio_file(filename: str):
    """ Эндпоинт отсылки кэшированного звукового файла """
    file_path = os.path.join(AUDIO_CACHE_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Аудиофайл не найден")
    return FileResponse(file_path, media_type="audio/mpeg")

@router.post("/image/generate", response_model=ImageGenerateResponse)
def generate_image(request: ImageGenerateRequest):
    """ Генерация изображения по визуальному промпту кадра """
    if not request.prompt or not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Промпт для изображения не может быть пустым")

    try:
        res = StateManager.execute_with_fallback(
            primary_fn=lambda: ImageGenerationService.generate_image(
                prompt=request.prompt,
                width=request.width or 1280,
                height=request.height or 720
            ),
            fallback_fn=lambda: ImageGenerationService.generate_image(
                prompt=request.prompt,
                width=request.width or 1280,
                height=request.height or 720
            ),
            provider_name="Primary Image Generator API"
        )
        return ImageGenerateResponse(
            frame_id=request.frame_id,
            image_url=f"/api/images/{res['filename']}",
            filename=res["filename"],
            cached=res["cached"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка генерации картинки: {str(e)}")

@router.get("/images/{filename}")
def get_image_file(filename: str):
    """ Эндпоинт отсылки кэшированного изображения """
    file_path = os.path.join(IMAGE_CACHE_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Изображение не найдено")
    return FileResponse(file_path, media_type="image/png")

@router.post("/video/generate", response_model=VideoGenerateResponse)
def generate_video(request: VideoGenerateRequest):
    """ Генерация анимационного видеоклипа MP4 по кадру """
    try:
        res = StateManager.execute_with_fallback(
            primary_fn=lambda: VideoGenerationService.generate_video(
                prompt=request.prompt,
                image_path=request.image_path or "",
                duration=request.duration or 3.0
            ),
            fallback_fn=lambda: VideoGenerationService.generate_video(
                prompt=request.prompt,
                image_path=request.image_path or "",
                duration=request.duration or 3.0
            ),
            provider_name="Primary Video Generator API"
        )
        return VideoGenerateResponse(
            frame_id=request.frame_id,
            video_url=f"/api/videos/{res['filename']}",
            filename=res["filename"],
            duration=res["duration"],
            cached=res["cached"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка генерации видео: {str(e)}")

@router.get("/videos/{filename}")
def get_video_file(filename: str):
    """ Эндпоинт отсылки кэшированного видеофайла MP4 """
    file_path = os.path.join(VIDEO_CACHE_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Видеофайл не найден")
    return FileResponse(file_path, media_type="video/mp4")

@router.post("/timeline/sync", response_model=TimelineResult)
def sync_timeline(script: ScriptParseResult):
    """ Синхронизация звука с картинками и построение таймлайна проекта """
    try:
        return SyncService.sync_script(script)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка синхронизации таймлайна: {str(e)}")

@router.post("/subtitles/generate", response_model=SubtitleGenerateResponse)
def generate_subtitles(timeline: TimelineResult):
    """ Генерация субтитров SRT и VTT по таймлайну проекта """
    try:
        res = SubtitleService.generate_subtitles(timeline)
        return SubtitleGenerateResponse(
            srt_url=res["srt_url"],
            vtt_url=res["vtt_url"],
            srt_filename=res["srt_filename"],
            vtt_filename=res["vtt_filename"],
            srt_content=res["srt_content"],
            vtt_content=res["vtt_content"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка генерации субтитров: {str(e)}")

@router.get("/subtitles/{filename}")
def get_subtitle_file(filename: str):
    """ Эндпоинт отсылки локального файла субтитров """
    file_path = os.path.join(SUBTITLE_CACHE_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Файл субтитров не найден")
    media_type = "text/vtt" if filename.endswith(".vtt") else "text/plain"
    return FileResponse(file_path, media_type=media_type)

@router.post("/render/full-video", response_model=FullVideoRenderResponse)
def render_full_video(timeline: TimelineResult):
    """ Локальный рендер и экспортирование финального фильма в MP4 """
    try:
        res = RenderService.render_full_video(timeline)
        return FullVideoRenderResponse(
            render_url=res["render_url"],
            filename=res["filename"],
            duration=res["duration"],
            cached=res["cached"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка финального рендеринга: {str(e)}")

@router.get("/renders/{filename}")
def get_rendered_video(filename: str):
    """ Эндпоинт отсылки готового скомпилированного роликов MP4 """
    file_path = os.path.join(RENDER_OUTPUT_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Скомпилированный файл не найден")
    return FileResponse(file_path, media_type="video/mp4")

@router.get("/project/state")
def get_project_state():
    """ Получение сохраненного состояния проекта """
    return StateManager.load_state()

@router.post("/project/save")
def save_project_state(project_data: Dict[str, Any]):
    """ Сохранение текущего состояния проекта """
    path = StateManager.save_state(project_data)
    return {"status": "ok", "saved_file": path}

@router.post("/cost/calculate", response_model=CostSummaryResponse)
def calculate_project_cost(script_data: Dict[str, Any]):
    """ Расчет финансовой сметы и экономии кэша для проекта """
    try:
        cost_info = CostTrackerService.calculate_script_cost(script_data)
        return CostSummaryResponse(**cost_info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка расчета сметы: {str(e)}")

class BatchTTSItem(BaseModel):
    frame_id: str
    text: str

class BatchTTSRequest(BaseModel):
    items: List[BatchTTSItem]
    voice: Optional[str] = "ru-RU-DmitryNeural"
    max_concurrency: Optional[int] = 4
    force: Optional[bool] = False

class BatchPromptItem(BaseModel):
    frame_id: str
    prompt: str

class BatchImageRequest(BaseModel):
    items: List[BatchPromptItem]
    max_concurrency: Optional[int] = 3

class BatchVideoRequest(BaseModel):
    items: List[BatchPromptItem]
    duration: Optional[float] = 3.0
    max_concurrency: Optional[int] = 2

@router.post("/batch/tts")
async def batch_generate_tts(request: BatchTTSRequest):
    """ Пакетная параллельная генерация озвучки для списка кадров """
    items = [item.model_dump() for item in request.items]
    return await BatchAsyncService.generate_tts_batch(
        items=items, 
        voice=request.voice or "ru-RU-DmitryNeural", 
        max_concurrency=request.max_concurrency or 4,
        force=bool(request.force)
    )

@router.post("/batch/images")
async def batch_generate_images(request: BatchImageRequest):
    """ Пакетная параллельная генерация иллюстраций """
    items = [item.model_dump() for item in request.items]
    return await BatchAsyncService.generate_images_batch(
        items=items, 
        max_concurrency=request.max_concurrency or 3
    )

@router.post("/batch/videos")
async def batch_generate_videos(request: BatchVideoRequest):
    """ Пакетная параллельная генерация видео клипов """
    items = [item.model_dump() for item in request.items]
    return await BatchAsyncService.generate_videos_batch(
        items=items, 
        duration=request.duration or 3.0, 
        max_concurrency=request.max_concurrency or 2
    )

class VoicePresetRequest(BaseModel):
    voice_id: str

@router.get("/voices")
def get_available_voices():
    """ Получение доступных дикторских голосов Edge-TTS """
    return {"voices": VoiceLibraryService.get_available_voices()}

@router.post("/voice/preset")
def set_voice_preset(request: VoicePresetRequest):
    """ Валидация и выбор пресета диктора """
    selected_voice = VoiceLibraryService.validate_voice(request.voice_id)
    return {"status": "ok", "selected_voice": selected_voice}

@router.post("/export/fcpxml")
def export_fcpxml(timeline_data: Dict[str, Any]):
    """ Генерация XML файла экспорта для DaVinci Resolve / Premiere Pro """
    try:
        return FCPXMLExportService.generate_fcpxml(timeline_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка экспорта FCPXML: {str(e)}")

@router.get("/fcpxml/{filename}")
def get_fcpxml_file(filename: str):
    """ Отдача сгенерированного файла FCPXML для скачивания """
    file_path = os.path.join(FCPXML_CACHE_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Файл FCPXML не найден")
    return FileResponse(file_path, media_type="application/xml", filename=filename)

@router.get("/system/logs")
def get_system_diagnostics():
    """ Диагностика состояния подсистем бэкенда """
    return {
        "status": "healthy",
        "audio_cache_count": len(os.listdir(AUDIO_CACHE_DIR)) if os.path.exists(AUDIO_CACHE_DIR) else 0,
        "image_cache_count": len(os.listdir(IMAGE_CACHE_DIR)) if os.path.exists(IMAGE_CACHE_DIR) else 0,
        "video_cache_count": len(os.listdir(VIDEO_CACHE_DIR)) if os.path.exists(VIDEO_CACHE_DIR) else 0,
        "render_count": len(os.listdir(RENDER_OUTPUT_DIR)) if os.path.exists(RENDER_OUTPUT_DIR) else 0
    }

class SaveSettingsRequest(BaseModel):
    openai_api_key: Optional[str] = None
    replicate_api_key: Optional[str] = None
    elevenlabs_api_key: Optional[str] = None
    image_provider: Optional[str] = None

@router.get("/system/settings")
def get_system_settings():
    """ Получение текущего состояния ключей и статуса МОК-режима """
    return SettingsService.get_settings()

@router.post("/system/settings")
def save_system_settings(request: SaveSettingsRequest):
    """ Сохранение ключей, обновление переменных окружения и автоматическое отключение МОК-режима """
    return SettingsService.save_settings(
        openai_key=request.openai_api_key,
        replicate_key=request.replicate_api_key,
        elevenlabs_key=request.elevenlabs_api_key,
        image_provider=request.image_provider
    )

@router.get("/system/file-logs")
def get_system_file_logs(limit: Optional[int] = 100):
    """ Получение содержимого ротируемых текстовых файлов логов app.log и error.log """
    return AppLogger.read_file_logs(limit=limit or 100)
