# Deep Dive Investigation: Speckit (Spec Kit) Mobile Dashboard

**Status:** Pre-Implementation Analysis
**Goal:** Identify "holes," risks, and technical blockers in the proposed plan to wrap GitHub's `spec-kit` (CLI: `specify`) in a mobile-friendly Web UI.

## 1. The "Interactive Mode" Risk (CRITICAL)
**Hypothesis:** The `specify` CLI is designed for a human typing in a terminal. It likely uses interactive prompts ("Select your AI:", "Confirm this plan? [y/N]").
**Risk:** If the wrapper (FastAPI) runs `specify` in a subprocess, it might hang indefinitely waiting for input that the user can't provide via a standard HTTP request.
**Investigation Needed:**
*   Does `specify` have a `--non-interactive` or `--yes` flag?
*   Does it support piping input (e.g., `echo "y" | specify ...`)?
*   **Mitigation:** We might need to use `ptyprocess` (like the terminal) instead of `subprocess` to "fake" a TTY and programmatically send keystrokes.

## 2. Authentication & Token Management
**Hypothesis:** `specify` relies on the underlying AI tools (e.g., `claude`, `gh copilot`). These tools store auth tokens in `~/.config/...`.
**Risk:**
*   **Cloud Run:** The container is ephemeral. Where do these tokens come from?
*   **User Context:** If User A logs in, does `specify` run as root? Does it have access to the token?
*   **Mitigation:** We need to inject tokens via Environment Variables (`ANTHROPIC_API_KEY`, `GITHUB_TOKEN`) into the subprocess environment at runtime.

## 3. Concurrency & State Locking
**Hypothesis:** `specify` writes state to `.specify/` directory.
**Risk:**
*   What if Tab A runs `specify plan` and Tab B runs `specify tasks` *at the same time*?
*   **Corruption:** The markdown files might get corrupted.
*   **Mitigation:** The backend *must* implement a **Session Lock**. Only one active `specify` process allowed per project/session. The UI should show "Busy" to other tabs.

## 4. The "Hot Swap" Reality
**Hypothesis:** We can switch from Claude to Gemini between phases.
**The Gap:**
*   Does `specify` bake the model name into `.specify/config.yaml`?
*   If we run `specify plan --ai gemini`, does it overwrite the config?
*   **Investigation:** We need to verify if the `--ai` flag overrides the project config *temporarily* or *permanently*.
*   **Risk:** If it's permanent, swapping back and forth might be "noisy" in git (constant config changes).

## 5. Mobile UI vs. Streaming Output
**Hypothesis:** We want "Cards", not "Logs".
**The Gap:**
*   `specify` outputs raw text/markdown to stdout.
*   **Parsing Complexity:** To show a "Checkbox", we need to reliably parse `[ ] Task Name` from the stdout stream *in real-time*.
*   **Fragility:** If `specify` changes its output format (e.g., updates to v2), our regex parser breaks.
*   **Mitigation:**
    *   **Primary View:** Stream raw HTML (converted from Markdown logs) for safety.
    *   **Secondary View:** "Smart Cards" strictly for the *artifacts* (reading `specs.md`, `plan.md` from disk) rather than parsing the CLI stream. **This is safer.** Read the *file* to build the UI, not the log stream.

## 6. System Dependencies (Cloud Run)
**Hypothesis:** We just `pip install`.
**The Reality:**
*   `specify` needs `uv`.
*   It might need `node` (some sources mentioned npm).
*   It definitely needs `git`.
*   It needs the AI agents themselves (`claude`, `gh`, `gemini`) installed and in PATH.
*   **Blocker:** Our current `Dockerfile` might lack these. We need to audit the Dockerfile.

## 7. Conclusion & Strategy Adjustment
The "Card" idea based on *stream parsing* is risky.
**Better Strategy:**
1.  **Run** the command via WebSocket (stream logs for transparency).
2.  **Watch** the file system (`.specify/plans/current.md`).
3.  **Render** the UI based on the *File Content*, not the log stream. This is the "Single Source of Truth".
