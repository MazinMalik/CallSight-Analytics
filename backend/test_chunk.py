import os
import sys
import numpy as np
import soundfile as sf
import torch
import tempfile

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
norm_path = r"uploads\210e9367-abe8-4f03-8791-1e090b18a49f_norm.wav"

# Simulate _load_audio_16k_mono
y, sr = sf.read(norm_path, dtype="float32")
if len(y.shape) > 1:
    y = np.mean(y, axis=1)
samples = y

chunk_samples = int(12.0 * 16000)
temp_dir = tempfile.mkdtemp()
chunk_file = os.path.join(temp_dir, "chunk_0000.wav")
chunk_audio = samples[0:chunk_samples]
sf.write(chunk_file, chunk_audio, 16000)

text = transcriber.transcribe_rnnt(chunk_file, "hi")
print(f"Chunk Transcript:\n{text}")
