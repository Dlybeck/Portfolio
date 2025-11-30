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
    
    # Determine Working Directory first
    # 1. Try explicit 'cwd' from payload
    cwd = command.get("cwd")
    
    # 2. Default to project root (where main.py is)
    if not cwd:
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        cwd = project_root

    # Map actions to Prompt Templates
    # The user uses custom Claude commands defined in .claude/commands/
    prompt_file = None
    
    if action == "specify":
        prompt_file = ".claude/commands/speckit.specify.md"
    elif action == "plan":
        prompt_file = ".claude/commands/speckit.plan.md"
    elif action == "tasks":
        prompt_file = ".claude/commands/speckit.tasks.md"
    elif action == "implement":
        prompt_file = ".claude/commands/speckit.implement.md"
    elif action == "check":
        return {"status": "ready", "cwd": cwd}
    else:
        raise HTTPException(status_code=400, detail="Invalid action")

    # Load and Format Prompt
    full_prompt = ""
    try:
        prompt_path = os.path.join(cwd, prompt_file)
        if not os.path.exists(prompt_path):
             raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
             
        with open(prompt_path, "r") as f:
            template = f.read()
            # Replace $ARGUMENTS with user args (or empty string)
            full_prompt = template.replace("$ARGUMENTS", args if args else "")
            
            # If args is empty, some prompts might need specific handling, 
            # but the template usually says "If empty: ERROR".
            # We rely on the CLI to handle the logic defined in the prompt.
    except Exception as e:
        logger.error(f"Error reading prompt template: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load prompt template: {e}")

    # Construct the Claude CLI command
    # We use -p (print) for non-interactive execution
    # We use --dangerously-skip-permissions because we cannot approve tool use interactively via API
    # We pass the prompt as a positional argument
    # Note: passing a very long prompt as an arg might hit shell limits. 
    # Better to write to a temp file or pass via stdin if supported?
    # 'claude --help' says [prompt] is an argument.
    # Let's try passing it as an argument first. 
    # WARNING: Shell command length limits (ARG_MAX) are usually high (megabytes on Linux/Mac), 
    # but newlines/special chars need careful escaping if passed as string.
    # Safe bet: Write prompt to a temporary file and cat it? 
    # Or just rely on Python's subprocess to handle arg passing safely (it skips shell parsing if list is used).
    
    cmd_list = [
        "claude",
        "-p", 
        full_prompt,
        "--dangerously-skip-permissions"
    ]
    
    if ai_model == "gemini":
         # If the user selected Gemini, does `claude` CLI support switching model backend?
         # `claude --model` supports aliases. 'gemini-pro' might work if configured?
         # If not, we stick to Claude or the user's default. 
         # For now, we just log it.
         pass

    logger.info(f"Starting Speckit Agent ({action}) in {cwd}")

    try:
        # Inherit environment
        env = os.environ.copy()
        # Force non-interactive mode
        env["CI"] = "true" 
        
        # Use list format for subprocess to avoid shell injection/quoting issues
        process = await asyncio.create_subprocess_exec(
            *cmd_list,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=env
        )
        
        ACTIVE_PROCESS = process
        
        # Start background streaming
        asyncio.create_task(broadcast_output(process))
        
        return {"status": "started", "cwd": cwd, "agent": "claude"}

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
