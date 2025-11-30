
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
            
            async with httpx.AsyncClient(proxy=settings.SOCKS5_PROXY, timeout=60.0) as client:
                resp = await client.post(target_url, json=command, headers=headers)
                
            if resp.status_code != 200:
                 raise HTTPException(status_code=resp.status_code, detail=resp.text)
                 
            return resp.json()
            
        except Exception as e:
            logger.error(f"Speckit Proxy Error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

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
    cmd_list = [
        "claude",
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
        raise HTTPException(status_code=500, detail=str(e))


async def broadcast_output(process):
    """Reads process output and broadcasts to all active WebSockets (Local Only)."""
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


@router.get("/artifacts/{file_type}")
async def get_speckit_file(
    file_type: str, 
    request: Request,
    user: dict = Depends(get_session_user)
):
    """
    Read artifact files.
    Cloud Run: Proxy to Mac.
    Mac: Read local file.
    """
    # CLOUD RUN: PROXY
    if settings.K_SERVICE is not None:
        try:
            target_url = f"http://{settings.MAC_SERVER_IP}:{settings.MAC_SERVER_PORT}/api/speckit/artifacts/{file_type}"
            headers = dict(request.headers)
            headers.pop("host", None)
            
            async with httpx.AsyncClient(proxy=settings.SOCKS5_PROXY, timeout=10.0) as client:
                resp = await client.get(target_url, headers=headers)
                
            if resp.status_code == 404:
                raise HTTPException(status_code=404, detail="Artifact not found")
            if resp.status_code != 200:
                 raise HTTPException(status_code=resp.status_code, detail=resp.text)
                 
            return PlainTextResponse(resp.text)
            
        except HTTPException as he:
            raise he
        except Exception as e:
            logger.error(f"Artifact Proxy Error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # MAC: LOCAL READ
    file_map = {
        "constitution": ".specify/memory/constitution.md",
        "spec": "spec.md",
        "plan": "PLAN.md",
        "tasks": "tasks.md"
    }
    
    target_path = None
    if file_type == "spec":
        candidates = ["spec.md", "SPEC.md", "specification.md"]
        for c in candidates:
            if os.path.exists(c):
                target_path = c
                break
    else:
        target_path = file_map.get(file_type)

    if not target_path:
         if file_type == "checklist":
             target_path = "checklist.md"
    
    if target_path and os.path.exists(target_path):
        try:
            with open(target_path, "r") as f:
                return PlainTextResponse(f.read())
        except Exception as e:
             raise HTTPException(status_code=500, detail=f"Error reading file: {e}")

    raise HTTPException(status_code=404, detail=f"Artifact '{file_type}' not found.")


@router.websocket("/ws")
async def speckit_websocket(websocket: WebSocket, token: str = None):
    """
    WebSocket for real-time logs.
    Cloud Run: Proxy to Mac via SOCKS5.
    Mac: Stream local process output.
    """
    if not token:
        await websocket.close(code=1008, reason="Missing token")
        return
    try:
        verify_token(token)
    except:
        await websocket.close(code=1008, reason="Invalid token")
        return

    await websocket.accept()
    
    # ---------------------------------------------------------
    # CLOUD RUN MODE: PROXY WEB SOCKET
    # ---------------------------------------------------------
    if settings.K_SERVICE is not None:
        sock = None
        try:
            ws_url = f"ws://{settings.MAC_SERVER_IP}:{settings.MAC_SERVER_PORT}/api/speckit/ws?token={token}"
            
            from python_socks.async_.asyncio import Proxy
            proxy = Proxy.from_url(settings.SOCKS5_PROXY)
            
            # Create SOCKS5 tunnel
            sock = await proxy.connect(
                dest_host=settings.MAC_SERVER_IP, 
                dest_port=settings.MAC_SERVER_PORT
            )
            
            async with websockets.connect(ws_url, sock=sock, open_timeout=10) as upstream_ws:
                # Bidirectional forwarding
                async def forward_to_mac():
                    try:
                        while True:
                            msg = await websocket.receive_text()
                            await upstream_ws.send(msg)
                    except WebSocketDisconnect:
                        pass
                    except Exception:
                        pass

                async def forward_to_client():
                    try:
                        async for msg in upstream_ws:
                            await websocket.send_text(msg)
                    except Exception:
                        pass

                await asyncio.gather(forward_to_mac(), forward_to_client())
        except Exception as e:
            logger.error(f"WS Proxy Error: {e}")
        finally:
            if sock:
                try:
                    sock.close()
                except:
                    pass
        return

    # ---------------------------------------------------------
    # MAC MODE: LOCAL STREAMING
    # ---------------------------------------------------------
    ACTIVE_WEBSOCKETS.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ACTIVE_WEBSOCKETS.remove(websocket)
    except Exception:
        if websocket in ACTIVE_WEBSOCKETS:
            ACTIVE_WEBSOCKETS.remove(websocket)

