# E-MIDI

![pytest](https://img.shields.io/badge/pytest-passing-brightgreen)
![license](https://img.shields.io/badge/license-MIT-blue)

## E-MIDIとは / What Is E-MIDI

E-MIDI（Emotional MIDI）は、楽器の演奏情報ではなく感情状態を送るための軽量プロトコルです。valence・arousal・tension・bounce を 23 バイト固定長で表現し、WebSocket で配信し、50x50 グリッド上にリアルタイム可視化します。人間やAIエージェントの気分変化を、ソフトウェア間で共有できる感情レイヤーとして扱います。

E-MIDI is a lightweight protocol for transmitting emotional state instead of musical notes. It encodes valence, arousal, tension, bounce, source identity, and timestamp into a fixed 23-byte frame, streams the data over WebSocket, and renders it on a live 50x50 visual grid. The goal is to make emotion portable between humans, AI agents, interfaces, and future instruments. Rather than treating feeling as vague metadata, E-MIDI turns it into structured, low-latency state that can be visualized, logged, and bridged into other systems, including MIDI-compatible workflows.

## Quick Start

```bash
cd ~/e-midi
./setup.sh
PYTHONPATH=/home/kawaii_ai_office/e-midi ./.venv/bin/python agents/akari_emitter.py --text "やった！完成したー！！"
```

Open `http://localhost:8765/` in your browser.

## Protocol Spec

E-MIDI is a fixed-length 23-byte frame.

| Offset | Length | Field | Description |
| --- | ---: | --- | --- |
| 0 | 1 | `header_0` | `0xE0` |
| 1 | 1 | `header_1` | `0x4D` |
| 2 | 1 | `valence` | `0-127` |
| 3 | 1 | `arousal` | `0-127` |
| 4 | 1 | `tension` | `0-127` |
| 5 | 1 | `flags` | `bit0=bounce`, others reserved |
| 6 | 8 | `source_id` | ASCII, truncated/padded to 8 bytes |
| 14 | 8 | `timestamp` | little-endian `uint64` Unix ms |
| 22 | 1 | `reserved` | `0x00` |

Detailed spec: [protocol/spec.md](./protocol/spec.md)

## Emotion Parameters

- `valence`: negative to positive emotional tone
- `arousal`: sleepy/calm to activated/excited energy
- `tension`: relaxed to tense/anxious pressure
- `bounce`: sudden emotional jump detection flag

## Visualizer

![E-MIDI Screenshot Placeholder](./docs/screenshot.png)

The browser visualizer maps `valence` to X, `arousal` to Y, and `tension` to color, with trail decay and bounce flash.

## Akari Emitter Example

Rule-based emission from text:

```bash
PYTHONPATH=/home/kawaii_ai_office/e-midi ./.venv/bin/python agents/akari_emitter.py --text "ありがとう！最高！！"
```

Example response:

```json
{"type":"emotion","valence":84,"arousal":79,"tension":64,"bounce":true,"source_id":"akari","timestamp":1774166645597}
```

## License / Author

- License: MIT
- Author: kawaii-ai-office
