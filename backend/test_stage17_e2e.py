import sys
import os
import time

# UTF-8 encoding fix for Windows terminal output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def run_end_to_end_test():
    print("==================================================================")
    print(" 🧪 [E2E TEST] Сквозное интеграционное тестирование приложения")
    print("==================================================================")

    # ------------------------------------------------------------------
    # ФАЗА 1: Парсинг реального сценария
    # ------------------------------------------------------------------
    print("\n[ФАЗА 1/8] Отправка и распарсивание полного текста сценария...")
    raw_script_text = """
Сцена 1: Исследование глубокого космоса
[Кадр 1]
Визуал: Галактика с миллиардами ярких звезд и туманностей
Озвучка: Вселенная таит в себе бесконечное множество тайн и удивительных открытий.

[Кадр 2]
Визуал: Футуристический космический телескоп на орбите
Озвучка: Современные астрономы используют новейшие технологии для наблюдения за далекими мирами.

Сцена 2: Будущее искусственного интеллекта
[Кадр 3]
Визуал: Нейросеть с светящимися узлами и цифровыми связями
Озвучка: Искусственный интеллект кардинально меняет подход к созданию контента и анализу данных.
    """.strip()

    parse_resp = client.post("/api/parse-text", json={"text": raw_script_text, "title": "Космос и ИИ"})
    assert parse_resp.status_code == 200, f"Ошибка парсинга: {parse_resp.text}"
    script_data = parse_resp.json()
    
    total_scenes = script_data["total_scenes"]
    total_frames = script_data["total_frames"]
    print(f"✅ Сценарий распарсен! Сцен: {total_scenes}, Кадров: {total_frames}")
    assert total_scenes == 2
    assert total_frames == 3

    # ------------------------------------------------------------------
    # ФАЗА 2: Пакетная параллельная генерация речи (TTS)
    # ------------------------------------------------------------------
    print("\n[ФАЗА 2/8] Пакетная параллельная генерация дикторской озвучки...")
    tts_items = []
    for scene in script_data["scenes"]:
        for frame in scene["frames"]:
            tts_items.push({"frame_id": frame["frame_id"], "text": frame["narration_text"]}) if hasattr(tts_items, "push") else tts_items.append({"frame_id": frame["frame_id"], "text": frame["narration_text"]})

    start_t = time.time()
    tts_resp = client.post("/api/batch/tts", json={"items": tts_items, "voice": "ru-RU-DmitryNeural", "max_concurrency": 4})
    elapsed_tts = time.time() - start_t
    assert tts_resp.status_code == 200, f"Ошибка TTS: {tts_resp.text}"
    tts_results = tts_resp.json()
    print(f"✅ Озвучка 3 кадров создана за {elapsed_tts:.2f}s!")

    # Привязываем аудиопути и длительности к кадрам
    audio_map = {res["frame_id"]: res for res in tts_results}
    for scene in script_data["scenes"]:
        for frame in scene["frames"]:
            fid = frame["frame_id"]
            if fid in audio_map:
                frame["audio_path"] = f"cache/audio/{audio_map[fid]['filename']}"
                frame["duration"] = audio_map[fid]["duration"]

    # ------------------------------------------------------------------
    # ФАЗА 3: Пакетная многопоточная генерация картинок и видео
    # ------------------------------------------------------------------
    print("\n[ФАЗА 3/8] Многопоточная генерация визуалов (иллюстрации и видеоклипы)...")
    img_items = []
    for scene in script_data["scenes"]:
        for frame in scene["frames"]:
            img_items.append({"frame_id": frame["frame_id"], "prompt": frame["visual_prompt"]})

    img_resp = client.post("/api/batch/images", json={"items": img_items, "max_concurrency": 3})
    assert img_resp.status_code == 200, f"Ошибка картинок: {img_resp.text}"
    img_results = img_resp.json()

    img_map = {res["frame_id"]: res for res in img_results}
    for scene in script_data["scenes"]:
        for frame in scene["frames"]:
            fid = frame["frame_id"]
            if fid in img_map:
                frame["image_path"] = f"cache/images/{img_map[fid]['filename']}"

    print(f"✅ Сгенерировано {len(img_results)} иллюстраций!")

    # ------------------------------------------------------------------
    # ФАЗА 4: Синхронизация таймлайна и таймкодов
    # ------------------------------------------------------------------
    print("\n[ФАЗА 4/8] Расчет хронометража и синхронизация таймлайна...")
    sync_resp = client.post("/api/timeline/sync", json=script_data)
    assert sync_resp.status_code == 200, f"Ошибка синхронизации: {sync_resp.text}"
    timeline_data = sync_resp.json()
    
    total_dur = timeline_data["total_duration"]
    formatted_dur = timeline_data["formatted_total_duration"]
    print(f"✅ Таймлайн синхронизирован! Итоговый хронометраж: {formatted_dur} ({total_dur:.2f}s)")

    # ------------------------------------------------------------------
    # ФАЗА 5: Генерация субтитров (SRT / VTT)
    # ------------------------------------------------------------------
    print("\n[ФАЗА 5/8] Генерация субтитров .SRT и .VTT...")
    sub_resp = client.post("/api/subtitles/generate", json=timeline_data)
    assert sub_resp.status_code == 200, f"Ошибка субтитров: {sub_resp.text}"
    sub_data = sub_resp.json()
    print(f"✅ Субтитры созданы! SRT: {sub_data['srt_filename']}, VTT: {sub_data['vtt_filename']}")

    # ------------------------------------------------------------------
    # ФАЗА 6: Подсчет финансовой сметы проекта
    # ------------------------------------------------------------------
    print("\n[ФАЗА 6/8] Расчет сметы расходов и экономии кэша...")
    cost_resp = client.post("/api/cost/calculate", json=script_data)
    assert cost_resp.status_code == 200, f"Ошибка сметы: {cost_resp.text}"
    cost_data = cost_resp.json()
    print(f"✅ Смета рассчитана: Оценка ${cost_data['total_estimated_cost']:.4f} | Фактически ${cost_data['actual_cost']:.4f} | Сэкономлено ${cost_data['cache_savings']:.4f}")

    # ------------------------------------------------------------------
    # ФАЗА 7: Экспорт таймлайна в формат FCPXML (DaVinci / Premiere)
    # ------------------------------------------------------------------
    print("\n[ФАЗА 7/8] Экспорт монтажного таймлайна FCPXML...")
    fcpxml_resp = client.post("/api/export/fcpxml", json=timeline_data)
    assert fcpxml_resp.status_code == 200, f"Ошибка FCPXML: {fcpxml_resp.text}"
    fcpxml_data = fcpxml_resp.json()
    print(f"✅ Экспорт FCPXML завершен: {fcpxml_data['filename']}")

    # ------------------------------------------------------------------
    # ФАЗА 8: Финальный рендеринг видеоролика MP4
    # ------------------------------------------------------------------
    print("\n[ФАЗА 8/8] Запуск финального рендеринга видеофильма MP4 через FFmpeg...")
    start_render = time.time()
    render_resp = client.post("/api/render/full-video", json=timeline_data)
    elapsed_render = time.time() - start_render
    assert render_resp.status_code == 200, f"Ошибка рендеринга: {render_resp.text}"
    render_data = render_resp.json()
    
    output_filename = render_data["filename"]
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(backend_dir, "output", output_filename)

    print(f"✅ Финальный рендеринг завершен за {elapsed_render:.2f}s!")
    print(f"🎬 Итоговый скомпилированный видеофайл: {output_path}")

    # Физическая проверка результатов на диске
    assert os.path.exists(output_path), "Выходной MP4 файл не создан!"
    assert os.path.getsize(output_path) > 1000, "Выходной MP4 файл имеет слишком маленький размер!"

    print("==================================================================")
    print(" 🎉 [E2E SUCCESS] Все 8 фаз сквозного теста пройдены успешно!")
    print("==================================================================")

if __name__ == "__main__":
    run_end_to_end_test()
