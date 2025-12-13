"""
AgentBridge V2 - AI-Agnostic Coding Orchestrator Routes

Chat-first interface for spec-driven development with hot-swapping between
AI coding tools (Claude, Gemini).
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
from pathlib import Path
from typing import Optional, List

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agentbridge", tags=["AgentBridge"])

# Global state to track active process and websockets
ACTIVE_PROCESS = None
ACTIVE_WEBSOCKETS = set()

# Current working directory for AgentBridge (can be changed)
CURRENT_CWD = None

# Path to config file (relative to cwd)
CONFIG_PATH = ".agentbridge/config.yaml"

# Recent projects file
RECENT_PROJECTS_FILE = os.path.expanduser("~/.agentbridge_recent.json")

# Code-server workspace file
CODE_SERVER_JSON = os.path.expanduser("~/.local/share/code-server/coder.json")


def get_code_server_workspace() -> Optional[str]:
    """Get the current workspace from code-server if available"""
    try:
        if os.path.exists(CODE_SERVER_JSON):
            with open(CODE_SERVER_JSON, "r") as f:
                data = json.load(f)
                folder = data.get("query", {}).get("folder")
                if folder and os.path.isdir(folder):
                    return folder
    except Exception as e:
        logger.warning(f"Could not read code-server workspace: {e}")
    return None


def get_project_root():
    """Get the current working directory for AgentBridge"""
    global CURRENT_CWD
    if CURRENT_CWD and os.path.isdir(CURRENT_CWD):
        return CURRENT_CWD

    # Try code-server workspace first
    cs_workspace = get_code_server_workspace()
    if cs_workspace:
        return cs_workspace

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


def load_recent_projects() -> List[str]:
    """Load recent projects list"""
    try:
        if os.path.exists(RECENT_PROJECTS_FILE):
            with open(RECENT_PROJECTS_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return []


def save_recent_projects(projects: List[str]):
    """Save recent projects list"""
    try:
        with open(RECENT_PROJECTS_FILE, "w") as f:
            json.dump(projects[:10], f)  # Keep only 10 most recent
    except Exception as e:
        logger.warning(f"Could not save recent projects: {e}")


def add_to_recent_projects(path: str):
    """Add a project to recent projects list"""
    projects = load_recent_projects()
    # Remove if already exists, then add to front
    if path in projects:
        projects.remove(path)
    projects.insert(0, path)
    save_recent_projects(projects[:10])


async def cleanup_prompt_file(file_path, process):
    """Clean up temporary prompt file after process completes"""
    try:
        await process.wait()
        import os
        if os.path.exists(file_path):
            os.unlink(file_path)
            logger.info(f"Cleaned up temp prompt file: {file_path}")
    except Exception as e:
        logger.warning(f"Failed to clean up temp file: {e}")


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

    # Add to recent projects
    add_to_recent_projects(new_cwd)

    return {
        "status": "changed",
        "cwd": new_cwd,
        "has_agentbridge": has_speckit,  # Keeping same key for backwards compat
        "message": f"Working directory set to {new_cwd}" + (" (SpecKit not initialized)" if not has_speckit else "")
    }


@router.get("/browse")
async def browse_directory(
    path: str = None,
    user: dict = Depends(get_session_user)
):
    """Browse filesystem for directory selection (Windows Explorer style)"""
    # Default to home directory if no path specified
    if not path:
        path = os.path.expanduser("~")
    else:
        path = os.path.expanduser(path)

    if not os.path.isdir(path):
        raise HTTPException(status_code=400, detail=f"Not a directory: {path}")

    try:
        entries = []
        for name in sorted(os.listdir(path)):
            full_path = os.path.join(path, name)
            try:
                is_dir = os.path.isdir(full_path)
                # Check if it's a git repo or has .specify (SpecKit project)
                is_git = is_dir and os.path.exists(os.path.join(full_path, ".git"))
                is_speckit = is_dir and os.path.exists(os.path.join(full_path, ".specify"))

                entries.append({
                    "name": name,
                    "path": full_path,
                    "is_dir": is_dir,
                    "is_git": is_git,
                    "is_speckit": is_speckit,
                    "hidden": name.startswith(".")
                })
            except PermissionError:
                continue  # Skip files we can't access

        # Get parent directory
        parent = os.path.dirname(path)
        if parent == path:
            parent = None  # We're at root

        # Build breadcrumbs
        breadcrumbs = []
        current = path
        while current and current != os.path.dirname(current):
            breadcrumbs.insert(0, {"name": os.path.basename(current) or current, "path": current})
            current = os.path.dirname(current)
        if current:
            breadcrumbs.insert(0, {"name": current, "path": current})

        return {
            "path": path,
            "parent": parent,
            "breadcrumbs": breadcrumbs,
            "entries": entries
        }

    except PermissionError:
        raise HTTPException(status_code=403, detail=f"Permission denied: {path}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent-projects")
async def get_recent_projects(user: dict = Depends(get_session_user)):
    """Get list of recent projects"""
    projects = load_recent_projects()

    # Filter out non-existent directories and add metadata
    valid_projects = []
    for path in projects:
        if os.path.isdir(path):
            valid_projects.append({
                "path": path,
                "name": os.path.basename(path),
                "is_git": os.path.exists(os.path.join(path, ".git")),
                "is_speckit": os.path.exists(os.path.join(path, ".specify"))
            })

    # Also include code-server workspace if not in list
    cs_workspace = get_code_server_workspace()
    if cs_workspace and cs_workspace not in projects:
        valid_projects.insert(0, {
            "path": cs_workspace,
            "name": os.path.basename(cs_workspace),
            "is_git": os.path.exists(os.path.join(cs_workspace, ".git")),
            "is_speckit": os.path.exists(os.path.join(cs_workspace, ".specify")),
            "is_current_workspace": True
        })

    return {"projects": valid_projects}


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

        # Copy spec-kit command files from Portfolio to new project
        portfolio_commands = os.path.join(os.path.dirname(__file__), "..", ".claude", "commands")
        target_commands_dir = os.path.join(cwd, ".claude", "commands")

        logger.info(f"Copying command files from {portfolio_commands} to {target_commands_dir}")

        try:
            if not os.path.exists(portfolio_commands):
                logger.error(f"Portfolio commands directory not found: {portfolio_commands}")
                raise Exception(f"Command files source not found: {portfolio_commands}")

            os.makedirs(target_commands_dir, exist_ok=True)
            logger.info(f"Created target directory: {target_commands_dir}")

            # Copy all speckit.*.md files
            import shutil
            copied_count = 0
            for filename in os.listdir(portfolio_commands):
                if filename.startswith("speckit.") and filename.endswith(".md"):
                    src = os.path.join(portfolio_commands, filename)
                    dst = os.path.join(target_commands_dir, filename)
                    shutil.copy2(src, dst)
                    logger.info(f"Copied command file: {filename}")
                    copied_count += 1

            logger.info(f"Successfully copied {copied_count} command files")

            if copied_count == 0:
                logger.warning("No command files were copied!")

        except Exception as e:
            logger.error(f"Failed to copy command files: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"SpecKit initialized but failed to copy command files: {str(e)}"
            )

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
            "env": {}
        }

    if not provider_config:
        raise HTTPException(status_code=400, detail=f"Provider '{provider}' not configured")

    # Map actions to slash commands - all official speckit commands
    command_files = {
        # Core workflow (linear stepper)
        "constitution": ".claude/commands/speckit.constitution.md",
        "specify": ".claude/commands/speckit.specify.md",
        "plan": ".claude/commands/speckit.plan.md",
        "tasks": ".claude/commands/speckit.tasks.md",
        "implement": ".claude/commands/speckit.implement.md",
        # Optional/utility commands (slash commands in chat)
        "clarify": ".claude/commands/speckit.clarify.md",
        "analyze": ".claude/commands/speckit.analyze.md",
        "checklist": ".claude/commands/speckit.checklist.md",
        "taskstoissues": ".claude/commands/speckit.taskstoissues.md",
        # Special actions
        "check": None,  # Just return status
        "chat": None,   # Send user message to ongoing conversation
    }

    if action == "check":
        return {"status": "ready", "provider": provider, "cwd": cwd}

    if action == "chat":
        # Chat action sends user input to the running process stdin
        user_input = args
        if not user_input:
            raise HTTPException(status_code=400, detail="No message provided for chat")
        if ACTIVE_PROCESS is None or ACTIVE_PROCESS.returncode is not None:
            raise HTTPException(status_code=400, detail="No active AI process to chat with")
        # Send to stdin - this enables back-and-forth conversation
        try:
            ACTIVE_PROCESS.stdin.write((user_input + "\n").encode())
            await ACTIVE_PROCESS.stdin.drain()
            return {"status": "sent", "message": user_input}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to send message: {e}")

    if action not in command_files:
        raise HTTPException(status_code=400, detail=f"Invalid action: {action}. Valid: {list(command_files.keys())}")

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

        # Prepend execution directive for Claude CLI
        # This ensures Claude executes the instructions rather than analyzing them
        if provider == "claude":
            execution_directive = """IMPORTANT: You are in execution mode for a spec-kit command. Follow the instructions below EXACTLY as written. Do not analyze, describe, or explain the prompt itself - EXECUTE the instructions it contains.

