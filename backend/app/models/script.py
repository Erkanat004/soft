from typing import List, Optional
from pydantic import BaseModel, Field

class Frame(BaseModel):
    frame_id: str = Field(..., description="Уникальный ID кадра (scene_1_frame_1)")
    scene_number: int = Field(..., description="Номер сцены")
    frame_number: int = Field(..., description="Номер кадра в сцене")
    narration_text: str = Field(..., description="Текст озвучки для TTS")
    visual_prompt: str = Field(..., description="Промпт для генерации картинки или видео")
    duration: float = Field(default=0.0, description="Длительность кадра в секундах")
    audio_path: Optional[str] = Field(default=None, description="Путь к сгенерированному файлу озвучки")
    image_path: Optional[str] = Field(default=None, description="Путь к сгенерированному изображению")
    video_path: Optional[str] = Field(default=None, description="Путь к сгенерированному видеоролику")

class Scene(BaseModel):
    scene_id: str = Field(..., description="Уникальный ID сцены (scene_1)")
    scene_number: int = Field(..., description="Порядковый номер сцены")
    title: str = Field(default="", description="Название или заголовок сцены")
    frames: List[Frame] = Field(default_factory=list, description="Кадры этой сцены")

class ScriptParseResult(BaseModel):
    title: str = Field(default="Сценарий без названия", description="Название сценария")
    scenes: List[Scene] = Field(default_factory=list, description="Список сцен")
    total_scenes: int = Field(default=0, description="Общее количество сцен")
    total_frames: int = Field(default=0, description="Общее количество кадров")
    raw_text: str = Field(default="", description="Исходный текст сценария")
