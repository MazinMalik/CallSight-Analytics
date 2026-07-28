import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    APP_ENV: str = "development"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DATABASE_URL: str = "sqlite:///./data/telecaller.db"

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen3.5:4b"
    OLLAMA_TIMEOUT_SECONDS: int = 180

    TRANSCRIPTION_ENGINE: str = "indic_conformer"
    DEFAULT_TRANSCRIPTION_LANGUAGE: str = "hi"
    TRANSCRIPTION_DEVICE: str = "cpu"
    TRANSCRIPTION_WORKERS: int = 1

    MAX_UPLOAD_MB: int = 50
    MAX_AUDIO_DURATION_MINUTES: int = 15
    DELETE_AUDIO_AFTER_PROCESSING: bool = False  # Keep audio files so user can preview/retranscribe

    FRONTEND_URL: str = "http://localhost:5173"
    EXPORT_DIRECTORY: str = "./exports"
    OUTPUTS_DIRECTORY: str = "./OUTPUTS"
    UPLOAD_DIRECTORY: str = "./uploads"

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def abs_upload_dir(self) -> Path:
        p = BASE_DIR / self.UPLOAD_DIRECTORY
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def abs_export_dir(self) -> Path:
        p = BASE_DIR / self.EXPORT_DIRECTORY
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def abs_outputs_dir(self) -> Path:
        p = BASE_DIR / self.OUTPUTS_DIRECTORY
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def sqlite_db_path(self) -> Path:
        if self.DATABASE_URL.startswith("sqlite:///"):
            db_rel = self.DATABASE_URL.replace("sqlite:///", "")
            p = BASE_DIR / db_rel
            p.parent.mkdir(parents=True, exist_ok=True)
            return p
        return BASE_DIR / "data" / "telecaller.db"

settings = Settings()
