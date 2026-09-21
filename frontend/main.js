const { app, BrowserWindow } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const http = require('http');

let pyProc = null;

function startBackendServer() {
  // Проверяем, запущен ли бэкенд на порту 8000
  const req = http.get('http://127.0.0.1:8000/api/health', (res) => {
    console.log('Бэкенд уже запущен.');
  });

  req.on('error', () => {
    console.log('Бэкенд не обнаружен. Автозапуск Python FastAPI бэкенда...');
    const backendPath = path.join(__dirname, '..', 'backend');
    const pythonExec = path.join(backendPath, 'venv', 'Scripts', 'python.exe');
    const mainScript = path.join(backendPath, 'main.py');

    try {
      pyProc = spawn(pythonExec, [mainScript], { cwd: backendPath });
      pyProc.stdout.on('data', (data) => console.log(`[PYTHON]: ${data}`));
      pyProc.stderr.on('data', (data) => console.error(`[PYTHON ERR]: ${data}`));
    } catch (e) {
      console.error('Ошибка автозапуска бэкенда:', e);
    }
  });
}

function createWindow() {
  const mainWindow = new BrowserWindow({
    width: 1080,
    height: 760,
    title: 'YouTube Video Generator',
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  });

  mainWindow.loadFile('index.html');
}

app.whenReady().then(() => {
  startBackendServer();
  createWindow();

  app.on('activate', function () {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', function () {
  if (pyProc) {
    try { pyProc.kill(); } catch (e) {}
  }
  if (process.platform !== 'darwin') app.quit();
});
