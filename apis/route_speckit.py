"""
Speckit (GitHub Spec Kit) Dashboard Routes
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import PlainTextResponse
from core.security import get_session_user, verify_token
from core.config import settings
import asyncio
import os
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/speckit", tags=["Speckit"])

# Global state to track active process and websockets
ACTIVE_PROCESS = None
ACTIVE_WEBSOCKETS = set()

@router.post("/run")
async def run_speckit_command(
    command: dict,
    user: dict = Depends(get_session_user)
):
    """
    Run a specific Speckit command (specify, plan, tasks, implement).
    Payload: {"action": "specify", "args": "Create a login page", "ai_model": "claude"}
    """
    global ACTIVE_PROCESS
    
    if ACTIVE_PROCESS and ACTIVE_PROCESS.returncode is None:
        raise HTTPException(status_code=409, detail="A Speckit process is already running.")

    action = command.get("action")
    args = command.get("args", "")
    ai_model = command.get("ai_model", "claude") 
    
    # Construct the CLI command
    # 'specify' must be in the PATH. 
    # If running inside a venv or specific location, might need adjustment.
    # The previous 'command -v specify' showed it at /Users/dlybeck/.local/bin/specify
    specify_bin = "specify" 
    
    # Map actions to CLI commands
    # Note: The CLI might use different flags or subcommands. 
    # Assuming standard usage: specify [subcommand] [args]
    if action == "specify":
        # 'specify' can take a prompt directly for the 'init' or 'spec' phase?
        # Looking at docs/GEMINI.md context, commands are 'specify', 'plan', 'tasks'.
        # 'specify' might be the root command. 
        # If action is 'specify', maybe it means creating the spec?
        # Let's assume: `specify "prompt"` creates the spec.
        cmd = f'{specify_bin} "{args}" --ai {ai_model}'
    elif action in ["plan", "tasks", "implement"]:
        cmd = f'{specify_bin} {action} --ai {ai_model}'
    elif action == "check":
        # Just a status check, effectively a no-op for the runner
        return {"status": "ready"}
    else:
        raise HTTPException(status_code=400, detail="Invalid action")

    logger.info(f"Starting Speckit command: {cmd}")

    try:
        # Inherit environment and ensure essential vars are present
        env = os.environ.copy()
        
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env
        )
        
        ACTIVE_PROCESS = process
        
        # Start background streaming
        asyncio.create_task(broadcast_output(process))
        
        return {"status": "started", "command": cmd}
        
    except Exception as e:
        logger.error(f"Failed to start Speckit: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def broadcast_output(process):
    """Reads process output and broadcasts to all active WebSockets."""
    try:
        async def read_stream(stream, stream_type):
            while True:
                line = await stream.readline()
                if not line:
                    break
                text = line.decode('utf-8', errors='replace')
                message = json.dumps({"type": stream_type, "data": text})
                
                disconnected = set()
                for ws in ACTIVE_WEBSOCKETS:
                    try:
                        await ws.send_text(message)
                    except:
                        disconnected.add(ws)
                
                for ws in disconnected:
                    ACTIVE_WEBSOCKETS.remove(ws)

        await asyncio.gather(
            read_stream(process.stdout, "stdout"),
            read_stream(process.stderr, "stderr")
        )
        
        await process.wait()
        
        # Broadcast completion
        message = json.dumps({"type": "status", "data": "completed", "exit_code": process.returncode})
        for ws in list(ACTIVE_WEBSOCKETS):
            try:
                await ws.send_text(message)
            except:
                pass
                
    except Exception as e:
        logger.error(f"Error in broadcast loop: {e}")

@router.websocket("/ws")
async def speckit_websocket(websocket: WebSocket, token: str = None):
    """
    WebSocket for real-time logs from Speckit.
    """
    if not token:
        await websocket.close(code=1008, reason="Missing token")
        return
    try:
        # Verify token logic (simplified import if needed)
        verify_token(token)
    except Exception as e:
        logger.warning(f"WS Auth failed: {e}")
        await websocket.close(code=1008, reason="Invalid token")
        return

    await websocket.accept()
    ACTIVE_WEBSOCKETS.add(websocket)
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        ACTIVE_WEBSOCKETS.remove(websocket)
    except Exception:
        if websocket in ACTIVE_WEBSOCKETS:
            ACTIVE_WEBSOCKETS.remove(websocket)

@router.get("/artifacts/{file_type}")
async def get_speckit_file(file_type: str, user: dict = Depends(get_session_user)):
    """
    Read the content of Speckit markdown files (Single Source of Truth).
    """
    # Map file_type to actual paths
    # Based on observation of standard Specify/Spec-kit behavior + existing files
    
    file_map = {
        "constitution": ".specify/memory/constitution.md",
        "spec": "spec.md", # Default spec file name?
        "plan": "PLAN.md",
        "tasks": "tasks.md" # Or .specify/tasks.json?
    }
    
    # Allow direct checking of existence for common variations if 'spec' is requested
    if file_type == "spec":
        # Try common spec names
        candidates = ["spec.md", "SPEC.md", "specification.md"]
        target_path = None
        for c in candidates:
            if os.path.exists(c):
                target_path = c
                break
    else:
        target_path = file_map.get(file_type)

    if not target_path:
         # Fallback or specific known paths from context
         if file_type == "checklist":
             target_path = "checklist.md"
    
    if target_path and os.path.exists(target_path):
        try:
            with open(target_path, "r") as f:
                return PlainTextResponse(f.read())
        except Exception as e:
             raise HTTPException(status_code=500, detail=f"Error reading file: {e}")

    # If file doesn't exist, return empty or specific status
    # Returning 404 might be noisy if we just want to know it's empty
    # But 404 is semantically correct.
    raise HTTPException(status_code=404, detail=f"Artifact '{file_type}' not found at expected path.")
