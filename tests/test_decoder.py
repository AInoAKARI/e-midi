import pytest

from core.decoder import from_bytes
from core.encoder import EmotionState


def test_from_bytes_round_trip():
    original = EmotionState(
        valence=22,
        arousal=91,
        tension=45,
        bounce=True,
        source_id="kiratan",
        timestamp=987654321,
    )

    restored = from_bytes(original.to_bytes())

    assert restored == original


def test_from_bytes_rejects_invalid_header():
    payload = bytearray(EmotionState(1, 2, 3, timestamp=1).to_bytes())
    payload[0] = 0x00

    with pytest.raises(ValueError):
        from_bytes(bytes(payload))
