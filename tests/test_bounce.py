from core.bounce import BounceDetector


def test_bounce_requires_full_window():
    detector = BounceDetector(window_size=5, threshold=10)

    for _ in range(4):
        assert detector.update(64, 64) is False


def test_bounce_triggers_when_variance_exceeds_threshold():
    detector = BounceDetector(window_size=5, threshold=20)

    series = [(20, 20), (100, 20), (20, 100), (100, 100), (20, 20)]
    results = [detector.update(v, a) for v, a in series]

    assert results[-1] is True


def test_bounce_stays_false_for_stable_signal():
    detector = BounceDetector(window_size=5, threshold=5)

    series = [(63, 64), (64, 63), (63, 63), (64, 64), (63, 64)]
    results = [detector.update(v, a) for v, a in series]

    assert results[-1] is False
