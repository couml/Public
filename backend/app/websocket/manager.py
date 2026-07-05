from __future__ import annotations

"""WebSocket Connection Manager for device real-time status."""

from fastapi import WebSocket
from typing import Dict, Set
import json


class ConnectionManager:
    """Manages WebSocket connections per device ID."""

    def __init__(self):
        self._connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, device_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        if device_id not in self._connections:
            self._connections[device_id] = set()
        self._connections[device_id].add(websocket)

    def disconnect(self, device_id: str, websocket: WebSocket) -> None:
        if device_id in self._connections:
            self._connections[device_id].discard(websocket)
            if not self._connections[device_id]:
                del self._connections[device_id]

    async def broadcast_to_device(self, device_id: str, data: dict) -> None:
        if device_id not in self._connections:
            return
        stale = []
        for ws in self._connections[device_id]:
            try:
                await ws.send_json(data)
            except Exception:
                stale.append(ws)
        for ws in stale:
            self.disconnect(device_id, ws)

    async def broadcast_all(self, data: dict) -> None:
        for device_id in list(self._connections.keys()):
            await self.broadcast_to_device(device_id, data)

    @property
    def active_connections(self) -> int:
        return sum(len(conns) for conns in self._connections.values())


manager = ConnectionManager()
