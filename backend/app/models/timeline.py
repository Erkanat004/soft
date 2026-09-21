from typing import List, Optional
from pydantic import BaseModel, Field

class TimelineFrame(BaseModel):
    frame_id: str = Field(..., description="ID кадра")
    scene_number: int = Field(..., description="Номер сцены")
    frame_number: int = Field(..., description="Номер кадра")
    start_time: float = Field(..., description="Время начала кадра в секундах")
    end_time: float = Field(..., description="Время окончания кадра в секундах")
    duration: float = Field(..., description="Длительность кадра в секундах")
    formatted_start: str = Field(..., description="Форматированное время начала (00:00.0)")
    formatted_end: str = Field(..., description="Форматированное время окончания (00:06.5)")
    narration_text: str = Field(..., description="Текст диктора")
    visual_prompt: str = Field(..., description="Промпт визуала")
    audio_path: Optional[str] = Field(default=None, description="Путь к аудиофайлу речи")
    media_path: Optional[str] = Field(default=None, description="Путь к файлу медиа (картинка или видео)")
    media_type: str = Field(default="image", description="Тип визуала: image или video")

class TimelineResult(BaseModel):
    title: str = Field(..., description="Название проекта")
    total_duration: float = Field(..., description="Общая длительность роликов в секундах")
    formatted_total_duration: str = Field(..., description="Красивый хронометраж (MM:SS)")
    total_scenes: int = Field(..., description="Общее кол-во сцен")
    total_frames: int = Field(..., description="Общее кол-во кадров")
    timeline: List[TimelineFrame] = Field(default_factory=list, description="Покадровый таймлайн")

class CostSummaryResponse(BaseModel):
    total_chars: int = Field(default=0, description="Общее количество символов озвучки")
    total_images: int = Field(default=0, description="Количество изображений")
    total_videos: int = Field(default=0, description="Количество видеоклипов")
    tts_cost: float = Field(default=0.0, description="Стоимость TTS в USD")
    image_cost: float = Field(default=0.0, description="Стоимость иллюстраций в USD")
    video_cost: float = Field(default=0.0, description="Стоимость анимации в USD")
    total_estimated_cost: float = Field(default=0.0, description="Полная оценка бюджета в USD")
    actual_cost: float = Field(default=0.0, description="Фактическая стоимость с учетом кэширования")
    cache_savings: float = Field(default=0.0, description="Сэкономлено бюджета благодаря кэшу в USD")
    cached_count: int = Field(default=0, description="Количество кэшированных элементов")
    total_items_count: int = Field(default=0, description="Всего элементов в проекте")

