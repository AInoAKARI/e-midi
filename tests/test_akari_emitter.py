from agents.akari_emitter import AkariEmitter


def test_analyze_positive_bounce_text():
    emitter = AkariEmitter()

    state = emitter.analyze("やった！完成したー！！最高")

    assert state.valence == 84
    assert state.arousal == 79
    assert state.tension == 64
    assert state.bounce is True


def test_analyze_low_energy_confused_text():
    emitter = AkariEmitter()

    state = emitter.analyze("ちょっと疲れた...わからない？")

    assert state.valence == 44
    assert state.arousal == 44
    assert state.tension == 74
    assert state.bounce is False
