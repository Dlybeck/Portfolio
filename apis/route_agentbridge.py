"""
AgentBridge - AI-Agnostic Coding Orchestrator Routes

Enables hot-swapping between AI coding tools (Claude, Gemini) while maintaining
project context in external files.
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
import yaml
import httpx

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agentbridge", tags=["AgentBridge"])

# Global state to track active process and websockets
ACTIVE_PROCESS = None
ACTIVE_WEBSOCKETS = set()

# Current working directory for AgentBridge (can be changed)
CURRENT_CWD = None

# Path to config file (relative to cwd)
CONFIG_PATH = ".agentbridge/config.yaml"


def get_project_root():
    """Get the current working directory for AgentBridge"""
    global CURRENT_CWD
    if CURRENT_CWD and os.path.isdir(CURRENT_CWD):
        return CURRENT_CWD
    # Default to Portfolio project
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def set_project_root(path):
    """Set the working directory for AgentBridge"""
    global CURRENT_CWD
    if os.path.isdir(path):
        CURRENT_CWD = os.path.abspath(path)
        return True
    return False


def load_config():
    """Load AgentBridge configuration from YAML"""
    config_path = os.path.join(get_project_root(), CONFIG_PATH)
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"AgentBridge config not found at {config_path}")

    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def save_config(config):
    """Save AgentBridge configuration to YAML"""
    config_path = os.path.join(get_project_root(), CONFIG_PATH)
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False)


async def broadcast_output(process, provider="claude"):
    """Broadcast process output to WebSocket clients"""
    try:
        async def read_stream(stream, stream_name):
            while True:
                line = await stream.readline()
                if not line:
                    break
                decoded = line.decode('utf-8', errors='replace').rstrip()
                logger.info(f"[{stream_name}] {decoded}")

                message = json.dumps({
                    "type": stream_name,
                    "data": decoded,
                    "provider": provider
                })

                disconnected = set()
                for ws in ACTIVE_WEBSOCKETS:
                    try:
                        await ws.send_text(message)
                    except Exception as send_error:
                        logger.warning(f"Failed to send to WebSocket: {send_error}")
                        disconnected.add(ws)

                for ws in disconnected:
                    ACTIVE_WEBSOCKETS.discard(ws)

        await asyncio.gather(
            read_stream(process.stdout, "stdout") if process.stdout else asyncio.sleep(0),
            read_stream(process.stderr, "stderr") if process.stderr else asyncio.sleep(0)
        )

        exit_code = await process.wait()
        logger.info(f"Process completed with exit code: {exit_code}")

        completion_msg = json.dumps({
            "type": "status",
            "data": "completed",
            "exit_code": exit_code
        })

        for ws in ACTIVE_WEBSOCKETS:
            try:
                await ws.send_text(completion_msg)
            except Exception:
                pass

    except Exception as e:
        logger.error(f"Error in broadcast_output: {e}")


@router.get("/health")
async def agentbridge_health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "mode": "proxy" if settings.K_SERVICE else "local",
        "cwd": get_project_root()
    }


@router.get("/cwd")
async def get_cwd(user: dict = Depends(get_session_user)):
    """Get current working directory"""
    cwd = get_project_root()
    # Check for .specify directory (official spec-kit) as initialization indicator
    has_speckit = os.path.exists(os.path.join(cwd, ".specify"))
    return {
        "cwd": cwd,
        "has_agentbridge": has_speckit  # Keeping same key for backwards compat
    }


@router.post("/cwd")
async def set_cwd(
    request_body: dict,
    user: dict = Depends(get_session_user)
):
    """Set working directory for AgentBridge"""
    global ACTIVE_PROCESS

    # Prevent changing during active execution
    if ACTIVE_PROCESS is not None and ACTIVE_PROCESS.returncode is None:
        raise HTTPException(
            status_code=409,
            detail="Cannot change directory during active execution"
        )

    new_cwd = request_body.get("cwd")
    if not new_cwd:
        raise HTTPException(status_code=400, detail="Missing 'cwd' field")

    # Expand ~ to home directory
    new_cwd = os.path.expanduser(new_cwd)

    if not os.path.isdir(new_cwd):
        raise HTTPException(status_code=400, detail=f"Directory not found: {new_cwd}")

    set_project_root(new_cwd)

    # Check if SpecKit is initialized in this directory
    has_speckit = os.path.exists(os.path.join(new_cwd, ".specify"))

    return {
        "status": "changed",
        "cwd": new_cwd,
        "has_agentbridge": has_speckit,  # Keeping same key for backwards compat
        "message": f"Working directory set to {new_cwd}" + (" (SpecKit not initialized)" if not has_speckit else "")
    }


@router.post("/init")
async def init_agentbridge(
    request_body: dict = None,
    user: dict = Depends(get_session_user)
):
    """
    Initialize SpecKit in current working directory using official spec-kit command.

    Uses: uvx --from git+https://github.com/github/spec-kit.git specify init . --ai {provider}

    Accepts optional body: {"provider": "claude" | "gemini"}
    """
    cwd = get_project_root()

    # Get provider from request or default to claude
    provider = "claude"
    if request_body and request_body.get("provider"):
        provider = request_body.get("provider")

    # Validate provider - spec-kit supports claude and gemini
    if provider not in ["claude", "gemini"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid provider '{provider}'. Supported: claude, gemini"
        )

    # Check if already initialized
    specify_dir = os.path.join(cwd, ".specify")
    if os.path.exists(specify_dir):
        return {
            "status": "exists",
            "cwd": cwd,
            "message": "SpecKit already initialized in this directory"
        }

    # Run official spec-kit init command
    # Using uvx to run directly from GitHub repo
    uvx_path = "/Users/dlybeck/.local/bin/uvx"
    cmd = [
        uvx_path,
        "--from", "git+https://github.com/github/spec-kit.git",
        "specify", "init", ".",
        "--ai", provider
    ]

    logger.info(f"Initializing SpecKit in {cwd} with {provider}: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout for git clone + install
        )

        if result.returncode != 0:
            logger.error(f"SpecKit init failed: {result.stderr}")
            raise HTTPException(
                status_code=500,
                detail=f"SpecKit init failed: {result.stderr or result.stdout}"
            )

        logger.info(f"SpecKit initialized successfully: {result.stdout}")

        return {
            "status": "initialized",
            "cwd": cwd,
            "provider": provider,
            "output": result.stdout,
            "message": f"SpecKit initialized successfully with {provider}"
        }

    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=504,
            detail="SpecKit initialization timed out (>2 minutes)"
        )
    except FileNotFoundError:
        # uvx not installed - provide helpful error
        raise HTTPException(
            status_code=500,
            detail="uvx not found. Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
        )


@router.get("/config")
async def get_config(user: dict = Depends(get_session_user)):
    """Get current AgentBridge configuration"""
    cwd = get_project_root()

    # Check if spec-kit is initialized
    specify_dir = os.path.join(cwd, ".specify")
    if not os.path.exists(specify_dir):
        # Not initialized - return minimal defaults
        return {
            "provider": "claude",
            "providers": ["claude", "gemini"],
            "features_dir": "specs",
            "initialized": False
        }

    # Try to load .agentbridge config if it exists, otherwise use defaults
    try:
        config = load_config()
        return {
            "provider": config.get("provider", "claude"),
            "providers": list(config.get("providers", {}).keys()) or ["claude", "gemini"],
            "features_dir": config.get("features_dir", "specs"),
            "initialized": True
        }
    except FileNotFoundError:
        # Spec-kit initialized but no .agentbridge config - use defaults
        return {
            "provider": "claude",
            "providers": ["claude", "gemini"],
            "features_dir": "specs",
            "initialized": True
        }


# In-memory provider state (when no config file exists)
CURRENT_PROVIDER = "claude"


@router.post("/switch")
async def switch_provider(
    request_body: dict,
    user: dict = Depends(get_session_user)
):
    """Switch the active AI provider"""
    global ACTIVE_PROCESS, CURRENT_PROVIDER

    # Prevent switching during active execution
    if ACTIVE_PROCESS is not None and ACTIVE_PROCESS.returncode is None:
        raise HTTPException(
            status_code=409,
            detail="Cannot switch providers during active execution"
        )

    new_provider = request_body.get("provider")
    if not new_provider:
        raise HTTPException(status_code=400, detail="Missing 'provider' field")

    # Validate provider
    available_providers = ["claude", "gemini"]
    if new_provider not in available_providers:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown provider '{new_provider}'. Available: {available_providers}"
        )

    # Try to save to config file if it exists
    try:
        config = load_config()
        config["provider"] = new_provider
        save_config(config)
    except FileNotFoundError:
        # No config file - just store in memory
        pass

    # Always update in-memory state
    CURRENT_PROVIDER = new_provider

    return {
        "status": "switched",
        "provider": new_provider,
        "message": f"Switched to {new_provider}"
    }


@router.post("/run")
async def run_agentbridge_command(
    command: dict,
    request: Request,
    user: dict = Depends(get_session_user)
):
    """
    Run an AgentBridge command (specify, plan, tasks, implement, status).
    Cloud Run: Proxies to Mac.
    Mac: Executes locally using configured AI provider.
    """
    # CLOUD RUN: PROXY
    if settings.K_SERVICE is not None:
        try:
            target_url = f"http://{settings.MAC_SERVER_IP}:{settings.MAC_SERVER_PORT}/api/agentbridge/run"
            headers = dict(request.headers)
            headers.pop("host", None)
            headers.pop("content-length", None)

            async with httpx.AsyncClient(proxy=settings.SOCKS5_PROXY, timeout=60.0) as client:
                resp = await client.post(target_url, json=command, headers=headers)

            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail=resp.text)
            return resp.json()

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"AgentBridge Proxy Error: {e}")
            raise HTTPException(status_code=500, detail=f"Proxy failed: {str(e)}")

    # MAC: LOCAL EXECUTION
    global ACTIVE_PROCESS

    action = command.get("action")
    feature = command.get("feature", "")
    args = command.get("args", "")
    provider_override = command.get("provider")

    cwd = get_project_root()

    # Determine provider - use override or default to claude
    provider = provider_override or "claude"

    # Check if SpecKit is initialized
    specify_dir = os.path.join(cwd, ".specify")
    if not os.path.exists(specify_dir):
        raise HTTPException(
            status_code=400,
            detail="SpecKit not initialized. Click 'Init SpecKit' first."
        )

    # Get provider config - use defaults if no .agentbridge config
    try:
        config = load_config()
        provider_config = config.get("providers", {}).get(provider)
    except FileNotFoundError:
        # No .agentbridge config - use defaults
        provider_config = {
            "binary": "/Users/dlybeck/.local/bin/claude" if provider == "claude" else "/opt/homebrew/bin/gemini",
            "args": ["-p", "{prompt}", "--dangerously-skip-permissions"] if provider == "claude" else ["{prompt}"],
            "env": {"CI": "true"}
        }

    if not provider_config:
        raise HTTPException(status_code=400, detail=f"Provider '{provider}' not configured")

    # Map actions to slash commands - use official speckit commands
    command_files = {
        "specify": ".claude/commands/speckit.specify.md",
        "plan": ".claude/commands/speckit.plan.md",
        "tasks": ".claude/commands/speckit.tasks.md",
        "implement": ".claude/commands/speckit.implement.md",
        "status": ".claude/commands/speckit.status.md" if os.path.exists(os.path.join(cwd, ".claude/commands/speckit.status.md")) else None,
        "check": None  # Special action - just return status
    }

    if action == "check":
        return {"status": "ready", "provider": provider, "cwd": cwd}

    if action not in command_files:
        raise HTTPException(status_code=400, detail=f"Invalid action: {action}")

    prompt_file = command_files[action]
    prompt_path = os.path.join(cwd, prompt_file)

    if not os.path.exists(prompt_path):
        raise HTTPException(status_code=404, detail=f"Command file not found: {prompt_file}")

    # Load prompt template
    try:
        with open(prompt_path, "r") as f:
            template = f.read()

        # Strip frontmatter if present
        if template.startswith("---"):
            parts = template.split("---", 2)
            if len(parts) >= 3:
                template = parts[2].strip()

        # Substitute variables
        full_prompt = template.replace("$ARGUMENTS", args if args else "")
        full_prompt = full_prompt.replace("$FEATURE", feature if feature else "")

    except Exception as e:
        logger.error(f"Error loading prompt: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load prompt: {e}")

    # Build command based on provider
    binary = provider_config.get("binary")
    if not os.path.exists(binary):
        # Try PATH fallback
        binary = provider

    if provider == "gemini":
        cmd_list = [binary, full_prompt]
    else:
        # Claude (default)
        cmd_list = [binary, "-p", full_prompt, "--dangerously-skip-permissions"]

    logger.info(f"Starting AgentBridge ({action}) with {provider} in {cwd}")

    try:
        env = os.environ.copy()
        env.update(provider_config.get("env", {}))

        process = await asyncio.create_subprocess_exec(
            *cmd_list,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=env
        )

        ACTIVE_PROCESS = process
        asyncio.create_task(broadcast_output(process, provider))

        return {
            "status": "started",
            "action": action,
            "feature": feature,
            "provider": provider,
            "cwd": cwd
        }

    except Exception as e:
        logger.error(f"Failed to start agent: {e}")
        raise HTTPException(status_code=500, detail=f"Agent start failed: {str(e)}")


@router.websocket("/ws")
async def agentbridge_websocket(websocket: WebSocket, token: str = None):
    """WebSocket endpoint for real-time output streaming"""
    if not token:
        await websocket.close(code=1008, reason="Missing authentication token")
        return

    try:
        payload = verify_token(token)
        if payload.get("type") != "access":
            await websocket.close(code=1008, reason="Invalid token type")
            return
    except Exception as e:
        logger.warning(f"WebSocket auth failed: {e}")
        await websocket.close(code=1008, reason="Invalid token")
        return

    await websocket.accept()
    logger.info(f"AgentBridge WebSocket connected (total: {len(ACTIVE_WEBSOCKETS) + 1})")

    # Cloud Run: Proxy to Mac
    if settings.K_SERVICE is not None:
        await websocket.close(code=1011, reason="Cloud Run proxy not yet implemented")
        return

    ACTIVE_WEBSOCKETS.add(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)

            if msg.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))

    except WebSocketDisconnect:
        logger.info("AgentBridge WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        ACTIVE_WEBSOCKETS.discard(websocket)
        try:
            await websocket.close()
        except:
            pass


@router.get("/features")
async def list_features(user: dict = Depends(get_session_user)):
    """List all features in AgentBridge (reads from specs/ directory for official spec-kit)"""
    cwd = get_project_root()

    # Official spec-kit uses 'specs/' directory for features
    features_dir = os.path.join(cwd, "specs")

    # Also check for legacy .agentbridge/features path
    if not os.path.exists(features_dir):
        try:
            config = load_config()
            features_dir = os.path.join(cwd, config.get("features_dir", "specs"))
        except FileNotFoundError:
            pass

    if not os.path.exists(features_dir):
        return {"features": []}

    features = []
    try:
        for name in os.listdir(features_dir):
            feature_path = os.path.join(features_dir, name)
            if os.path.isdir(feature_path):
                # Check which artifacts exist
                artifacts = {}
                for artifact in ["spec.md", "plan.md", "tasks.md", "context.md"]:
                    artifact_path = os.path.join(feature_path, artifact)
                    artifacts[artifact.replace(".md", "")] = os.path.exists(artifact_path)

                features.append({
                    "name": name,
                    "artifacts": artifacts
                })

        return {"features": features}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/features/{feature}/artifacts/{artifact_type}")
async def get_feature_artifact(
    feature: str,
    artifact_type: str,
    user: dict = Depends(get_session_user)
):
    """Get a specific artifact for a feature"""
    cwd = get_project_root()

    # Try official spec-kit path first (specs/)
    artifact_path = os.path.join(cwd, "specs", feature, f"{artifact_type}.md")

    # Fallback to legacy path if configured
    if not os.path.exists(artifact_path):
        try:
            config = load_config()
            features_dir = config.get("features_dir", "specs")
            artifact_path = os.path.join(cwd, features_dir, feature, f"{artifact_type}.md")
        except FileNotFoundError:
            pass

    if not os.path.exists(artifact_path):
        raise HTTPException(status_code=404, detail=f"{artifact_type}.md not found for {feature}")

    try:
        with open(artifact_path, "r") as f:
            return PlainTextResponse(content=f.read(), media_type="text/markdown")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/debug/test-providers")
async def test_providers():
    """Test which AI providers are available"""
    results = {}

    try:
        config = load_config()
        for name, provider_config in config.get("providers", {}).items():
            binary = provider_config.get("binary", name)
            exists = os.path.exists(binary)
            results[name] = {
                "binary": binary,
                "exists": exists,
                "active": config.get("provider") == name
            }
    except Exception as e:
        results["error"] = str(e)

    return results
