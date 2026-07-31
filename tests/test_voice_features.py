from __future__ import annotations

import io
import wave

import numpy as np
import pytest

from voice.features import extract_wav_features


def _wav_bytes(signal: np.ndarray, sample_rate: int = 16_000) -> bytes:
    pcm = np.clip(signal, -1.0, 1.0)
    pcm = (pcm * 32767).astype("<i2")
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(pcm.tobytes())
    return buffer.getvalue()


def test_extracts_signal_features_without_persisting_audio() -> None:
    sample_rate = 16_000
    silence = np.zeros(int(sample_rate * 0.25), dtype=np.float32)
    time = np.arange(int(sample_rate * 0.75)) / sample_rate
    tone = 0.25 * np.sin(2 * np.pi * 220 * time)
    audio = np.concatenate([silence, tone]).astype(np.float32)

    features = extract_wav_features(
        _wav_bytes(audio), transcript="今日は一気に全部進めて"
    )

    assert 990 <= features.duration_ms <= 1010
    assert features.raw_audio_persisted is False
    assert features.extraction_mode == "signal_features_v1"
    assert features.valence == 64
    assert features.valence_source == "neutral_without_semantics"
    assert features.velocity > 0
    assert features.arousal > 0
    assert features.silence_ratio > 0.10
    assert features.pitch_hz_mean is not None
    assert 205 <= features.pitch_hz_mean <= 235
    assert features.speech_rate_chars_per_minute is not None


def test_rejects_non_wav_input() -> None:
    with pytest.raises(ValueError, match="valid PCM WAV"):
        extract_wav_features(b"not-a-wav")
