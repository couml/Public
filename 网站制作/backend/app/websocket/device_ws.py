"""WebSocket endpoint for real-time device status updates."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from jose import JWTError
import asyncio
import json

from app.core.config import settings
from app.core.security import decode_token
from app.websocket.manager import manager
from app.utils.redis_client import get_redis

router = APIRouter()


@router.websocket("/ws/devices/{device_id}")
async def device_websocket(
    websocket: WebSocket,
    device_id: str,
    token: str = Query(...),
):
    """WebSocket for real-time device status. Requires JWT token in query param."""
    # Authenticate
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
    except (JWTError, Exception):
        await websocket.close(code=4001, reason="Invalid token")
        return

    # Register connection
    await manager.connect(device_id, websocket)

    # Subscribe to Redis pub/sub for this device
    redis = get_redis()
    pubsub = redis.pubsub()
    await pubsub.subscribe(f"device:{device_id}:status")

    try:
        # Listen for Redis messages and forward to WebSocket
        async def redis_listener():
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        await websocket.send_json(data)
                    except Exception:
                        pass

        # Start Redis listener as a background task
        redis_task = asyncio.create_task(redis_listener())

        # Keep connection alive, handle client messages (ping/pong)
        while True:
            try:
                # Wait for client messages (or timeout to keep checking)
                msg = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                # Client can send "ping" to keep alive
                if msg == "ping":
                    await websocket.send_text("pong")
            except asyncio.TimeoutError:
                # Send keepalive
                try:
                    await websocket.send_text("keepalive")
                except Exception:
                    break

    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        redis_task.cancel()
        try:
            await redis_task
        except asyncio.CancelledError:
            pass
        await pubsub.unsubscribe(f"device:{device_id}:status")
        await pubsub.close()
        manager.disconnect(device_id, websocket)
