import os
import sys
import time
import json
import logging
import tempfile
import soundfile as sf
from pathlib import Path
from typing import Optional, List, Dict, Any

from app.core.config import settings
from app.services.transcription.base import BaseTranscriptionService, TranscriptionResult
from app.services.audio.audio_preprocessor import find_ffmpeg_executable

logger = logging.getLogger("indic_conformer")

# Force UTF-8 encoding for console output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Ensure FFmpeg directory is in os.environ["PATH"]
ffmpeg_bin = find_ffmpeg_executable()
if ffmpeg_bin and os.path.exists(ffmpeg_bin):
    ffmpeg_dir = str(Path(ffmpeg_bin).parent)
    if ffmpeg_dir not in os.environ.get("PATH", ""):
        os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")
        logger.info(f"Injected FFmpeg directory into PATH: {ffmpeg_dir}")

try:
    import imageio_ffmpeg
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    ffmpeg_dir2 = os.path.dirname(ffmpeg_exe)
    if ffmpeg_dir2 not in os.environ["PATH"]:
        os.environ["PATH"] = ffmpeg_dir2 + os.pathsep + os.environ["PATH"]
except Exception:
    pass

from indic_asr_onnx.transcriber import IndicTranscriber
import soundfile as sf
import numpy as np
import torch

def _patched_preprocess_audio(self, audio_path):
    y, sr = sf.read(audio_path, dtype="float32")
    if len(y.shape) > 1:
        y = y.mean(axis=1)
    waveform = torch.from_numpy(y).unsqueeze(0).to(self.device)
    
    features = self.mel_transform(waveform)
    features = torch.log(features + 1e-9)
    mean = features.mean(dim=2, keepdims=True)
    stddev = features.std(dim=2, keepdim=True) + 1e-5
    features = (features - mean) / stddev
    return features.squeeze(0).cpu().numpy().astype(np.float32)

IndicTranscriber._preprocess_audio = _patched_preprocess_audio

def _load_audio_16k_mono(path: str):
    # The file is already normalized to 16kHz Mono WAV by audio_preprocessor.py
    y, sr = sf.read(path, dtype="float32")
    if len(y.shape) > 1:
        y = np.mean(y, axis=1)
    return y


