from __future__ import annotations

from collections import deque
from statistics import pstdev


class BounceDetector:
    def __init__(self, window_size: int = 5, threshold: float = 30.0) -> None:
        self.window_size = window_size
        self.threshold = threshold
        self._valence = deque(maxlen=window_size)
        self._arousal = deque(maxlen=window_size)

    def update(self, valence: int, arousal: int) -> bool:
        self._valence.append(int(valence))
        self._arousal.append(int(arousal))

        if len(self._valence) < self.window_size:
            return False

        valence_dev = pstdev(self._valence)
        arousal_dev = pstdev(self._arousal)
        return max(valence_dev, arousal_dev) > self.threshold
