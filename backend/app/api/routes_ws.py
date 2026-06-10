"""WebSocket route for real-time audio chunk streaming from the browser."""

import os
import uuid
import logging
from pathlib import Path

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.utils.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

_DATA_DIR = Path(settings.data_dir) if settings.data_dir else Path(".")
AUDIO_DIR = _DATA_DIR / "audio_uploads"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)


@router.websocket("/ws/audio/{session_id}")
async def stream_audio_ws(websocket: WebSocket, session_id: str):
    """
    Accepts raw audio chunks from the browser's MediaRecorder via WebSocket.
    Chunks are appended to a single .webm file on disk in real-time for research evaluation.
    Research prototype only — output requires physician review.
    """
    await websocket.accept()
    logger.info("WS connected for session: %s", session_id)

    audio_path = AUDIO_DIR / f"{session_id}_live.webm"
    total_bytes = 0

    try:
        with open(audio_path, "wb") as f:
            while True:
                message = await websocket.receive()
                
                if "bytes" in message:
                    chunk = message["bytes"]
                    f.write(chunk)
                    total_bytes += len(chunk)
                    # Acknowledge each chunk so frontend knows it arrived
                    await websocket.send_json({
                        "status": "chunk_received",
                        "bytes_received": total_bytes
                    })
                elif "text" in message and message["text"] == "END":
                    logger.info("WS stream ended for session %s. Total: %d bytes at %s", session_id, total_bytes, audio_path)
                    await websocket.send_json({
                        "status": "stream_complete",
                        "file_path": str(audio_path),
                        "total_bytes": total_bytes
                    })
                    break

    except WebSocketDisconnect:
        logger.warning("WS disconnected prematurely for session: %s (%d bytes saved)", session_id, total_bytes)
    except Exception as e:
        logger.error("WS error for session %s: %s", session_id, e)
        try:
            await websocket.send_json({"status": "error", "detail": str(e)})
        except Exception:
            pass
    finally:
        await websocket.close()
