import json
from collections import defaultdict
from fastapi import WebSocket
from typing import Any


class WebSocketManager:
    """Gère les connexions WebSocket pour les analyses live."""

    def __init__(self):
        # match_id → liste de connexions actives
        self._connections: dict[str, list[WebSocket]] = defaultdict(list)
        # connexions globales (dashboard principal)
        self._broadcast_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket, match_id: str | None = None):
        await websocket.accept()
        if match_id:
            self._connections[match_id].append(websocket)
        else:
            self._broadcast_connections.append(websocket)

    def disconnect(self, websocket: WebSocket, match_id: str | None = None):
        if match_id:
            self._connections[match_id] = [
                ws for ws in self._connections[match_id] if ws != websocket
            ]
        else:
            self._broadcast_connections = [
                ws for ws in self._broadcast_connections if ws != websocket
            ]

    async def send_to_match(self, match_id: str, data: Any):
        """Envoie une mise à jour à tous les abonnés d'un match."""
        payload = json.dumps(data)
        dead = []
        for ws in self._connections.get(match_id, []):
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws, match_id)

    async def broadcast(self, data: Any):
        """Diffuse une alerte à tous les clients du dashboard."""
        payload = json.dumps(data)
        dead = []
        for ws in self._broadcast_connections:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    def active_connections(self) -> int:
        total = len(self._broadcast_connections)
        for conns in self._connections.values():
            total += len(conns)
        return total


ws_manager = WebSocketManager()
