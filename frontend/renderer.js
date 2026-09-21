const API_BASE = 'http://127.0.0.1:8000/api';

// UI Элементы с функциями безаварийной выборки
const getEl = (id) => document.getElementById(id);

let selectedFile = null;
let currentScriptData = null;
let currentTimelineData = null;

// Функции логирования и прогресс-бара
function logDiagnostic(type, message) {
  const logConsole = getEl('logConsole');
  if (!logConsole) return;
  const line = document.createElement('div');
  const now = new Date().toLocaleTimeString();
  line.className = `log-line log-${type}`;
  line.textContent = `[${now}] [${type.toUpperCase()}] ${message}`;
  logConsole.appendChild(line);
  logConsole.scrollTop = logConsole.scrollHeight;
}

function updateProgress(percent, label) {
  const progressBar = getEl('progressBar');
  const progressLabel = getEl('progressLabel');
  if (progressBar) progressBar.style.width = `${percent}%`;
  if (progressLabel) progressLabel.textContent = `${label} (${percent}%)`;
}

// 1. Проверка бэкенда и восстановление состояния
async function checkBackendHealth() {
  logDiagnostic('info', 'Проверка связи с REST API бэкендом...');
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (res.ok) {
      const statusBadge = getEl('statusBadge');
      const statusDot = getEl('statusDot');
      const statusText = getEl('statusText');
      if (statusBadge) statusBadge.className = 'status-badge status-online';
      if (statusDot) statusDot.className = 'dot online-dot';
      if (statusText) statusText.textContent = 'REST API подключен';
      
      logDiagnostic('success', 'Подключение к бэкенду установлено (FastAPI v0.2.0)');

      // Проверка диагностики диска
      const diagRes = await fetch(`${API_BASE}/system/logs`);
      if (diagRes.ok) {
        const diag = await diagRes.json();
        logDiagnostic('info', `Кэш: Аудио (${diag.audio_cache_count}), Картинки (${diag.image_cache_count}), Видео (${diag.video_cache_count}), Рендеры (${diag.render_count})`);
      }

      await loadAvailableVoices();
      await restoreProjectState();
    } else {
      throw new Error();
    }
  } catch {
    const statusBadge = getEl('statusBadge');
    const statusDot = getEl('statusDot');
    const statusText = getEl('statusText');
    if (statusBadge) statusBadge.className = 'status-badge status-offline';
    if (statusDot) statusDot.className = 'dot offline-dot';
    if (statusText) statusText.textContent = 'REST API офлайн';
    logDiagnostic('error', 'Ошибка связи с бэкендом! Убедитесь, что сервер запущен');
  }
}

// Восстановление проекта из project_state.json
async function restoreProjectState() {
  try {
    const res = await fetch(`${API_BASE}/project/state`);
    if (res.ok) {
      const state = await res.json();
      if (state && state.scenes && state.scenes.length > 0) {
        logDiagnostic('info', 'Найдено сохраненное состояние проекта. Восстановление данных...');
        renderScript(state);
        await syncTimeline();
        logDiagnostic('success', 'Проект успешно восстановлен из памяти');
      }
    }
  } catch (err) {
    logDiagnostic('warning', `Ошибка выгрузки сохраненного состояния: ${err.message}`);
  }
}

// 2. Вкладки
document.addEventListener('DOMContentLoaded', () => {
  setupEventListeners();
});

