import os
import sys
import io
import json
import time
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
import soundfile as sf
import numpy as np

# Force UTF-8 encoding for console output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Ensure imageio_ffmpeg is in PATH for standalone ffmpeg access
try:
    import imageio_ffmpeg
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    ffmpeg_dir = os.path.dirname(ffmpeg_exe)
    if ffmpeg_dir not in os.environ["PATH"]:
        os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ["PATH"]
except Exception:
    pass

from indic_asr_onnx.transcriber import IndicTranscriber, _load_audio_16k_mono


class AudioTranscriber:
    """
    High-accuracy Audio Transcriber using AI4Bharat IndicConformer ONNX engine
    with Chunked Audio Processing for 100% full, un-truncated raw Hindi transcriptions.
    Runs efficiently on low-end PCs using CPU INT8 quantization.
    """

    def __init__(
        self,
        engine: str = "indic-conformer",
        model_size: str = "base",
        device: str = "cpu"
    ):
        self.engine = engine.lower()
        self.model_size = model_size
        self.device = device

        if self.engine == "indic-conformer":
            print("[Transcriber] Initializing AI4Bharat IndicConformer (600M INT8 Quantized)...")
            self.indic_model = IndicTranscriber()
            print("[Transcriber] IndicConformer model loaded successfully!")
        else:
            from faster_whisper import WhisperModel
            print(f"[Transcriber] Initializing Faster-Whisper '{model_size}'...")
            self.whisper_model = WhisperModel(
                model_size,
                device="cpu",
                compute_type="int8",
                download_root=os.path.join(os.path.expanduser("~"), ".cache", "whisper_models")
            )
            print(f"[Transcriber] Faster-Whisper model loaded!")

    def transcribe(
        self,
        audio_path: str,
        language: str = "hi",
        chunk_sec: float = 12.0
    ) -> Dict[str, Any]:
        """
        Transcribe the COMPLETE audio file using chunked audio processing.
        """
        audio_path = str(Path(audio_path).resolve())
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        print(f"\n[Processing] Transcribing full audio: {os.path.basename(audio_path)}")
        start_time = time.time()

        if self.engine == "indic-conformer":
            # Load 16kHz mono audio samples
            samples = _load_audio_16k_mono(audio_path)
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

                text = self.indic_model.transcribe_rnnt(chunk_file, language).strip()
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

            result = {
                "file_name": os.path.basename(audio_path),
                "file_path": audio_path,
                "engine": "AI4Bharat IndicConformer (Chunked ASR)",
                "language": language,
                "duration": total_duration,
                "elapsed_seconds": elapsed,
                "full_text": full_text,
                "segments": segments_list
            }

        else:
            # Fallback Whisper engine
            segments_gen, info = self.whisper_model.transcribe(
                audio_path,
                beam_size=5,
                language=language,
                vad_filter=True,
                word_timestamps=True
            )
            segments_list = []
            full_text_parts = []
            for seg in segments_gen:
                segments_list.append({
                    "id": seg.id,
                    "start": round(seg.start, 2),
                    "end": round(seg.end, 2),
                    "text": seg.text.strip(),
                    "words": []
                })
                full_text_parts.append(seg.text.strip())

            elapsed = round(time.time() - start_time, 2)
            result = {
                "file_name": os.path.basename(audio_path),
                "file_path": audio_path,
                "engine": f"Faster-Whisper ({self.model_size})",
                "language": info.language,
                "duration": round(info.duration, 2),
                "elapsed_seconds": elapsed,
                "full_text": " ".join(full_text_parts),
                "segments": segments_list
            }

        print(f"[Success] Completed FULL transcription in {elapsed}s ({len(result['segments'])} segments)")
        return result

    @staticmethod
    def export_all(result: Dict[str, Any], output_dir: str):
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
                start_str = AudioTranscriber.format_timestamp(seg["start"], srt=True)
                end_str = AudioTranscriber.format_timestamp(seg["end"], srt=True)
                f.write(f"{idx}\n{start_str} --> {end_str}\n{seg['text']}\n\n")

        # 3. Export VTT
        vtt_file = out_path / f"{base_name}.vtt"
        with open(vtt_file, "w", encoding="utf-8") as f:
            f.write("WEBVTT\n\n")
            for idx, seg in enumerate(result["segments"], 1):
                start_str = AudioTranscriber.format_timestamp(seg["start"], srt=False)
                end_str = AudioTranscriber.format_timestamp(seg["end"], srt=False)
                f.write(f"{start_str} --> {end_str}\n{seg['text']}\n\n")

        # 4. Export JSON
        json_file = out_path / f"{base_name}.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"[Exported] Saved full transcript files to: {out_path}")
        return {
            "txt": str(txt_file),
            "srt": str(srt_file),
            "vtt": str(vtt_file),
            "json": str(json_file)
        }

    @staticmethod
    def format_timestamp(seconds: float, srt: bool = True) -> str:
        """Format seconds into HH:MM:SS,mmm (SRT) or HH:MM:SS.mmm (VTT)"""
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int(round((seconds - int(seconds)) * 1000))
        sep = "," if srt else "."
        return f"{hrs:02d}:{mins:02d}:{secs:02d}{sep}{millis:03d}"
