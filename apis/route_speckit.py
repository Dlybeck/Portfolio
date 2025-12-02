
"""
Speckit (GitHub Spec Kit) Dashboard Routes
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import PlainTextResponse
from core.security import get_session_user, verify_token
from core.config import settings
import asyncio
import os
import subprocess
import logging
import json
import httpx
import websockets

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/speckit", tags=["Speckit"])

# Global state to track active process and websockets (Local Only)
ACTIVE_PROCESS = None
ACTIVE_WEBSOCKETS = set()

async def broadcast_output(process):
    """Simple broadcast function - reads process output and logs it"""
    try:
        # Read both stdout and stderr concurrently
        async def read_stream(stream, stream_name):
            while True:
                line = await stream.readline()
                if not line:
                    break
                decoded = line.decode('utf-8', errors='replace').rstrip()
                logger.info(f"[{stream_name}] {decoded}")

        # Read both streams concurrently
        await asyncio.gather(
            read_stream(process.stdout, "stdout") if process.stdout else asyncio.sleep(0),
            read_stream(process.stderr, "stderr") if process.stderr else asyncio.sleep(0)
        )

        # Wait for process to complete
        exit_code = await process.wait()
        logger.info(f"Process completed with exit code: {exit_code}")

    except Exception as e:
        logger.error(f"Error in broadcast_output: {e}")

@router.get("/health")
async def speckit_health():
    return {
        "status": "ok", 
        "mode": "proxy" if settings.K_SERVICE else "local",
        "cwd": os.getcwd()
    }

@router.get("/run")
async def run_speckit_command_get():
    return {"message": "Use POST to run commands. Speckit router is active."}

@router.get("/debug_proxy")
async def debug_proxy():
    """Test the proxy connection to Mac /run endpoint"""
    if settings.K_SERVICE is None:
        return {"status": "skipped", "reason": "Running locally"}
        
    target_url = f"http://{settings.MAC_SERVER_IP}:{settings.MAC_SERVER_PORT}/api/speckit/run"
    results = {
        "target": target_url,
        "proxy": settings.SOCKS5_PROXY,
        "test_payload": {"action": "check", "cwd": "/tmp"}
    }
    
    try:
        async with httpx.AsyncClient(proxy=settings.SOCKS5_PROXY, timeout=10.0) as client:
            # Try POST
            resp = await client.post(target_url, json=results["test_payload"])
            results["status_code"] = resp.status_code
            results["response_text"] = resp.text
            results["headers"] = dict(resp.headers)
            
    except Exception as e:
        results["error"] = str(e)
        results["error_type"] = type(e).__name__
        
    return results

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

        # Strip frontmatter (YAML between --- delimiters) to avoid CLI parsing issues
        # Frontmatter causes "unknown option '---'" error when passed to claude -p
        if template.startswith("---"):
            parts = template.split("---", 2)
            if len(parts) >= 3:
                # parts[0] = empty, parts[1] = frontmatter, parts[2] = content
                template = parts[2].strip()

        full_prompt = template.replace("$ARGUMENTS", args if args else "")
    except Exception as e:
        logger.error(f"Error reading prompt: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load prompt: {e}")

    # Construct AI Command (supports both Claude and Gemini)
    if ai_model == "gemini":
        # Gemini uses positional argument (no -p flag)
        gemini_bin = "/opt/homebrew/bin/gemini"
        if not os.path.exists(gemini_bin):
            gemini_bin = "gemini"  # Fallback to PATH

        cmd_list = [
            gemini_bin,
            "--yolo",  # Auto-approve actions (like Claude's --dangerously-skip-permissions)
            full_prompt
        ]
    else:
        # Claude (default)
        claude_bin = "/Users/dlybeck/.local/bin/claude"
        if not os.path.exists(claude_bin):
            claude_bin = "claude"  # Fallback to PATH

        cmd_list = [
            claude_bin,
            "-p",
            full_prompt,
            "--dangerously-skip-permissions"
        ]

    logger.info(f"Starting Speckit Agent ({action}) with {ai_model} in {cwd}")

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

        return {"status": "started", "cwd": cwd, "agent": ai_model}
        
    except Exception as e:
        logger.error(f"Failed to start agent: {e}")
        raise HTTPException(status_code=500, detail=f"Agent start failed: {str(e)}")

@router.get("/artifacts/{artifact_type}")
async def get_artifact(
    artifact_type: str,
    user: dict = Depends(get_session_user)
):
    """Get a generated artifact (spec.md, plan.md, tasks.md)"""
    # Simple implementation - look in current directory for specs folder
    cwd = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    # Try to get current git branch to find feature directory
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=5
        )
        branch = result.stdout.strip()

        if branch:
            # Try specs/branch-name/artifact.md
            artifact_path = os.path.join(cwd, "specs", branch, f"{artifact_type}.md")
            if os.path.exists(artifact_path):
                with open(artifact_path, "r") as f:
                    return PlainTextResponse(content=f.read(), media_type="text/markdown")
    except:
        pass

    # Not found
    raise HTTPException(status_code=404, detail=f"{artifact_type} not found")

