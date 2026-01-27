from fastapi import APIRouter, WebSocket
from services.pty_service import pty_service
import logging

logger = logging.getLogger(__name__)

pty_router = APIRouter(tags=["PTY"])

@pty_router.websocket("/pty/{pty_id}/connect")
async def pty_connect(websocket: WebSocket, pty_id: str, directory: str = None):
    logger.info(f"PTY WebSocket connection: {pty_id}")
    await pty_service.handle_pty_websocket(websocket, pty_id, directory)
