import json

from typing import Annotated

from fastapi import APIRouter, Depends
from starlette.websockets import WebSocket, WebSocketDisconnect

from app.db.models.users import User
from app.services.auth.core import get_current_user
from app.services.utils.websocket_manager import WebSocketManager


notification_router = APIRouter(prefix="/notifications", tags=["notifications"])
socket_manager = WebSocketManager()


@notification_router.websocket("/ws/{room_id}/")
async def notification_websocket(
    websocket: WebSocket, room_id: str, user: Annotated[User, Depends(get_current_user)]
):
    message = {
        "user_id": user.id,
        "room_id": room_id,
        "message": f"User {user.id} connected to room {room_id}",
    }

    await socket_manager.broadcast_to_room(room_id, json.dumps(message))
    try:
        while True:
            data = await websocket.receive_text()
            message = {"user_id": user.id, "room_id": room_id, "message": data}
            await socket_manager.broadcast_to_room(room_id, json.dumps(message))
    except WebSocketDisconnect:
        await socket_manager.remove_user_from_room(room_id, websocket)

        message = {
            "user_id": user.id,
            "room_id": room_id,
            "message": f"User {user.id} disconnected from room {room_id}",
        }
        await socket_manager.broadcast_to_room(room_id, json.dumps(message))