function setupEventListeners() {
  const tabTextBtn = getEl('tabTextBtn');
  const tabFileBtn = getEl('tabFileBtn');
  const tabTextContent = getEl('tabTextContent');
  const tabFileContent = getEl('tabFileContent');

  if (tabTextBtn && tabFileBtn) {
    tabTextBtn.addEventListener('click', () => {
      tabTextBtn.classList.add('active');
      tabFileBtn.classList.remove('active');
      if (tabTextContent) tabTextContent.classList.add('active');
      if (tabFileContent) tabFileContent.classList.remove('active');
    });

    tabFileBtn.addEventListener('click', () => {
      tabFileBtn.classList.add('active');
      tabTextBtn.classList.remove('active');
      if (tabFileContent) tabFileContent.classList.add('active');
      if (tabTextContent) tabTextContent.classList.remove('active');
    });
  }

  const clearLogsBtn = getEl('clearLogsBtn');
  if (clearLogsBtn) {
    clearLogsBtn.addEventListener('click', () => {
      const logConsole = getEl('logConsole');
      if (logConsole) logConsole.innerHTML = '<div class="log-line log-info">[SYSTEM] Лог очищен</div>';
    });
  }

  // Обработчики модального окна справки
  const helpBtn = getEl('helpBtn');
  const closeHelpBtn = getEl('closeHelpBtn');
  const okHelpBtn = getEl('okHelpBtn');
  const helpModal = getEl('helpModal');

  if (helpBtn && helpModal) {
    helpBtn.addEventListener('click', () => helpModal.style.display = 'flex');
  }
  if (closeHelpBtn && helpModal) {
    closeHelpBtn.addEventListener('click', () => helpModal.style.display = 'none');
  }
  // Обработчики модального окна настроек ключей
  const settingsBtn = getEl('settingsBtn');
  const closeSettingsBtn = getEl('closeSettingsBtn');
  const saveSettingsBtn = getEl('saveSettingsBtn');
  const settingsModal = getEl('settingsModal');

  if (settingsBtn && settingsModal) {
    settingsBtn.addEventListener('click', async () => {
      settingsModal.style.display = 'flex';
      await loadSystemSettings();
    });
  }
  if (closeSettingsBtn && settingsModal) {
    closeSettingsBtn.addEventListener('click', () => settingsModal.style.display = 'none');
  }
  if (saveSettingsBtn) {
    saveSettingsBtn.addEventListener('click', async () => {
      const openaiKey = getEl('openaiKeyInput') ? getEl('openaiKeyInput').value : '';
      const replicateKey = getEl('replicateKeyInput') ? getEl('replicateKeyInput').value : '';
      const elevenlabsKey = getEl('elevenlabsKeyInput') ? getEl('elevenlabsKeyInput').value : '';

      try {
        saveSettingsBtn.disabled = true;
        const res = await fetch(`${API_BASE}/system/settings`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            openai_api_key: openaiKey,
            replicate_api_key: replicateKey,
            elevenlabs_api_key: elevenlabsKey
          })
        });

        if (!res.ok) throw new Error(`Ошибка сохранения: ${res.status}`);
        const data = await res.json();

        updateSettingsStatusBadge(data);
        logDiagnostic('success', `API Ключи сохранены! Провайдер: ${data.image_provider.toUpperCase()} | ${data.status_label}`);
        alert(`Настройки успешно сохранены!\nСтатус: ${data.status_label}`);
        settingsModal.style.display = 'none';

      } catch (err) {
        logDiagnostic('error', `Ошибка сохранения ключей: ${err.message}`);
        alert(`Ошибка сохранения: ${err.message}`);
      } finally {
        saveSettingsBtn.disabled = false;
      }
    });
  }

  // Drag & Drop файла
  const dropZone = getEl('dropZone');
  const fileInput = getEl('fileInput');
  if (dropZone && fileInput) {
    dropZone.addEventListener('click', () => fileInput.click());
    dropZone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropZone.style.borderColor = '#38bdf8';
    });
    dropZone.addEventListener('dragleave', () => {
      dropZone.style.borderColor = '#475569';
    });
    dropZone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropZone.style.borderColor = '#475569';
      if (e.dataTransfer.files.length > 0) {
        handleFileSelect(e.dataTransfer.files[0]);
      }
    });
    fileInput.addEventListener('change', (e) => {
      if (e.target.files.length > 0) {
        handleFileSelect(e.target.files[0]);
      }
    });
  }

  // Парсинг текста
  const parseTextBtn = getEl('parseTextBtn');
  if (parseTextBtn) {
    parseTextBtn.addEventListener('click', async () => {
      const scriptTextInput = getEl('scriptTextInput');
      const text = scriptTextInput ? scriptTextInput.value.trim() : '';
      if (!text) {
        alert('Введите текст сценария!');
        return;
      }
      
      parseTextBtn.disabled = true;
      updateProgress(10, 'Парсинг текста...');
      logDiagnostic('info', 'Отправка текста на распарсивание...');
      try {
        const res = await fetch(`${API_BASE}/parse-text`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text })
        });
        if (!res.ok) throw new Error(`Ошибка сервера: ${res.status}`);
        const data = await res.json();
        renderScript(data);
        await syncTimeline();
        updateProgress(100, 'Сценарий загружен');
        logDiagnostic('success', `Сценарий успешно распарсен! Сцен: ${data.total_scenes}, Кадров: ${data.total_frames}`);
      } catch (err) {
        logDiagnostic('error', `Ошибка парсинга: ${err.message}`);
        updateProgress(0, 'Ошибка');
      } finally {
        parseTextBtn.disabled = false;
      }
    });
  }

  // Парсинг файла
  const parseFileBtn = getEl('parseFileBtn');
  if (parseFileBtn) {
    parseFileBtn.addEventListener('click', async () => {
      if (!selectedFile) return;

      parseFileBtn.disabled = true;
      updateProgress(10, 'Чтение файла...');
      logDiagnostic('info', `Отправка файла '${selectedFile.name}' на сервер...`);

      const formData = new FormData();
      formData.append('file', selectedFile);

      try {
        const res = await fetch(`${API_BASE}/upload-script`, {
          method: 'POST',
          body: formData
        });
        if (!res.ok) throw new Error(`Ошибка сервера: ${res.status}`);
        const data = await res.json();
        renderScript(data);
        await syncTimeline();
        updateProgress(100, 'Файл распарсен');
        logDiagnostic('success', `Файл ${selectedFile.name} успешно распарсен!`);
      } catch (err) {
        logDiagnostic('error', `Ошибка парсинга файла: ${err.message}`);
        updateProgress(0, 'Ошибка');
      } finally {
        parseFileBtn.disabled = false;
      }
    });
  }

  // Кнопки пакетных действий
  const generateAllTtsBtn = getEl('generateAllTtsBtn');
  if (generateAllTtsBtn) {
    generateAllTtsBtn.addEventListener('click', async () => {
      const frameCards = document.querySelectorAll('.frame-card');
      if (frameCards.length === 0) return;

      generateAllTtsBtn.disabled = true;
      updateProgress(10, 'Подготовка к пакетному озвучиванию...');
      logDiagnostic('info', `Запуск асинхронного пакетного озвучивания для ${frameCards.length} кадров...`);

      const items = [];
      frameCards.forEach(card => {
        const frameId = card.getAttribute('data-frame-id');
        const narrationInput = card.querySelector('.narration-input');
        const narrationText = narrationInput ? narrationInput.value : '';
        if (narrationText) {
          items.push({ frame_id: frameId, text: narrationText });
        }
      });

      const voiceSelect = getEl('voiceSelect');
      const selectedVoice = voiceSelect ? voiceSelect.value : 'ru-RU-DmitryNeural';

      try {
        const res = await fetch(`${API_BASE}/batch/tts`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ items, voice: selectedVoice, max_concurrency: 4 })
        });
        if (!res.ok) throw new Error(`Ошибка сервера: ${res.status}`);
        const results = await res.json();

        results.forEach(resItem => {
          if (resItem.error) return;
          const card = document.querySelector(`.frame-card[data-frame-id="${resItem.frame_id}"]`);
          if (card) {
            let audioContainer = card.querySelector('.audio-preview');
            if (!audioContainer) {
              audioContainer = document.createElement('div');
              audioContainer.className = 'audio-preview';
              card.appendChild(audioContainer);
            }
            audioContainer.innerHTML = `
              <span style="font-size: 12px; color: #4ade80;">🔊 Озвучено (${resItem.duration}s):</span>
              <audio controls src="http://127.0.0.1:8000${resItem.audio_url}"></audio>
            `;
          }
        });

        await syncTimeline();
        updateProgress(100, 'Пакетная озвучка готова!');
        logDiagnostic('success', `Асинхронная пакетная озвучка (${results.length} кадров) успешно завершена!`);

      } catch (err) {
        logDiagnostic('error', `Ошибка пакетного TTS: ${err.message}`);
        updateProgress(0, 'Ошибка');
      } finally {
        generateAllTtsBtn.disabled = false;
      }
    });
  }

  const generateAllImagesBtn = getEl('generateAllImagesBtn');
  if (generateAllImagesBtn) {
    generateAllImagesBtn.addEventListener('click', async () => {
      const frameCards = document.querySelectorAll('.frame-card');
      if (frameCards.length === 0) return;

      generateAllImagesBtn.disabled = true;
      updateProgress(10, 'Подготовка к генерации иллюстраций...');
      logDiagnostic('info', `Запуск многопоточной генерации картинок для ${frameCards.length} кадров...`);

      const items = [];
      frameCards.forEach(card => {
        const frameId = card.getAttribute('data-frame-id');
        const visualInput = card.querySelector('.visual-input');
        const visualPrompt = visualInput ? visualInput.value : '';
        if (visualPrompt) {
          items.push({ frame_id: frameId, prompt: visualPrompt });
        }
      });

      try {
        const res = await fetch(`${API_BASE}/batch/images`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ items, max_concurrency: 3 })
        });
        if (!res.ok) throw new Error(`Ошибка сервера: ${res.status}`);
        const results = await res.json();

        results.forEach(resItem => {
          if (resItem.error) return;
          const card = document.querySelector(`.frame-card[data-frame-id="${resItem.frame_id}"]`);
          if (card) {
            const mediaContainer = card.querySelector('.media-preview-container');
            if (mediaContainer) {
              const fullImgUrl = `http://127.0.0.1:8000${resItem.image_url}?t=${Date.now()}`;
              mediaContainer.innerHTML = `<img src="${fullImgUrl}" alt="Превью" title="${resItem.cached ? 'Из кэша' : 'Сгенерировано'}">`;
            }
          }
        });

        await syncTimeline();
        updateProgress(100, 'Все иллюстрации готовы!');
        logDiagnostic('success', `Многопоточная генерация ${results.length} картинок завершена!`);

      } catch (err) {
        logDiagnostic('error', `Ошибка генерации картинок: ${err.message}`);
        updateProgress(0, 'Ошибка');
      } finally {
        generateAllImagesBtn.disabled = false;
      }
    });
  }

  const generateAllVideosBtn = getEl('generateAllVideosBtn');
  if (generateAllVideosBtn) {
    generateAllVideosBtn.addEventListener('click', async () => {
      const frameCards = document.querySelectorAll('.frame-card');
      if (frameCards.length === 0) return;

      generateAllVideosBtn.disabled = true;
      updateProgress(10, 'Подготовка к видеоанимации...');
      logDiagnostic('info', `Запуск параллельного Ken Burns рендеринга для ${frameCards.length} кадров...`);

      const items = [];
      frameCards.forEach(card => {
        const frameId = card.getAttribute('data-frame-id');
        const visualInput = card.querySelector('.visual-input');
        const visualPrompt = visualInput ? visualInput.value : '';
        if (visualPrompt) {
          items.push({ frame_id: frameId, prompt: visualPrompt });
        }
      });

      try {
        const res = await fetch(`${API_BASE}/batch/videos`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ items, duration: 3.0, max_concurrency: 2 })
        });
        if (!res.ok) throw new Error(`Ошибка сервера: ${res.status}`);
        const results = await res.json();

        results.forEach(resItem => {
          if (resItem.error) return;
          const card = document.querySelector(`.frame-card[data-frame-id="${resItem.frame_id}"]`);
          if (card) {
            const mediaContainer = card.querySelector('.media-preview-container');
            if (mediaContainer) {
              const fullVideoUrl = `http://127.0.0.1:8000${resItem.video_url}?t=${Date.now()}`;
              mediaContainer.innerHTML = `<video controls autoplay loop src="${fullVideoUrl}"></video>`;
            }
          }
        });

        await syncTimeline();
        updateProgress(100, 'Анимация клипов завершена!');
        logDiagnostic('success', `Параллельный рендеринг (${results.length} клипов) завершен!`);

      } catch (err) {
        logDiagnostic('error', `Ошибка пакетной видеоанимации: ${err.message}`);
        updateProgress(0, 'Ошибка');
      } finally {
        generateAllVideosBtn.disabled = false;
      }
    });
  }

  const generateSubtitlesBtn = getEl('generateSubtitlesBtn');
  if (generateSubtitlesBtn) {
    generateSubtitlesBtn.addEventListener('click', async () => {
      const timeline = await syncTimeline();
      if (!timeline) return;

      generateSubtitlesBtn.disabled = true;
      updateProgress(40, 'Генерация субтитров...');
      logDiagnostic('info', 'Генерация субтитров SRT и VTT...');

      try {
        const res = await fetch(`${API_BASE}/subtitles/generate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(timeline)
        });

        if (!res.ok) throw new Error(`Ошибка генерации субтитров: ${res.status}`);
        const data = await res.json();

        const subtitlesBox = getEl('subtitlesBox');
        const subtitlePreviewText = getEl('subtitlePreviewText');
        const downloadSrtLink = getEl('downloadSrtLink');
        const downloadVttLink = getEl('downloadVttLink');

        if (subtitlesBox) subtitlesBox.style.display = 'flex';
        if (subtitlePreviewText) subtitlePreviewText.textContent = data.srt_content;
        if (downloadSrtLink) downloadSrtLink.href = `http://127.0.0.1:8000${data.srt_url}`;
        if (downloadVttLink) downloadVttLink.href = `http://127.0.0.1:8000${data.vtt_url}`;

        updateProgress(100, 'Субтитры готовы');
        logDiagnostic('success', 'Файлы субтитров .SRT и .VTT успешно сформированы');

      } catch (err) {
        logDiagnostic('error', `Ошибка генерации субтитров: ${err.message}`);
        updateProgress(0, 'Ошибка');
      } finally {
        generateSubtitlesBtn.disabled = false;
      }
    });
  }

  const exportFcpxmlBtn = getEl('exportFcpxmlBtn');
  if (exportFcpxmlBtn) {
    exportFcpxmlBtn.addEventListener('click', async () => {
      const timeline = await syncTimeline();
      if (!timeline) return;

      exportFcpxmlBtn.disabled = true;
      updateProgress(40, 'Экспорт проекта в FCPXML...');
      logDiagnostic('info', 'Формирование файла монтажного таймлайна (.fcpxml)...');

      try {
        const res = await fetch(`${API_BASE}/export/fcpxml`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(timeline)
        });

        if (!res.ok) throw new Error(`Ошибка экспорта: ${res.status}`);
        const data = await res.json();

        const downloadUrl = `http://127.0.0.1:8000${data.fcpxml_url}`;
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = data.filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);

        updateProgress(100, 'FCPXML экспортирован!');
        logDiagnostic('success', `Файл FCPXML для DaVinci / Premiere успешно сформирован: ${data.filename}`);

      } catch (err) {
        logDiagnostic('error', `Ошибка экспорта FCPXML: ${err.message}`);
        updateProgress(0, 'Ошибка');
      } finally {
        exportFcpxmlBtn.disabled = false;
      }
    });
  }

  const renderFullVideoBtn = getEl('renderFullVideoBtn');
  if (renderFullVideoBtn) {
    renderFullVideoBtn.addEventListener('click', async () => {
      const timeline = await syncTimeline();
      if (!timeline) return;

      renderFullVideoBtn.disabled = true;
      updateProgress(20, 'Запуск локального рендера FFmpeg...');
      logDiagnostic('info', 'Сборка и компиляция финального роликов MP4...');

      try {
        const res = await fetch(`${API_BASE}/render/full-video`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(timeline)
        });

        if (!res.ok) throw new Error(`Ошибка рендеринга: ${res.status}`);
        const data = await res.json();

        const renderBox = getEl('renderBox');
        const finalVideoPlayer = getEl('finalVideoPlayer');
        const downloadRenderLink = getEl('downloadRenderLink');

        if (renderBox) renderBox.style.display = 'flex';
        const fullRenderUrl = `http://127.0.0.1:8000${data.render_url}?t=${Date.now()}`;
        if (finalVideoPlayer) finalVideoPlayer.src = fullRenderUrl;
        if (downloadRenderLink) downloadRenderLink.href = fullRenderUrl;

        updateProgress(100, 'Рендеринг завершен!');
        logDiagnostic('success', `Видеофильм успешно скомпилирован! Файл: ${data.filename} ${data.cached ? '(из кэша)' : ''}`);

      } catch (err) {
        logDiagnostic('error', `Ошибка рендеринга видео: ${err.message}`);
        updateProgress(0, 'Сбой рендера');
      } finally {
        renderFullVideoBtn.disabled = false;
      }
    });
  }
}

