
"""
Speckit (GitHub Spec Kit) Dashboard Routes
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import PlainTextResponse
from core.security import get_session_user, verify_token
from core.config import settings
import asyncio
import os
import logging
import json
import httpx
import websockets

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/speckit", tags=["Speckit"])

# Global state to track active process and websockets (Local Only)
ACTIVE_PROCESS = None
ACTIVE_WEBSOCKETS = set()

@router.post("/run")
async def run_speckit_command(
    command: dict,
    request: Request,
    user: dict = Depends(get_session_user)
):
    """
    Run a specific Speckit command.
    Cloud Run: Proxies to Mac.
    Mac: Executes locally using Claude CLI.
    """
    # CLOUD RUN: PROXY
    if settings.K_SERVICE is not None:
        try:
            target_url = f"http://{settings.MAC_SERVER_IP}:{settings.MAC_SERVER_PORT}/api/speckit/run"
            
            # Extract headers (Auth)
            headers = dict(request.headers)
            headers.pop("host", None) # Let httpx set host
            headers.pop("content-length", None) # Let httpx calculate length
            
            async with httpx.AsyncClient(proxy=settings.SOCKS5_PROXY, timeout=60.0) as client:
                resp = await client.post(target_url, json=command, headers=headers)
                
            if resp.status_code != 200:
                 # Log the details from the upstream error
                 error_detail = resp.text
                 logger.error(f"Upstream Proxy Error ({resp.status_code}): {error_detail}")
                 raise HTTPException(status_code=resp.status_code, detail=f"Upstream error: {error_detail}")
                 
            return resp.json()
            
        except HTTPException as he:
            raise he
        except Exception as e:
            logger.error(f"Speckit Proxy Connection Error: {e}")
            raise HTTPException(status_code=500, detail=f"Proxy connection failed: {str(e)}")

    # MAC: LOCAL EXECUTION
    global ACTIVE_PROCESS
    
    action = command.get("action")
    args = command.get("args", "")
    ai_model = command.get("ai_model", "claude")
    
    # Determine Working Directory
    cwd = command.get("cwd")
    if not cwd:
        # Default to project root
        cwd = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    # Map actions to Prompt Templates
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
    try:
        prompt_path = os.path.join(cwd, prompt_file)
        if not os.path.exists(prompt_path):
             raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
             
        with open(prompt_path, "r") as f:
            template = f.read()
            full_prompt = template.replace("$ARGUMENTS", args if args else "")
    except Exception as e:
        logger.error(f"Error reading prompt: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load prompt: {e}")

    # Construct Claude Command
    # Use full path to ensure it is found (especially if run via service/cron)
    claude_bin = "/Users/dlybeck/.local/bin/claude"
    if not os.path.exists(claude_bin):
        # Fallback to "claude" if specific path doesn't exist (e.g. different environment)
        claude_bin = "claude"

    cmd_list = [
        claude_bin,
        "-p", 
        full_prompt,
        "--dangerously-skip-permissions"
    ]

    logger.info(f"Starting Speckit Agent ({action}) in {cwd}")

    try:
        env = os.environ.copy()
        env["CI"] = "true" 
        
        process = await asyncio.create_subprocess_exec(
            *cmd_list,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=env
        )
        
        ACTIVE_PROCESS = process
        asyncio.create_task(broadcast_output(process))
        
        return {"status": "started", "cwd": cwd, "agent": "claude"}
        
    except Exception as e:
        logger.error(f"Failed to start agent: {e}")
        raise HTTPException(status_code=500, detail=f"Agent start failed: {str(e)}")

