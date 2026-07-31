from __future__ import annotations

import io
import math
import wave
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np


@dataclass(frozen=True)
class VoiceFeatures:
    duration_ms: int
    sample_rate: int
    channels: int
    rms_mean: float
    rms_peak: float
    rms_curve: list[float]
    silence_ratio: float
    zero_crossing_rate: float
    pitch_hz_mean: float | None
    pitch_hz_curve: list[float]
    speech_rate_chars_per_minute: float | None
    velocity: int
    valence: int
    arousal: int
    tension: int
    confidence: float
    extraction_mode: str = "signal_features_v1"
    raw_audio_persisted: bool = False
    valence_source: str = "neutral_without_semantics"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _pcm_to_float(raw: bytes, sample_width: int, channels: int) -> np.ndarray:
    if sample_width == 1:
        pcm = np.frombuffer(raw, dtype=np.uint8).astype(np.float32)
        pcm = (pcm - 128.0) / 128.0
    elif sample_width == 2:
        pcm = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
    elif sample_width == 3:
        packed = np.frombuffer(raw, dtype=np.uint8)
        if len(packed) % 3:
            raise ValueError("invalid 24-bit PCM byte length")
        triplets = packed.reshape(-1, 3).astype(np.int32)
        values = triplets[:, 0] | (triplets[:, 1] << 8) | (triplets[:, 2] << 16)
        values = np.where(values & 0x800000, values - 0x1000000, values)
        pcm = values.astype(np.float32) / 8388608.0
    elif sample_width == 4:
        pcm = np.frombuffer(raw, dtype="<i4").astype(np.float32) / 2147483648.0
    else:
        raise ValueError(f"unsupported PCM sample width: {sample_width}")

    if channels < 1:
        raise ValueError("WAV must contain at least one channel")
    if len(pcm) % channels:
        raise ValueError("PCM sample count is not divisible by channel count")
    if channels > 1:
        pcm = pcm.reshape(-1, channels).mean(axis=1)
    return np.clip(pcm, -1.0, 1.0)


def _sample_curve(values: np.ndarray, limit: int = 50) -> list[float]:
    if values.size == 0:
        return []
    if values.size <= limit:
        sampled = values
    else:
        indexes = np.linspace(0, values.size - 1, limit).astype(int)
        sampled = values[indexes]
    return [round(float(value), 6) for value in sampled]


def _frame_signal(signal: np.ndarray, frame_length: int, hop_length: int) -> np.ndarray:
    if signal.size == 0:
        return np.empty((0, frame_length), dtype=np.float32)
    if signal.size < frame_length:
        padded = np.pad(signal, (0, frame_length - signal.size))
        return padded.reshape(1, -1)
    frame_count = 1 + math.ceil((signal.size - frame_length) / hop_length)
    total = (frame_count - 1) * hop_length + frame_length
    padded = np.pad(signal, (0, total - signal.size))
    shape = (frame_count, frame_length)
    strides = (padded.strides[0] * hop_length, padded.strides[0])
    return np.lib.stride_tricks.as_strided(
        padded, shape=shape, strides=strides
    ).copy()


def _estimate_pitch(frame: np.ndarray, sample_rate: int) -> tuple[float | None, float]:
    centered = frame.astype(np.float64) - float(np.mean(frame))
    energy = float(np.dot(centered, centered))
    if energy <= 1e-8:
        return None, 0.0
    centered *= np.hanning(centered.size)
    autocorr = np.correlate(centered, centered, mode="full")[centered.size - 1 :]
    min_lag = max(1, int(sample_rate / 400.0))
    max_lag = min(autocorr.size - 1, int(sample_rate / 70.0))
    if max_lag <= min_lag:
        return None, 0.0
    search = autocorr[min_lag : max_lag + 1]
    relative_index = int(np.argmax(search))
    lag = min_lag + relative_index
    confidence = float(search[relative_index] / max(autocorr[0], 1e-9))
    if confidence < 0.25:
        return None, confidence
    return float(sample_rate / lag), min(1.0, confidence)


