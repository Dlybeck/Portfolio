# Debugging Journey: Speckit Dashboard Connectivity (405/Connection Refused)

**Status:** Critical Block. Dashboard fails with `405 Method Not Allowed` on POST `/api/speckit/run` and WebSocket connection failures.

## Symptoms
1.  **Frontend:** 
    - `POST /api/speckit/run` returns `405 Method Not Allowed`.
    - `GET /api/speckit/artifacts/*` returns `404 Not Found`.
    - `WS /api/speckit/ws` connection fails immediately.
2.  **Cloud Run:** 
    - `/api/speckit/health` returns `{"status":"ok", "mode":"proxy"}` (Router IS registered).
    - `/debug/tailscale/full-diagnostic` confirms Tailscale is up, but connectivity to Mac is suspect.
3.  **Local Mac Server:**
    - Server is running (`ps aux` confirms PID).
    - Logs (`server.log`) show startup success.
    - **CRITICAL:** Logs show **ZERO** incoming requests from Cloud Run.

## Root Cause Analysis

### 1. The "405 Method Not Allowed" Mystery
- **Fact:** The router is registered (`/health` works).
- **Fact:** The code defines `@router.post("/run")`.
- **Observation:** Hitting it returns 405.
- **Deduction:** The request is NOT reaching the FastAPI route handler for `POST /run`.
- **Hypothesis A (Disproven):** Router missing? No, `health` works.
- **Hypothesis B (Likely):** Something *upstream* of FastAPI (Cloud Run Ingress, Load Balancer, or Middleware) is rewriting the request or rejecting POST.
    - *Check:* Trailing slash? `/run` vs `/run/`. Browser sends `/run`. FastAPI expects `/run`. Match.
    - *Check:* HTTP vs HTTPS? Client uses HTTPS. Cloud Run terminates SSL. App sees HTTP. POST should be preserved.
- **Hypothesis C:** The request is hitting a *different* router that captures `/api/speckit/run` via a wildcard?
    - Checked `dev_proxy_router` (`/dev/vscode/{path:path}`). No overlap.

### 2. The Connection Gap (Cloud Run -> Mac)
- **Observation:** Local logs show no activity.
- **Implication:** The SOCKS5 tunnel from Cloud Run to Mac is not establishing, OR it connects to the wrong target.
- **Diagnostic:** `/api/speckit/debug_proxy` was added to test this. (Pending result).

### 3. The Code mismatch?
- Cloud Run is confirmed updated (`/health` exists).
- Local Mac is confirmed updated and running.

## Actions Taken
1.  **Implemented Proxy Logic:** Rewrote `route_speckit.py` to forward requests from Cloud Run to Mac via SOCKS5.
2.  **Fixed Dependencies:** Updated Dockerfile to remove heavy deps (`claude`, `node`) and keep it lightweight.
3.  **Added Diagnostics:** Created `/debug/tailscale` and `/api/speckit/debug_proxy`.
4.  **Verified Local:** Restarted Mac server multiple times, verified process and logs.
5.  **Verified Route:** Added `GET /run` handler to test path existence.

## Next Steps
1.  **Isolate the 405:** Use `curl` from a local machine against the Cloud Run URL to precisely control headers/path and see raw response.
    - `curl -X POST -v https://davidlybeck.com/api/speckit/run`
2.  **Verify SOCKS Tunnel:** Use the `/debug/tailscale/test-http-socks5` endpoint to confirm Cloud Run can actually "see" the Mac.
3.  **Bypass Domain:** Test against the raw `run.app` URL to rule out domain mapping issues.

**Current Theory:** The `405` is a red herring caused by a failure in the SOCKS proxy handshake that is bubbling up as a generic error, OR a mismatch in how `httpx` forwards headers (Host header?) causing the Mac to reject it. But since logs show *no* request on Mac, the SOCKS failure is most likely.

---

## Session 2: AI Hot-Swapping Implementation (2025-12-01/02)

### Goal
Implement hot-swapping between Claude Code and Gemini CLI for Speckit workflows.

### Implementation Summary

**Changes Made:**
1. **route_speckit.py (lines 143-166):** Added simple if/else for Claude vs Gemini CLI
   - Gemini: `gemini --yolo "prompt"` (positional argument)
   - Claude: `claude -p "prompt" --dangerously-skip-permissions"` (flag-based)
   - Backend now honors `ai_model` parameter from frontend

