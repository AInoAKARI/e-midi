from __future__ import annotations

from dataclasses import dataclass
import struct
import time

HEADER = b"\xE0\x4D"
FRAME_SIZE = 23


def _clip_midi(value: int) -> int:
    return max(0, min(127, int(value)))


def _encode_source_id(source_id: str) -> bytes:
    ascii_value = source_id.encode("ascii", errors="strict")
    return ascii_value[:8].ljust(8, b"\x00")


@dataclass(slots=True)
class EmotionState:
    valence: int
    arousal: int
    tension: int
    bounce: bool = False
    source_id: str = "unknown"
    timestamp: int = 0

    def __post_init__(self) -> None:
        self.valence = _clip_midi(self.valence)
        self.arousal = _clip_midi(self.arousal)
        self.tension = _clip_midi(self.tension)
        self.timestamp = int(self.timestamp or time.time_ns() // 1_000_000)

    def to_bytes(self) -> bytes:
        flags = 0x01 if self.bounce else 0x00
        payload = struct.pack(
            "<2sBBBB8sQB",
            HEADER,
            self.valence,
            self.arousal,
            self.tension,
            flags,
            _encode_source_id(self.source_id),
            self.timestamp,
            0,
        )
        if len(payload) != FRAME_SIZE:
            raise ValueError(f"E-MIDI frame must be {FRAME_SIZE} bytes, got {len(payload)}")
        return payload