def extract_wav_features(audio_bytes: bytes, transcript: str | None = None) -> VoiceFeatures:
    """Extract E-MIDI-ready signal features without persisting the raw WAV."""
    if not audio_bytes:
        raise ValueError("audio body is empty")

    try:
        with wave.open(io.BytesIO(audio_bytes), "rb") as wav:
            channels = wav.getnchannels()
            sample_rate = wav.getframerate()
            sample_width = wav.getsampwidth()
            frame_count = wav.getnframes()
            compression = wav.getcomptype()
            if compression != "NONE":
                raise ValueError("only uncompressed PCM WAV is supported")
            raw = wav.readframes(frame_count)
    except wave.Error as exc:
        raise ValueError("body must be a valid PCM WAV file") from exc

    if sample_rate < 8_000 or sample_rate > 192_000:
        raise ValueError("sample rate must be between 8 kHz and 192 kHz")

    signal = _pcm_to_float(raw, sample_width, channels)
    if signal.size == 0:
        raise ValueError("WAV contains no samples")

    duration_seconds = signal.size / sample_rate
    frame_length = max(128, int(sample_rate * 0.025))
    hop_length = max(64, int(sample_rate * 0.010))
    frames = _frame_signal(signal, frame_length, hop_length)

    rms = np.sqrt(np.mean(np.square(frames, dtype=np.float64), axis=1))
    rms_mean = float(np.mean(rms))
    rms_peak = float(np.max(rms))
    silence_threshold = max(0.006, rms_peak * 0.12)
    silence_ratio = float(np.mean(rms <= silence_threshold))

    signs = np.signbit(frames)
    zcr_per_frame = np.mean(signs[:, 1:] != signs[:, :-1], axis=1)
    zero_crossing_rate = float(np.mean(zcr_per_frame))

    candidate_indexes = np.linspace(
        0, frames.shape[0] - 1, min(50, frames.shape[0])
    ).astype(int)
    pitch_values: list[float] = []
    pitch_confidences: list[float] = []
    for index in candidate_indexes:
        if rms[index] <= silence_threshold:
            continue
        pitch, confidence = _estimate_pitch(frames[index], sample_rate)
        if pitch is not None:
            pitch_values.append(pitch)
            pitch_confidences.append(confidence)

    pitch_array = np.asarray(pitch_values, dtype=np.float64)
    pitch_hz_mean = float(np.median(pitch_array)) if pitch_array.size else None
    pitch_curve = _sample_curve(pitch_array)

    speech_rate: float | None = None
    if transcript and duration_seconds > 0:
        char_count = len("".join(transcript.split()))
        speech_rate = char_count / (duration_seconds / 60.0)

    loudness = float(np.clip(rms_mean / 0.18, 0.0, 1.0))
    peak_factor = float(np.clip(rms_peak / 0.45, 0.0, 1.0))
    continuity = 1.0 - float(np.clip(silence_ratio, 0.0, 1.0))
    zcr_norm = float(np.clip(zero_crossing_rate / 0.20, 0.0, 1.0))
    rate_norm = (
        0.5
        if speech_rate is None
        else float(np.clip(speech_rate / 420.0, 0.0, 1.0))
    )

    pitch_variability = 0.0
    if pitch_array.size >= 3 and pitch_hz_mean:
        pitch_variability = float(
            np.clip(np.std(pitch_array) / max(pitch_hz_mean, 1.0), 0.0, 1.0)
        )

    velocity = int(round(127 * (0.65 * loudness + 0.35 * peak_factor)))
    arousal = int(
        round(
            127
            * np.clip(
                0.45 * loudness
                + 0.25 * rate_norm
                + 0.20 * continuity
                + 0.10 * zcr_norm,
                0.0,
                1.0,
            )
        )
    )
    tension = int(
        round(
            127
            * np.clip(
                0.35 * zcr_norm
                + 0.25 * pitch_variability
                + 0.20 * rate_norm
                + 0.20 * (1.0 - continuity),
                0.0,
                1.0,
            )
        )
    )

    pitch_confidence = (
        float(np.mean(pitch_confidences)) if pitch_confidences else 0.0
    )
    confidence = float(
        np.clip(0.35 + 0.35 * continuity + 0.30 * pitch_confidence, 0.0, 1.0)
    )

    return VoiceFeatures(
        duration_ms=int(round(duration_seconds * 1000)),
        sample_rate=sample_rate,
        channels=channels,
        rms_mean=round(rms_mean, 6),
        rms_peak=round(rms_peak, 6),
        rms_curve=_sample_curve(rms),
        silence_ratio=round(silence_ratio, 6),
        zero_crossing_rate=round(zero_crossing_rate, 6),
        pitch_hz_mean=(
            round(pitch_hz_mean, 3) if pitch_hz_mean is not None else None
        ),
        pitch_hz_curve=pitch_curve,
        speech_rate_chars_per_minute=(
            round(speech_rate, 3) if speech_rate is not None else None
        ),
        velocity=max(0, min(127, velocity)),
        valence=64,
        arousal=max(0, min(127, arousal)),
        tension=max(0, min(127, tension)),
        confidence=round(confidence, 6),
    )
