import os
import sys
import numpy as np
import soundfile as sf
import torch

from app.services.audio.audio_preprocessor import audio_preprocessor
from indic_asr_onnx.transcriber import IndicTranscriber

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

transcriber = IndicTranscriber()
# Use an already normalized file from uploads
norm_path = r"uploads\210e9367-abe8-4f03-8791-1e090b18a49f_norm.wav"

text = transcriber.transcribe_rnnt(norm_path, "hi")
with open("test_output.txt", "w", encoding="utf-8") as f:
    f.write(text)
