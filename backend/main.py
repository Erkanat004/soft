import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.api.routes import router as api_router

load_dotenv()

app = FastAPI(
    title="YouTube Video Generator Backend",
    version="0.2.0",
    description="REST API бэкенд для автоматической генерации видео из сценария"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение маршрутов API
app.include_router(api_router)

@app.get("/")
def read_root():
    return {"message": "YouTube Video Generator API работает"}

@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "app": "YouTube Video Generator Backend",
        "stage": 2,
        "env": {
            "host": os.getenv("HOST", "127.0.0.1"),
            "port": int(os.getenv("PORT", 8000)),
            "tts_provider": os.getenv("TTS_PROVIDER", "edge-tts")
        }
    }

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host=host, port=port, reload=True)
