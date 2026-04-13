"""
Audio Utilities — resampling and format conversions for Telephony (Twilio).

Twilio uses 8000Hz, mono, mu-law encoded audio (G.711).
Our internal VAD/STT pipeline prefers 16000Hz, float32 PCM.
Our Kokoro TTS outputs 24000Hz, float32 PCM.
"""

import audioop
import numpy as np
import scipy.signal

def mulaw_to_float32_16khz(mulaw_bytes: bytes) -> np.ndarray:
    """
    Decodes 8kHz mu-law bytes into 16kHz float32 numpy array.
    """
    # 1. Decode mu-law to 16-bit PCM (8kHz)
    pcm_8k_bytes = audioop.ulaw2lin(mulaw_bytes, 2)
    
    # 2. Convert bytes to int16 numpy array
    pcm_8k_int16 = np.frombuffer(pcm_8k_bytes, dtype=np.int16)
    
    # 3. Resample from 8kHz to 16kHz
    num_samples_16k = len(pcm_8k_int16) * 2
    pcm_16k_int16 = scipy.signal.resample(pcm_8k_int16, num_samples_16k)
    
    # 4. Convert to float32 range [-1.0, 1.0]
    return (pcm_16k_int16 / 32768.0).astype(np.float32)

def float32_24khz_to_mulaw(audio_f32: np.ndarray) -> bytes:
    """
    Converts 24kHz float32 numpy array (from TTS) directly to 8kHz mu-law bytes.
    """
    # 1. Resample from 24kHz to 8kHz
    num_samples_8k = len(audio_f32) // 3
    if num_samples_8k == 0:
        return b""
        
    audio_8k_f32 = scipy.signal.resample(audio_f32, num_samples_8k)
    
    # 2. Convert float32 [-1.0, 1.0] to int16
    audio_8k_int16 = np.clip(audio_8k_f32 * 32767.0, -32768, 32767).astype(np.int16)
    
    # 3. Encode 16-bit PCM to mu-law bytes
    mulaw_bytes = audioop.lin2ulaw(audio_8k_int16.tobytes(), 2)
    return mulaw_bytes

def float32_16khz_to_mulaw(audio_f32: np.ndarray) -> bytes:
    """
    Converts 16kHz float32 numpy array (for standard responses) to 8kHz mu-law bytes.
    """
    # 1. Resample from 16kHz to 8kHz
    num_samples_8k = len(audio_f32) // 2
    if num_samples_8k == 0:
        return b""
        
    audio_8k_f32 = scipy.signal.resample(audio_f32, num_samples_8k)
    audio_8k_int16 = np.clip(audio_8k_f32 * 32767.0, -32768, 32767).astype(np.int16)
    mulaw_bytes = audioop.lin2ulaw(audio_8k_int16.tobytes(), 2)
    return mulaw_bytes
