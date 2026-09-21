import re
from io import BytesIO
from typing import List, Tuple
import docx
from app.models.script import ScriptParseResult, Scene, Frame

class ScriptParser:
    """ Сервис распарсивания сценариев из TXT и DOCX в структуру Сцен и Кадров """

    @staticmethod
    def parse_docx_bytes(file_bytes: bytes) -> str:
        """ Извлечение текста из байтов .docx файла """
        doc = docx.Document(BytesIO(file_bytes))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(paragraphs)

    @staticmethod
    def parse_txt_bytes(file_bytes: bytes) -> str:
        """ Извлечение текста из байтов .txt файла с учетом кодировки """
        try:
            return file_bytes.decode('utf-8')
        except UnicodeDecodeError:
            return file_bytes.decode('cp1251', errors='ignore')

    @classmethod
    def parse_text_to_script(cls, raw_text: str, default_title: str = "Новый Сценарий") -> ScriptParseResult:
        """ 
        Универсальный метод разбора текста на Сцены и Кадры.
        Поддерживает разбор как специально размеченного текста, так и свободного.
        """
        raw_text_clean = raw_text.strip()
        if not raw_text_clean:
            return ScriptParseResult(title=default_title, scenes=[], total_scenes=0, total_frames=0, raw_text="")

        # Попытка извлечь название сценария (первая строка, если это не метка сцены)
        lines = [line.strip() for line in raw_text_clean.split("\n") if line.strip()]
        title = default_title
        if lines and not re.match(r'^(сцена|scene|\[сцена|\[scene|\d+\.)', lines[0], re.IGNORECASE):
            title = lines[0]

        # 1. Проверяем, есть ли явная разметка сцен (Сцена X / Scene X / [Сцена X])
        scene_blocks = cls._split_into_scene_blocks(raw_text_clean)

        scenes: List[Scene] = []
        total_frames_count = 0

        for scene_idx, (scene_title, block_text) in enumerate(scene_blocks, start=1):
            scene_id = f"scene_{scene_idx}"
            frames = cls._parse_frames_from_block(scene_idx, block_text)
            
            if frames:
                scenes.append(Scene(
                    scene_id=scene_id,
                    scene_number=scene_idx,
                    title=scene_title or f"Сцена {scene_idx}",
                    frames=frames
                ))
                total_frames_count += len(frames)

        return ScriptParseResult(
            title=title,
            scenes=scenes,
            total_scenes=len(scenes),
            total_frames=total_frames_count,
            raw_text=raw_text_clean
        )

    @classmethod
    def _split_into_scene_blocks(cls, text: str) -> List[Tuple[str, str]]:
        """ Разделение текста по заголовкам сцен """
        # Ищем паттерны вида: Сцена 1, Scene 1, [Сцена 1: Описание]
        scene_pattern = re.compile(
            r'^(?:\[?\s*(?:Сцена|Scene)\s*(\d+)[\:\.\s]*(.*?)\]?)$', 
            re.IGNORECASE | re.MULTILINE
        )

        matches = list(scene_pattern.finditer(text))
        if not matches:
            # Если явных меток сцен нет, делим весь текст на 1 сцену или по пустым строкам
            paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
            if len(paragraphs) > 4:
                # Если параграфов много, группируем по 2 параграфа в сцену
                blocks = []
                for i in range(0, len(paragraphs), 2):
                    scene_num = (i // 2) + 1
                    block_content = "\n".join(paragraphs[i:i+2])
                    blocks.append((f"Сцена {scene_num}", block_content))
                return blocks
            else:
                return [("Сцена 1", text)]

        blocks = []
        for i, match in enumerate(matches):
            scene_num = match.group(1)
            scene_header = match.group(2).strip() or f"Сцена {scene_num}"
            start_pos = match.end()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            block_text = text[start_pos:end_pos].strip()
            blocks.append((scene_header, block_text))

        return blocks

    @classmethod
    def _parse_frames_from_block(cls, scene_num: int, block_text: str) -> List[Frame]:
        """ Разбор блока сцены на отдельные кадры """
        frames: List[Frame] = []
        
        # Проверяем наличие меток "Кадр" или "Промпт/Озвучка"
        frame_pattern = re.compile(
            r'(?:\[?\s*(?:Кадр|Frame)\s*\d+[\:\.\s]*\]?|(?=\[(?:Визуал|Промпт|Озвучка|Prompt|Visual|Audio)[\:\s]))',
            re.IGNORECASE
        )
        
        raw_chunks = [c.strip() for c in frame_pattern.split(block_text) if c.strip()]
        
        if not raw_chunks:
            raw_chunks = [block_text]

        frame_idx = 1
        for chunk in raw_chunks:
            # Ищем пары (Визуал/Промпт, Озвучка/Текст)
            visual_prompt = cls._extract_field(chunk, [r'визуал', r'промпт', r'prompt', r'visual', r'картинка'])
            narration_text = cls._extract_field(chunk, [r'озвучка', r'текст', r'audio', r'narration', r'диктор'])

            # Если явных полей нет, используем весь кусок как озвучку, а промпт формируем автоматически
            if not narration_text and not visual_prompt:
                lines = [l.strip() for l in chunk.split("\n") if l.strip()]
                narration_text = " ".join(lines)
                visual_prompt = f"High quality cinematic shot illustrating: {narration_text[:100]}"
            elif not visual_prompt:
                visual_prompt = f"Cinematic scene representing: {narration_text[:100]}"
            elif not narration_text:
                narration_text = visual_prompt

            if narration_text.strip():
                frame_id = f"scene_{scene_num}_frame_{frame_idx}"
                frames.append(Frame(
                    frame_id=frame_id,
                    scene_number=scene_num,
                    frame_number=frame_idx,
                    narration_text=narration_text,
                    visual_prompt=visual_prompt
                ))
                frame_idx += 1

        return frames

    @staticmethod
    def _extract_field(text: str, keywords: List[str]) -> str:
        """ Извлечение значения поля по ключевым словам (например, Визуал: ...) """
        for kw in keywords:
            pattern = re.compile(rf'(?:\[?\s*{kw}\s*[\:\=]\s*\]?)(.*?)(?=\n\[?\s*(?:визуал|промпт|озвучка|текст|кадр|сцена)|$)', re.IGNORECASE | re.DOTALL)
            match = pattern.search(text)
            if match:
                return match.group(1).strip()
        return ""
