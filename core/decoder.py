from __future__ import annotations

import struct

from core.encoder import EmotionState, FRAME_SIZE, HEADER


def from_bytes(data: bytes) -> EmotionState:
    if len(data) != FRAME_SIZE:
        raise ValueError(f"E-MIDI frame must be {FRAME_SIZE} bytes")

    header, valence, arousal, tension, flags, source_raw, timestamp, reserved = struct.unpack(
        "<2sBBBB8sQB",
        data,
    )

    if header != HEADER:
        raise ValueError("Invalid E-MIDI header")
    if reserved != 0:
        raise ValueError("Reserved byte must be zero")

    source_id = source_raw.rstrip(b"\x00").decode("ascii")
    return EmotionState(
        valence=valence,
        arousal=arousal,
        tension=tension,
        bounce=bool(flags & 0x01),
        source_id=source_id or "unknown",
        timestamp=timestamp,
    )
