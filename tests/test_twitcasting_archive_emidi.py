import io
import math
import wave

from bridge.twitcasting_archive_emidi import analyzable_movies, build_voice_event


def make_wav(seconds: float = 0.5, sample_rate: int = 16000) -> bytes:
    frames = bytearray()
    for index in range(int(seconds * sample_rate)):
        sample = int(9000 * math.sin(2 * math.pi * 180 * index / sample_rate))
        frames += int(sample).to_bytes(2, byteorder="little", signed=True)
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(bytes(frames))
    return buffer.getvalue()


def test_analyzable_movies_requires_recording_and_hls():
    movies = [
        {"id": "1", "is_recorded": True, "hls_url": "https://example.test/a.m3u8"},
        {"id": "2", "is_recorded": False, "hls_url": "https://example.test/b.m3u8"},
        {"id": "3", "is_recorded": True, "hls_url": None},
    ]
    assert [movie["id"] for movie in analyzable_movies(movies)] == ["1"]


def test_voice_event_reuses_voice1_without_persisting_audio():
    movie = {
        "id": "123",
        "title": "archive",
        "link": "https://twitcasting.tv/example/movie/123",
        "created": 1234567890,
        "duration": 300,
    }
    event = build_voice_event(movie=movie, segment_index=2, segment_seconds=60, wav_bytes=make_wav())
    assert event["type"] == "voice_event"
    assert event["movie"]["id"] == "123"
    assert event["segment"]["offset_seconds"] == 120
    assert 0 <= event["emotion_midi"]["arousal"] <= 127
    assert 0 <= event["emotion_midi"]["tension"] <= 127
    assert event["truth_boundary"]["raw_audio_persisted"] is False
    assert event["truth_boundary"]["transcript_present"] is False
    assert event["emotion_midi"]["valence_source"] == "neutral_without_semantics"
