"""
mic_emitter.py — Realtime microphone audio → E-MIDI emotion-bus emitter.

Captures audio from the default mic, extracts RMS/spectral features,
maps them to valence/arousal/tension, and streams to the local emotion-bus
via HTTP POST every EMIT_INTERVAL_MS milliseconds.

Usage:
    python agents/mic_emitter.py
    python agents/mic_emitter.py --url http://localhost:8765/api/emotion --interval 100
    python agents/mic_emitter.py --list-devices
"""
from __future__ import annotations

import argparse
import math
import sys
import time
import threading
from collections import deque

import numpy as np
import requests
import sounddevice as sd

SAMPLE_RATE = 16000
BLOCK_SIZE = 512
EMIT_INTERVAL_MS = 80

_audio_buffer: deque[np.ndarray] = deque(maxlen=10)
_lock = threading.Lock()


def _audio_callback(indata: np.ndarray, frames: int, time_info, status) -> None:
    if status:
        pass
    mono = indata[:, 0] if indata.ndim > 1 else indata.flatten()
    with _lock:
        _audio_buffer.append(mono.copy())


def _extract_features(chunk: np.ndarray) -> tuple[float, float, float]:
    """Returns (valence, arousal, tension) each 0.0–127.0."""
    if len(chunk) == 0:
        return 64.0, 64.0, 64.0

    rms = float(np.sqrt(np.mean(chunk ** 2)))
    # arousal: volume energy (0 = silent, 127 = loud)
    arousal = min(127.0, rms * 3000.0)

    # spectral centroid → maps to tension (high freq = tense)
    fft = np.abs(np.fft.rfft(chunk * np.hanning(len(chunk))))
    freqs = np.fft.rfftfreq(len(chunk), d=1.0 / SAMPLE_RATE)
    if fft.sum() > 1e-9:
        centroid = float(np.sum(freqs * fft) / fft.sum())
    else:
        centroid = 1000.0
    tension = float(np.clip((centroid - 500.0) / 70.0, 0.0, 127.0))

    # spectral flux in low-freq band → rough valence proxy
    # High energy below 300Hz (bass/warmth) → higher valence
    low_mask = freqs < 300
    low_energy = float(fft[low_mask].sum()) if low_mask.any() else 0.0
    total_energy = float(fft.sum()) + 1e-12
    low_ratio = low_energy / total_energy
    valence = float(np.clip(40.0 + low_ratio * 80.0, 0.0, 127.0))

    return valence, arousal, tension


def _emit(url: str, valence: float, arousal: float, tension: float, bounce: bool, source_id: str) -> None:
    try:
        requests.post(
            url,
            json={
                "valence": int(valence),
                "arousal": int(arousal),
                "tension": int(tension),
                "bounce": bounce,
                "source_id": source_id,
                "timestamp": int(time.time() * 1000),
            },
            timeout=0.5,
        )
    except Exception:
        pass


def run(url: str, interval_ms: int, source_id: str) -> None:
    prev_arousal = 64.0
    stream = sd.InputStream(
        samplerate=SAMPLE_RATE,
        blocksize=BLOCK_SIZE,
        channels=1,
        dtype="float32",
        callback=_audio_callback,
    )
    print(f"[mic_emitter] listening → {url}  (Ctrl+C to stop)", flush=True)
    with stream:
        while True:
            time.sleep(interval_ms / 1000.0)
            with _lock:
                if not _audio_buffer:
                    continue
                chunk = np.concatenate(list(_audio_buffer))

            valence, arousal, tension = _extract_features(chunk)
            bounce = (arousal - prev_arousal) > 25
            prev_arousal = arousal
            _emit(url, valence, arousal, tension, bounce, source_id)
            bar = "#" * int(arousal / 10)
            print(
                f"\r  V={int(valence):3d} A={int(arousal):3d} T={int(tension):3d}  {bar:<13}",
                end="",
                flush=True,
            )


def list_devices() -> None:
    print(sd.query_devices())


def main() -> None:
    parser = argparse.ArgumentParser(description="Mic → E-MIDI emotion-bus emitter")
    parser.add_argument("--url", default="http://localhost:8765/api/emotion")
    parser.add_argument("--interval", type=int, default=EMIT_INTERVAL_MS, help="Emit interval in ms")
    parser.add_argument("--source-id", default="mic")
    parser.add_argument("--list-devices", action="store_true")
    args = parser.parse_args()

    if args.list_devices:
        list_devices()
        return

    try:
        run(args.url, args.interval, args.source_id)
    except KeyboardInterrupt:
        print("\n[mic_emitter] stopped.")


if __name__ == "__main__":
    main()