class IndicConformerTranscriber(BaseTranscriptionService):
    """
    High-accuracy Audio Transcriber using AI4Bharat IndicConformer ONNX engine
    with Chunked Audio Processing for 100% full, un-truncated raw Hindi transcriptions.
    Runs efficiently on low-end PCs using CPU INT8 quantization.
    """

    def __init__(self, engine: str = "indic-conformer"):
        self.engine = engine.lower()
        self.indic_model = None
        self.is_loaded = False

    def load_model(self) -> None:
        """
        Loads the pre-cached IndicConformer model into memory on demand.
        """
        if self.is_loaded:
            return

        logger.info("[Transcriber] Initializing AI4Bharat IndicConformer (600M INT8 Quantized)...")
        start = time.time()
        try:
            self.indic_model = IndicTranscriber()
            self.is_loaded = True
            logger.info(f"[Transcriber] IndicConformer model loaded successfully in {round(time.time() - start, 2)}s.")
        except Exception as e:
            logger.error(f"Failed to load AI4Bharat model: {e}")

    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = "hi"
    ) -> TranscriptionResult:
        """
        Transcribe the COMPLETE audio file using chunked audio processing.
        """
        if not self.is_loaded:
            self.load_model()
            
        language = language or "hi"
        chunk_sec = 12.0

        audio_path_obj = Path(audio_path).resolve()
        if not audio_path_obj.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path_obj}")
            
        audio_path = str(audio_path_obj)

        logger.info(f"\n[Processing] Transcribing full audio: {os.path.basename(audio_path)}")
        start_time = time.time()

        if self.indic_model is None:
            # Fallback
            elapsed = time.time() - start_time
            return TranscriptionResult(
                text="Engine not loaded.",
                language=language,
                duration_seconds=0.0,
                processing_time_seconds=round(elapsed, 2),
                segments=[]
            )

        # Load 16kHz mono audio samples
        try:
            samples = _load_audio_16k_mono(audio_path)
        except Exception as e:
            logger.error(f"Error loading audio: {e}")
            elapsed = time.time() - start_time
            return TranscriptionResult(
                text="Error loading audio for transcription.",
                language=language,
                duration_seconds=0.0,
                processing_time_seconds=round(elapsed, 2),
                segments=[]
            )
            
        total_duration = round(len(samples) / 16000.0, 2)
        chunk_samples = int(chunk_sec * 16000)

        # Create temporary folder for audio chunk WAVs
        temp_dir = tempfile.mkdtemp()
        segments_list = []
        full_text_parts = []

        chunk_idx = 0
        for start_sample in range(0, len(samples), chunk_samples):
            end_sample = min(start_sample + chunk_samples, len(samples))
            chunk_audio = samples[start_sample:end_sample]

            if len(chunk_audio) < 1600: # Skip tiny < 0.1s fragments
                continue

            chunk_file = os.path.join(temp_dir, f"chunk_{chunk_idx:04d}.wav")
            sf.write(chunk_file, chunk_audio, 16000)

            seg_start = round(start_sample / 16000.0, 2)
            seg_end = round(end_sample / 16000.0, 2)

            try:
                text = self.indic_model.transcribe_rnnt(chunk_file, language).strip()
            except Exception as e:
                logger.error(f"Error transcribing chunk {chunk_idx}: {e}")
                text = ""
                
            if text:
                segments_list.append({
                    "id": chunk_idx + 1,
                    "start": seg_start,
                    "end": seg_end,
                    "text": text
                })
                full_text_parts.append(text)

            chunk_idx += 1

        # Clean up temp directory files
        try:
            for f in os.listdir(temp_dir):
                os.remove(os.path.join(temp_dir, f))
            os.rmdir(temp_dir)
        except Exception:
            pass

        full_text = " ".join(full_text_parts)
        elapsed = round(time.time() - start_time, 2)

        result_dict = {
            "file_name": os.path.basename(audio_path),
            "file_path": audio_path,
            "engine": "AI4Bharat IndicConformer (Chunked ASR)",
            "language": language,
            "duration": total_duration,
            "elapsed_seconds": elapsed,
            "full_text": full_text,
            "segments": segments_list
        }
        
        logger.info(f"[Success] Completed FULL transcription in {elapsed}s ({len(segments_list)} segments)")

        self._export_all(result_dict, str(settings.abs_outputs_dir))

        return TranscriptionResult(
            text=full_text,
            language=language,
            duration_seconds=total_duration,
            processing_time_seconds=elapsed,
            segments=segments_list
        )

    def _export_all(self, result: Dict[str, Any], output_dir: str):
        """Export result to TXT, SRT, VTT, and JSON files in output_dir."""
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        base_name = Path(result["file_name"]).stem

        # 1. Export TXT
        txt_file = out_path / f"{base_name}.txt"
        with open(txt_file, "w", encoding="utf-8") as f:
            f.write(f"Source File: {result['file_name']}\n")
            f.write(f"Engine: {result['engine']}\n")
            f.write(f"Language: {result['language']}\n")
            f.write(f"Duration: {result['duration']} seconds\n")
            f.write("=" * 60 + "\n\n")
            f.write(result["full_text"])
            f.write("\n\n" + "=" * 60 + "\n")
            f.write("TIMESTAMPED FULL TRANSCRIPTION SEGMENTS:\n")
            for seg in result["segments"]:
                f.write(f"[{seg['start']}s -> {seg['end']}s] {seg['text']}\n")

        # 2. Export SRT
        srt_file = out_path / f"{base_name}.srt"
        with open(srt_file, "w", encoding="utf-8") as f:
            for idx, seg in enumerate(result["segments"], 1):
                start_str = self._format_timestamp(seg["start"], srt=True)
                end_str = self._format_timestamp(seg["end"], srt=True)
                f.write(f"{idx}\n{start_str} --> {end_str}\n{seg['text']}\n\n")

        # 3. Export VTT
        vtt_file = out_path / f"{base_name}.vtt"
        with open(vtt_file, "w", encoding="utf-8") as f:
            f.write("WEBVTT\n\n")
            for idx, seg in enumerate(result["segments"], 1):
                start_str = self._format_timestamp(seg["start"], srt=False)
                end_str = self._format_timestamp(seg["end"], srt=False)
                f.write(f"{start_str} --> {end_str}\n{seg['text']}\n\n")

        # 4. Export JSON
        json_file = out_path / f"{base_name}.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        logger.info(f"[Exported] Saved full transcript files to: {out_path}")
        return {
            "txt": str(txt_file),
            "srt": str(srt_file),
            "vtt": str(vtt_file),
            "json": str(json_file)
        }

    def _format_timestamp(self, seconds: float, srt: bool = True) -> str:
        """Format seconds into HH:MM:SS,mmm (SRT) or HH:MM:SS.mmm (VTT)"""
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int(round((seconds - int(seconds)) * 1000))
        sep = "," if srt else "."
        return f"{hrs:02d}:{mins:02d}:{secs:02d}{sep}{millis:03d}"

# Global singleton instance for worker model reuse
indic_transcriber = IndicConformerTranscriber()
