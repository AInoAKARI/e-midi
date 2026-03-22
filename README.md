# E-MIDI

E-MIDI is an Emotional MIDI protocol: a small system that encodes valence, arousal, tension, and bounce as a fixed binary frame, streams it over WebSocket, and visualizes live emotional coordinates on a 50x50 grid.

E-MIDI（感情MIDI）は、感情状態を固定長バイナリとWebSocketで扱い、50x50グリッド上にリアルタイム可視化するための小さなプロトコル兼ツール群です。

![E-MIDI Screenshot Placeholder](./docs/screenshot.png)

## Quick Start

```bash
cd ~/e-midi
./setup.sh
PYTHONPATH=/home/kawaii_ai_office/e-midi ./.venv/bin/python agents/akari_emitter.py --text "子供と遊んでた！最高な日だった！！"
```

Open `http://localhost:8765/` in your browser.

ブラウザで `http://localhost:8765/` を開いてください。

## Repository Layout

- `protocol/spec.md`: protocol specification
- `protocol/schema.json`: JSON schema for REST payloads
- `core/`: encoder, decoder, bounce detection
- `server/`: FastAPI + WebSocket server
- `visualizer/`: browser-based emotional grid
- `agents/`: sample emitters
- `bridge/`: MIDI bridge

## Protocol

See [protocol/spec.md](./protocol/spec.md) for the fixed 23-byte E-MIDI frame layout.

23バイト固定長のE-MIDIフレーム仕様は [protocol/spec.md](./protocol/spec.md) を参照してください。

## License

MIT
