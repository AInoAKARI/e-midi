from core.encoder import EmotionState, FRAME_SIZE, HEADER


def test_to_bytes_has_expected_layout():
    state = EmotionState(
        valence=80,
        arousal=60,
        tension=30,
        bounce=True,
        source_id="akari",
        timestamp=123456789,
    )

    payload = state.to_bytes()

    assert len(payload) == FRAME_SIZE
    assert payload[:2] == HEADER
    assert payload[2] == 80
    assert payload[3] == 60
    assert payload[4] == 30
    assert payload[5] == 1
    assert payload[6:14].startswith(b"akari")
    assert payload[-1] == 0


def test_values_are_clipped_and_source_is_truncated():
    state = EmotionState(
        valence=999,
        arousal=-20,
        tension=160,
        source_id="toolong-source",
        timestamp=1,
    )

    payload = state.to_bytes()

    assert payload[2] == 127
    assert payload[3] == 0
    assert payload[4] == 127
    assert payload[6:14] == b"toolong-"
