from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import time

import websockets

try:
    import rtmidi
except ImportError:  # pragma: no cover
    rtmidi = None


def source_channel(source_id: str) -> int:
    digest = hashlib.sha256(source_id.encode("utf-8")).digest()
    return digest[0] % 16


def cc_message(channel: int, control: int, value: int) -> list[int]:
    return [0xB0 | channel, control, max(0, min(127, int(value)))]


def note_on(channel: int, note: int, velocity: int) -> list[int]:
    return [0x90 | channel, note, velocity]


def note_off(channel: int, note: int, velocity: int = 0) -> list[int]:
    return [0x80 | channel, note, velocity]


async def bridge_loop(port_name: str, ws_url: str) -> None:
    midi = rtmidi.MidiOut()
    ports = midi.get_ports()
    if port_name not in ports:
        raise RuntimeError(f"MIDI port not found: {port_name}")
    midi.open_port(ports.index(port_name))

    async with websockets.connect(ws_url) as websocket:
        while True:
            raw = await websocket.recv()
            payload = json.loads(raw)
            if payload.get("type") != "emotion":
                continue

            channel = source_channel(payload["source_id"])
            midi.send_message(cc_message(channel, 11, payload["valence"]))
            midi.send_message(cc_message(channel, 7, payload["arousal"]))
            midi.send_message(cc_message(channel, 1, payload["tension"]))

            if payload.get("bounce"):
                midi.send_message(note_on(channel, 48, 127))
                await asyncio.sleep(0.2)
                midi.send_message(note_off(channel, 48, 0))


def main() -> int:
    parser = argparse.ArgumentParser(description="Bridge E-MIDI emotions to a real MIDI device")
    parser.add_argument("--port", help="MIDI output port name")
    parser.add_argument("--ws-url", default="ws://localhost:8765/ws/receive")
    parser.add_argument("--list-ports", action="store_true")
    args = parser.parse_args()

    if rtmidi is None:
        print(json.dumps({"status": "skipped", "reason": "python-rtmidi not available"}))
        return 0

    try:
        ports = rtmidi.MidiOut().get_ports()
    except Exception as exc:  # pragma: no cover
        print(json.dumps({"status": "skipped", "reason": str(exc)}, ensure_ascii=False))
        return 0

    if args.list_ports:
        print(json.dumps({"status": "ok", "ports": ports}, ensure_ascii=False))
        return 0

    if not args.port:
        print(json.dumps({"status": "skipped", "reason": "no --port specified", "ports": ports}, ensure_ascii=False))
        return 0

    asyncio.run(bridge_loop(args.port, args.ws_url))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