2. **route_speckit.py (lines 26-49):** Implemented `broadcast_output()` function
   - Initially only captured stdout
   - Updated to capture BOTH stdout and stderr using `asyncio.gather`
   - Logs to server logs (WebSocket streaming not yet implemented)

3. **speckit.js (lines 29-42):** Added model lock during execution
   - Prevents switching models while `isRunning = true`
   - Shows error message if attempted

4. **route_speckit.py (lines 190-220):** Added `/artifacts/{type}` endpoint
   - Retrieves spec.md, plan.md, tasks.md from `specs/branch-name/`
   - Uses git branch to find feature directory

### Critical Findings

**✅ Slash Commands Don't Work with `-p` Flag:**
- `claude -p "content"` treats input as plain text, ignores frontmatter/handoffs
- Solution: Load template files (`.claude/commands/speckit.*.md`), replace `$ARGUMENTS`, pass full content
- Both CLIs now use symmetric approach (Approach B from plan)

**✅ Stateless One-Shot Execution:**
- Each Speckit command is a fresh CLI invocation
- No persistent sessions needed
- File-based state enables seamless hot-swapping
- Both CLIs use subscription login (no API keys)

### Issues Encountered

**🔴 Issue #1: Server Restart Failure (2025-12-02)**
- **Problem:** Attempted to restart local Mac server to pick up stderr capture changes
- **Action:** Killed PIDs 682, 29207, 29326 (running on port 8080)
- **Result:** Server failed to restart due to missing dependencies (`aiohttp`, `pydantic_settings`)
- **Root Cause:** Wrong Python environment (venv not activated, or dependencies not installed)
- **Impact:** Local testing blocked
- **Note:** User's original server was likely started differently (Cloud Run proxy setup?)

**✅ Issue #2: Claude CLI Exiting with Code 1 (RESOLVED)**
- **Symptom:** Process starts but immediately fails
  ```
  Starting Speckit Agent (specify) with claude in /Users/dlybeck/Documents/Portfolio
  Process completed with exit code: 1
  ```
- **Root Cause:** Frontmatter YAML delimiters (`---`) in template files were being passed to `claude -p`, causing CLI to interpret them as command-line options
- **Error Message:** `error: unknown option '---`
- **Fix Applied:** Strip frontmatter before passing to CLI (lines 165-171 of route_speckit.py)
  ```python
  if template.startswith("---"):
      parts = template.split("---", 2)
      if len(parts) >= 3:
          template = parts[2].strip()  # Keep only content after frontmatter
  ```
- **Status:** Fixed, ready for testing

**⚠️ Issue #3: WebSocket Endpoint Missing**
- **Symptom:** `WebSocket connection to 'ws://localhost:8080/api/speckit/ws' failed: 403`
- **Status:** Endpoint not implemented yet
- **Impact:** Frontend can't receive real-time updates

**✅ Issue #4: Artifacts 404 (Expected)**
- **Symptom:** `/api/speckit/artifacts/spec` returns 404
- **Status:** Expected behavior when no artifacts generated yet
- **Resolution:** Endpoint implemented correctly

### Key Lessons

1. **Always capture stderr in subprocess execution** - Without it, debugging failures is impossible
2. **Server restart requires proper environment** - Need to find correct startup method
3. **Cloud Run proxy complicates local testing** - User might be testing via `davidlybeck.com` (Cloud Run) → SOCKS proxy → Mac
4. **Document everything** - User explicitly requested: "Document document document and use that documentation to learn"

### Recovery from Server Restart Issue

**Problem:** Killed running server (PIDs 682, 29207, 29326), couldn't restart due to missing dependencies.

**Root Cause:** The startup script `scripts/start-local-dev.sh` creates a venv in `scripts/.venv`, but dependencies weren't installed in that venv (script checks for fastapi but doesn't ensure ALL dependencies are present).

**Solution:**
1. Manually installed requirements: `cd scripts && source .venv/bin/activate && pip install -r ../requirements.txt`
2. Re-ran startup script: `scripts/start-local-dev.sh`
3. Server now running on port 8080 (PID 30733)

**Lesson:** The venv check in start-local-dev.sh is incomplete - it only checks if fastapi is importable, not if ALL requirements are installed.

### Next Steps

1. **Test Speckit command via web UI** - Server is running, need to trigger a command to capture stderr
2. **Diagnose Claude CLI exit code 1** - Check logs for [stderr] output
3. **Fix Claude CLI execution issue** - Once we see the error
4. **Implement WebSocket endpoint** - Pattern exists in `route_dev_proxy.py`