function handleFileSelect(file) {
  if (!file.name.endsWith('.txt') && !file.name.endsWith('.docx')) {
    alert('Пожалуйста, выберите файл .txt или .docx');
    return;
  }
  selectedFile = file;
  const selectedFileName = getEl('selectedFileName');
  const parseFileBtn = getEl('parseFileBtn');

  if (selectedFileName) {
    selectedFileName.textContent = `Выбран файл: ${file.name}`;
    selectedFileName.style.display = 'block';
  }
  if (parseFileBtn) parseFileBtn.disabled = false;
  logDiagnostic('info', `Файл выбран: ${file.name}`);
}

// 6. Синхронизация Таймлайна
async function syncTimeline() {
  if (!currentScriptData) return null;

  try {
    const res = await fetch(`${API_BASE}/timeline/sync`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(currentScriptData)
    });

    if (!res.ok) throw new Error(`Ошибка синхронизации: ${res.status}`);
    currentTimelineData = await res.json();

    const totalDurationBadge = getEl('totalDurationBadge');
    if (totalDurationBadge) {
      totalDurationBadge.textContent = `⏱️ Хронометраж: ${currentTimelineData.formatted_total_duration} (${currentTimelineData.total_duration}s)`;
    }

    currentTimelineData.timeline.forEach(tf => {
      const card = document.querySelector(`.frame-card[data-frame-id="${tf.frame_id}"]`);
      if (card) {
        const durationSpan = card.querySelector('.frame-duration');
        if (durationSpan) {
          durationSpan.innerHTML = `<span class="tc-badge">${tf.formatted_start} ➔ ${tf.formatted_end}</span> ${tf.duration}s`;
        }
      }
    });

    return currentTimelineData;

  } catch (err) {
    logDiagnostic('error', `Ошибка синхронизации таймлайна: ${err.message}`);
  }
}

