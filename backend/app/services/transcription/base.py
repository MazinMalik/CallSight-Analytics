from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class TranscriptionSegment(BaseModel):
    start: float
    end: float
    text: str

class TranscriptionResult(BaseModel):
    text: str
    language: Optional[str] = "hi"
    duration_seconds: float = 0.0
    processing_time_seconds: float = 0.0
    segments: List[Dict[str, Any]] = []

class BaseTranscriptionService(ABC):
    @abstractmethod
    def load_model(self) -> None:
        """Loads the transcription model into memory ONCE at startup."""
        pass

    @abstractmethod
    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None
    ) -> TranscriptionResult:
        """Transcribe an audio file and return structured TranscriptionResult."""
        pass