---

"""
            full_prompt = execution_directive + full_prompt

    except Exception as e:
        logger.error(f"Error loading prompt: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load prompt: {e}")

    # Build command based on provider
    binary = provider_config.get("binary")
    if not os.path.exists(binary):
        # Try PATH fallback
        binary = provider

    #  For large prompts, write to temp file and use -p @file syntax
    import tempfile
    prompt_file = None

    if provider == "gemini":
        cmd_list = [binary, full_prompt]
    else:
        # Claude - use temp file for large prompts to avoid command-line length limits
        prompt_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
        prompt_file.write(full_prompt)
        prompt_file.close()

        cmd_list = [binary, "-p", f"@{prompt_file.name}", "--dangerously-skip-permissions"]

    logger.info(f"Starting AgentBridge ({action}) with {provider} in {cwd}")
    logger.info(f"Command: {' '.join(cmd_list[:3])}...")  # Don't log full prompt path
    logger.info(f"Prompt length: {len(full_prompt)} chars")

    try:
        env = os.environ.copy()
        env.update(provider_config.get("env", {}))

        process = await asyncio.create_subprocess_exec(
            *cmd_list,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=env
        )

        ACTIVE_PROCESS = process

        asyncio.create_task(broadcast_output(process, provider))

        # Clean up temp file after process completes
        if prompt_file:
            asyncio.create_task(cleanup_prompt_file(prompt_file.name, process))

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