// 9. Генерация TTS для одного кадра
async function generateFrameTTS(frameId, text, btnElement, cardElement) {
  if (!text.trim()) return;

  btnElement.disabled = true;
  logDiagnostic('info', `Озвучивание кадра ${frameId}...`);

  const voiceSelect = getEl('voiceSelect');
  const selectedVoice = voiceSelect ? voiceSelect.value : 'ru-RU-DmitryNeural';

  try {
    const res = await fetch(`${API_BASE}/tts/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ frame_id: frameId, text, voice: selectedVoice })
    });

    if (!res.ok) throw new Error(`Ошибка TTS: ${res.status}`);
    const data = await res.json();

    let audioContainer = cardElement.querySelector('.audio-preview');
    if (!audioContainer) {
      audioContainer = document.createElement('div');
      audioContainer.className = 'audio-preview';
      cardElement.appendChild(audioContainer);
    }

    const fullAudioUrl = `http://127.0.0.1:8000${data.audio_url}`;
    audioContainer.innerHTML = `
      <span style="font-size: 12px; color: #4ade80;">🔊 Озвучено (${data.duration}s):</span>
      <audio controls src="${fullAudioUrl}"></audio>
    `;

    logDiagnostic('success', `Кадр ${frameId} озвучен (${data.duration}s) ${data.cached ? '⚡(из кэша)' : ''}`);
    await syncTimeline();

  } catch (err) {
    logDiagnostic('error', `Ошибка TTS кадра ${frameId}: ${err.message}`);
  } finally {
    btnElement.disabled = false;
  }
}

// 10. Генерация Изображения для одного кадра
async function generateFrameImage(frameId, prompt, btnElement, cardElement) {
  if (!prompt.trim()) return;

  btnElement.disabled = true;
  logDiagnostic('info', `Генерация картинки для кадра ${frameId}...`);

  try {
    const res = await fetch(`${API_BASE}/image/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ frame_id: frameId, prompt })
    });

    if (!res.ok) throw new Error(`Ошибка картинки: ${res.status}`);
    const data = await res.json();

    const mediaContainer = cardElement.querySelector('.media-preview-container');
    if (mediaContainer) {
      const fullImgUrl = `http://127.0.0.1:8000${data.image_url}?t=${Date.now()}`;
      mediaContainer.innerHTML = `<img src="${fullImgUrl}" alt="Превью" title="${data.cached ? 'Из кэша' : 'Сгенерировано'}">`;
    }

    logDiagnostic('success', `Картинка для кадра ${frameId} создана ${data.cached ? '⚡(из кэша)' : ''}`);

  } catch (err) {
    logDiagnostic('error', `Ошибка генерации картинки кадра ${frameId}: ${err.message}`);
  } finally {
    btnElement.disabled = false;
  }
}

// 11. Генерация Видео Анимации для одного кадра
async function generateFrameVideo(frameId, prompt, btnElement, cardElement) {
  if (!prompt.trim()) return;

  btnElement.disabled = true;
  logDiagnostic('info', `Анимация видео для кадра ${frameId}...`);

  try {
    const res = await fetch(`${API_BASE}/video/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ frame_id: frameId, prompt, duration: 3.0 })
    });

    if (!res.ok) throw new Error(`Ошибка видео: ${res.status}`);
    const data = await res.json();

    const mediaContainer = cardElement.querySelector('.media-preview-container');
    if (mediaContainer) {
      const fullVideoUrl = `http://127.0.0.1:8000${data.video_url}?t=${Date.now()}`;
      mediaContainer.innerHTML = `<video controls autoplay loop src="${fullVideoUrl}"></video>`;
    }

    logDiagnostic('success', `Анимация клипа кадра ${frameId} сгенерирована ${data.cached ? '⚡(из кэша)' : ''}`);

  } catch (err) {
    logDiagnostic('error', `Ошибка анимации кадра ${frameId}: ${err.message}`);
  } finally {
    btnElement.disabled = false;
  }
}

// 13. Отрисовка сценария
function renderScript(scriptData) {
  currentScriptData = scriptData;

  const emptyState = getEl('emptyState');
  const scriptView = getEl('scriptView');
  const renderBox = getEl('renderBox');
  const subtitlesBox = getEl('subtitlesBox');
  const scriptTitleView = getEl('scriptTitleView');
  const totalScenesCount = getEl('totalScenesCount');
  const totalFramesCount = getEl('totalFramesCount');
  const scenesContainer = getEl('scenesContainer');

  if (emptyState) emptyState.style.display = 'none';
  if (scriptView) scriptView.style.display = 'flex';
  if (renderBox) renderBox.style.display = 'none';
  if (subtitlesBox) subtitlesBox.style.display = 'none';

  if (scriptTitleView) scriptTitleView.textContent = scriptData.title || 'Сценарий';
  if (totalScenesCount) totalScenesCount.textContent = scriptData.total_scenes != null ? scriptData.total_scenes : (scriptData.scenes ? scriptData.scenes.length : 0);
  if (totalFramesCount) totalFramesCount.textContent = scriptData.total_frames != null ? scriptData.total_frames : 0;

  updateCostTracker(scriptData);

  if (!scenesContainer) return;
  scenesContainer.innerHTML = '';

  scriptData.scenes.forEach(scene => {
    const sceneCard = document.createElement('div');
    sceneCard.className = 'scene-card';

    const framesContainer = document.createElement('div');
    framesContainer.className = 'frames-container';

    scene.frames.forEach(frame => {
      const frameCard = document.createElement('div');
      frameCard.className = 'frame-card';
      frameCard.setAttribute('data-frame-id', frame.frame_id);

      frameCard.innerHTML = `
        <div class="frame-header">
          <span>Кадр #${frame.frame_number} (${frame.frame_id})</span>
          <div style="display: flex; align-items: center; gap: 6px;">
            <span class="frame-duration" style="color: #94a3b8; font-size: 12px;">Длительность: ${frame.duration || 0}s</span>
            <button class="btn-secondary tts-single-btn">🔊 Озвучить</button>
            <button class="btn-secondary img-single-btn">🎨 Картинка</button>
            <button class="btn-secondary video-single-btn">🎬 Видео</button>
          </div>
        </div>

        <div class="frame-body">
          <div style="display: flex; flex-direction: column; gap: 10px;">
            <div class="form-group">
              <label>🎙️ Текст для озвучки (TTS):</label>
              <textarea class="narration-input">${escapeHtml(frame.narration_text)}</textarea>
            </div>

            <div class="form-group">
              <label>🎨 Промпт для визуала (Image / Video Model):</label>
              <textarea class="visual-input">${escapeHtml(frame.visual_prompt)}</textarea>
            </div>
          </div>

          <div class="media-preview-container">
            <div class="media-placeholder">🎬 Медиа не сгенерировано</div>
          </div>
        </div>
      `;

      // Восстановление существующих визуалов и аудио из сохраненного состояния
      if (frame.audio_path) {
        let audioContainer = frameCard.querySelector('.audio-preview');
        if (!audioContainer) {
          audioContainer = document.createElement('div');
          audioContainer.className = 'audio-preview';
          frameCard.appendChild(audioContainer);
        }
        const audioFileName = frame.audio_path.split(/[/\\]/).pop();
        audioContainer.innerHTML = `
          <span style="font-size: 12px; color: #4ade80;">🔊 Озвучено (${frame.duration || 0}s):</span>
          <audio controls src="http://127.0.0.1:8000/api/audio/${audioFileName}"></audio>
        `;
      }

      const mediaContainer = frameCard.querySelector('.media-preview-container');
      if (mediaContainer) {
        if (frame.video_path) {
          const videoFileName = frame.video_path.split(/[/\\]/).pop();
          mediaContainer.innerHTML = `<video controls autoplay loop src="http://127.0.0.1:8000/api/videos/${videoFileName}"></video>`;
        } else if (frame.image_path) {
          const imageFileName = frame.image_path.split(/[/\\]/).pop();
          mediaContainer.innerHTML = `<img src="http://127.0.0.1:8000/api/images/${imageFileName}" alt="Превью">`;
        }
      }

      const ttsSingleBtn = frameCard.querySelector('.tts-single-btn');
      const imgSingleBtn = frameCard.querySelector('.img-single-btn');
      const videoSingleBtn = frameCard.querySelector('.video-single-btn');

      const narrationInput = frameCard.querySelector('.narration-input');
      const visualInput = frameCard.querySelector('.visual-input');

      ttsSingleBtn.addEventListener('click', () => {
        generateFrameTTS(frame.frame_id, narrationInput.value, ttsSingleBtn, frameCard);
      });

      imgSingleBtn.addEventListener('click', () => {
        generateFrameImage(frame.frame_id, visualInput.value, imgSingleBtn, frameCard);
      });

      videoSingleBtn.addEventListener('click', () => {
        generateFrameVideo(frame.frame_id, visualInput.value, videoSingleBtn, frameCard);
      });

      framesContainer.appendChild(frameCard);
    });

    sceneCard.innerHTML = `
      <div class="scene-header">
        <span>🎬 ${escapeHtml(scene.title)}</span>
        <span style="font-size: 13px; font-weight: normal; color: #94a3b8;">${scene.frames.length} кадра(ов)</span>
      </div>
    `;

    sceneCard.appendChild(framesContainer);
    scenesContainer.appendChild(sceneCard);
  });
}

// Подсчет сметы проекта через REST API
async function updateCostTracker(scriptData) {
  if (!scriptData) return;
  try {
    const res = await fetch(`${API_BASE}/cost/calculate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(scriptData)
    });
    if (res.ok) {
      const costInfo = await res.json();
      const costBadge = getEl('costBadge');
      if (costBadge) {
        costBadge.textContent = `💰 Смета: $${costInfo.total_estimated_cost.toFixed(3)} (Экономия: $${costInfo.cache_savings.toFixed(3)})`;
      }
      logDiagnostic('info', `Финансовая смета: Оценка $${costInfo.total_estimated_cost.toFixed(3)} | Фактически $${costInfo.actual_cost.toFixed(3)} | Кэш сэкономил $${costInfo.cache_savings.toFixed(3)}`);
    }
  } catch (err) {
    logDiagnostic('warning', `Ошибка обновления сметы: ${err.message}`);
  }
}

// Динамическая загрузка библиотеки дикторских голосов
async function loadAvailableVoices() {
  try {
    const res = await fetch(`${API_BASE}/voices`);
    if (res.ok) {
      const data = await res.json();
      const voiceSelect = getEl('voiceSelect');
      if (voiceSelect && data.voices && data.voices.length > 0) {
        voiceSelect.innerHTML = data.voices.map(v => 
          `<option value="${v.id}" ${v.default ? 'selected' : ''}>${v.name}</option>`
        ).join('');
        logDiagnostic('info', `Загружена библиотека голосов (${data.voices.length} доступно)`);
      }
    }
  } catch (err) {
    logDiagnostic('warning', `Не удалось загрузить дикторов: ${err.message}`);
  }
}

// Настройки API Ключей и статуса МОК-режима
async function loadSystemSettings() {
  try {
    const res = await fetch(`${API_BASE}/system/settings`);
    if (res.ok) {
      const data = await res.json();
      updateSettingsStatusBadge(data);

      const openaiInput = getEl('openaiKeyInput');
      const replicateInput = getEl('replicateKeyInput');
      if (openaiInput && data.openai_api_key_masked) {
        openaiInput.placeholder = `Ключ загружен (${data.openai_api_key_masked})`;
      }
      if (replicateInput && data.replicate_api_key_masked) {
        replicateInput.placeholder = `Ключ загружен (${data.replicate_api_key_masked})`;
      }
    }
  } catch (err) {
    logDiagnostic('warning', `Не удалось загрузить статус настроек: ${err.message}`);
  }
}

function updateSettingsStatusBadge(data) {
  const badge = getEl('settingsStatusBadge');
  if (badge) {
    badge.textContent = data.status_label;
    if (data.mock_disabled) {
      badge.style.backgroundColor = 'rgba(34, 197, 94, 0.15)';
      badge.style.color = '#4ade80';
      badge.style.borderColor = 'rgba(34, 197, 94, 0.3)';
    } else {
      badge.style.backgroundColor = 'rgba(251, 191, 36, 0.15)';
      badge.style.color = '#fbbf24';
      badge.style.borderColor = 'rgba(251, 191, 36, 0.3)';
    }
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

checkBackendHealth();
