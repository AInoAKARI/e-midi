from __future__ import annotations

import asyncio
import json
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from core.bounce import BounceDetector
from core.decoder import from_bytes
from core.encoder import EmotionState

app = FastAPI(title="E-MIDI Server")
VISUALIZER_DIR = Path(__file__).resolve().parent.parent / "visualizer"


class EmotionPayload(BaseModel):
    valence: int = Field(ge=0, le=127)
    arousal: int = Field(ge=0, le=127)
    tension: int = Field(ge=0, le=127)
    source_id: str
    timestamp: int | None = None


class BroadcastHub:
    def __init__(self) -> None:
        self.receivers: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self.receivers.add(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self.receivers.discard(websocket)

    async def broadcast_json(self, message: dict[str, Any]) -> None:
        dead: list[WebSocket] = []
        for websocket in list(self.receivers):
            try:
                await websocket.send_json(message)
            except Exception:
                dead.append(websocket)
        for websocket in dead:
            await self.disconnect(websocket)


hub = BroadcastHub()
detectors: dict[str, BounceDetector] = defaultdict(BounceDetector)


def _emotion_message(state: EmotionState) -> dict[str, Any]:
    return {
        "type": "emotion",
        "valence": state.valence,
        "arousal": state.arousal,
        "tension": state.tension,
        "bounce": state.bounce,
        "source_id": state.source_id,
        "timestamp": state.timestamp,
    }


async def process_state(state: EmotionState) -> dict[str, Any]:
    detector = detectors[state.source_id]
    state.bounce = state.bounce or detector.update(state.valence, state.arousal)
    payload = _emotion_message(state)
    await hub.broadcast_json(payload)
    if state.bounce:
        await hub.broadcast_json(
            {
                "type": "bounce",
                "source_id": state.source_id,
                "timestamp": state.timestamp,
            }
        )
    return payload


@app.get("/health")
async def health() -> dict[str, Any]:
    return {"status": "ok", "connections": len(hub.receivers)}


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(VISUALIZER_DIR / "index.html")


@app.get("/visualizer/{asset_name}")
async def visualizer_asset(asset_name: str) -> FileResponse:
    return FileResponse(VISUALIZER_DIR / asset_name)


@app.post("/api/emotion")
async def api_emotion(payload: EmotionPayload) -> dict[str, Any]:
    state = EmotionState(
        valence=payload.valence,
        arousal=payload.arousal,
        tension=payload.tension,
        source_id=payload.source_id,
        timestamp=payload.timestamp or int(time.time() * 1000),
    )
    return await process_state(state)


@app.websocket("/ws/emit")
async def ws_emit(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            message = await websocket.receive()
            if message.get("bytes") is not None:
                state = from_bytes(message["bytes"])
            elif message.get("text") is not None:
                data = json.loads(message["text"])
                state = EmotionState(**data)
            else:
                continue
            payload = await process_state(state)
            await websocket.send_json({"status": "ok", "accepted": payload})
    except WebSocketDisconnect:
        return


@app.websocket("/ws/receive")
async def ws_receive(websocket: WebSocket) -> None:
    await hub.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await hub.disconnect(websocket)
