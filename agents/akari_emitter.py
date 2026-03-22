from __future__ import annotations

import argparse
import json
from typing import Iterable

import requests

from core.encoder import EmotionState


def _clip(value: int) -> int:
    return max(0, min(127, value))


class AkariEmitter:
    """
    Estimate emotion parameters from text and send them to the E-MIDI server.
    """

    def __init__(self, endpoint: str = "http://localhost:8765/api/emotion", source_id: str = "akari") -> None:
        self.endpoint = endpoint
        self.source_id = source_id

    def analyze(self, text: str) -> EmotionState:
        valence = 64
        arousal = 64
        tension = 64
        bounce = False

        positive_tokens = ("！", "嬉しい", "やった", "ありがとう")
        low_tokens = ("...", "疲れ", "しんどい")
        bounce_tokens = ("！！", "最高", "天才")
        tense_tokens = ("？", "わからない")

        if any(token in text for token in positive_tokens):
            valence += 20
            arousal += 15
        if any(token in text for token in low_tokens):
            valence -= 20
            arousal -= 20
        if any(token in text for token in tense_tokens):
            tension += 10
        if any(token in text for token in bounce_tokens):
            bounce = True

        return EmotionState(
            valence=_clip(valence),
            arousal=_clip(arousal),
            tension=_clip(tension),
            bounce=bounce,
            source_id=self.source_id,
        )

    def emit(self, text: str) -> dict:
        state = self.analyze(text)
        response = requests.post(
            self.endpoint,
            json={
                "valence": state.valence,
                "arousal": state.arousal,
                "tension": state.tension,
                "bounce": state.bounce,
                "source_id": state.source_id,
                "timestamp": state.timestamp,
            },
            timeout=5,
        )
        response.raise_for_status()
        return response.json()

    def stream_emit(self, text_generator: Iterable[str]) -> list[dict]:
        results = []
        for text in text_generator:
            results.append(self.emit(text))
        return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Send Akari emotion as E-MIDI JSON")
    parser.add_argument("--text", required=True, help="Input text to analyze and emit")
    parser.add_argument("--url", default="http://localhost:8765/api/emotion", help="E-MIDI API endpoint")
    parser.add_argument("--source-id", default="akari", help="Source ID")
    args = parser.parse_args()

    emitter = AkariEmitter(endpoint=args.url, source_id=args.source_id)
    result = emitter.emit(args.text)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
