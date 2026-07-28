import os
import glob
import subprocess
import logging
from pathlib import Path
from typing import Optional
from app.core.config import settings

logger = logging.getLogger("audio_preprocessor")

def find_ffmpeg_executable() -> Optional[str]:
    """
    Locates FFmpeg executable across system PATH and Windows WinGet package directories.
    """
    try:
        res = subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode == 0:
            return "ffmpeg"
    except Exception:
        pass

    local_appdata = os.environ.get("LOCALAPPDATA", r"C:\Users\malik\AppData\Local")
    winget_pattern = os.path.join(local_appdata, "Microsoft", "WinGet", "Packages", "*FFmpeg*", "*", "bin", "ffmpeg.exe")
    matches = glob.glob(winget_pattern)
    if matches and os.path.exists(matches[0]):
        return matches[0]

    program_files_matches = glob.glob(r"C:\Program Files*\ffmpeg*\bin\ffmpeg.exe")
    if program_files_matches and os.path.exists(program_files_matches[0]):
        return program_files_matches[0]

    return None

class AudioPreprocessingError(Exception):
    pass

class AudioPreprocessor:
    """
    Handles audio file validation, FFmpeg normalization to 16 kHz Mono WAV format,
    and duration calculation.
    """
    SUPPORTED_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".webm"}

    def __init__(self):
        self.ffmpeg_path = find_ffmpeg_executable()
        if self.ffmpeg_path:
            logger.info(f"AudioPreprocessor initialized with FFmpeg path: {self.ffmpeg_path}")
        else:
            logger.warning("FFmpeg executable not found in PATH or WinGet packages. Conversions may fail.")

    def validate_file(self, filename: str, file_size: int) -> None:
        """Validates file extension and size constraints."""
        ext = Path(filename).suffix.lower()
        if ext not in self.SUPPORTED_EXTENSIONS:
            raise AudioPreprocessingError(
                f"Unsupported audio format '{ext}'. Supported formats: {', '.join(sorted(self.SUPPORTED_EXTENSIONS))}"
            )
        max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
        if file_size > max_bytes:
            raise AudioPreprocessingError(
                f"Audio file size ({round(file_size / (1024*1024), 2)} MB) exceeds maximum allowed limit of {settings.MAX_UPLOAD_MB} MB."
            )

    def convert_to_wav(self, input_path: str, output_path: str) -> str:
        """
        Converts input audio file to 16 kHz 16-bit Mono WAV format using FFmpeg.
        """
        input_p = Path(input_path).resolve()
        output_p = Path(output_path).resolve()

        if not input_p.exists():
            raise AudioPreprocessingError(f"Input audio file not found: {input_path}")

        ffmpeg_cmd = self.ffmpeg_path or "ffmpeg"
        cmd = [
            ffmpeg_cmd,
            "-y",
            "-i", str(input_p),
            "-ac", "1",
            "-ar", "16000",
            "-sample_fmt", "s16",
            str(output_p)
        ]

        logger.info(f"Running FFmpeg audio normalization: {' '.join(cmd)}")

        try:
            # Ensure PATH environment variable contains FFmpeg bin directory
            env = os.environ.copy()
            if self.ffmpeg_path and os.path.exists(self.ffmpeg_path):
                f_dir = str(Path(self.ffmpeg_path).parent)
                env["PATH"] = f_dir + os.pathsep + env.get("PATH", "")

            process = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                check=True
            )
            logger.info(f"Audio file normalized successfully to: {output_p}")
            return str(output_p)
        except subprocess.CalledProcessError as e:
            err_msg = e.stderr.decode("utf-8", errors="ignore")
            logger.error(f"FFmpeg conversion failed: {err_msg}")
            raise AudioPreprocessingError(f"FFmpeg audio normalization failed: {err_msg[:200]}")
        except Exception as e:
            logger.error(f"Error during audio conversion: {e}")
            raise AudioPreprocessingError(f"Failed to normalize audio file: {e}")

    def get_audio_duration(self, filepath: str) -> float:
        """
        Calculates audio duration in seconds using wave or soundfile.
        """
        p = Path(filepath).resolve()
        if not p.exists():
            return 0.0

        try:
            import wave
            with wave.open(str(p), "rb") as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                if rate > 0:
                    return round(float(frames) / float(rate), 2)
        except Exception:
            pass

        try:
            import soundfile as sf
            info = sf.info(str(p))
            return round(info.duration, 2)
        except Exception:
            pass

        return 0.0

audio_preprocessor = AudioPreprocessor()
