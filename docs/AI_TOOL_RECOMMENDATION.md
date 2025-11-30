# AI Tooling Research & Recommendation Report (Late 2025)

**Objective:** Identify a visual, structured AI development tool to complement VS Code/CLI, ideally suitable for mobile use and integrating with existing subscriptions (Claude Code, Gemini CLI).

**Core Constraint:** The user prefers "Speckit" (GitHub CLI tool) but needs a mobile-friendly Web UI wrapper for it, rather than a purely text-based CLI.

## 1. Landscape Analysis (Late 2025)
The market has bifurcated into:
*   **Full-Blown Web IDEs:** Tools like `Bolt.new`, `Replit Agent`, and `OpenWebUI`. These are powerful but often redundant if you already have a robust VS Code setup.
*   **AI-Native Editors:** `Cursor`, `Windsurf` (VS Code forks). Great for desktop, bad for mobile.
*   **CLI Agents:** `Speckit`, `Claude Code`, `Aider`. Powerful automation but poor mobile UX.

**The Gap:** There is no "official" mobile GUI for Speckit or Claude Code.

## 2. Deep Dive: Speckit (GitHub)
**What it is:** A "Spec-Driven Development" (SDD) CLI tool.
**Key Workflow:**
1.  `/speckit.specify`: Define the "what" and "why".
2.  `/speckit.plan`: Generate a technical plan (architecture, stack).
3.  `/speckit.tasks`: Break down the plan into actionable tasks.
4.  `/speckit.implement`: Execute the code changes.

**Why it fits your goal:**
*   **Structured:** It inherently uses the "Plan -> Task -> Code" structure you liked in Agor.
*   **Visualizable:** The distinct phases (Specification, Plan, Task List) map *perfectly* to a tab-based UI.
*   **Output:** It uses Markdown templates, which are easy to parse and render as HTML cards.

## 3. Recommendation: "Speckit Mobile Dashboard" (Custom Wrapper)
Instead of buying a new tool, **build a lightweight Web UI wrapper for Speckit** hosted on your Mac.

### Architecture
*   **Backend:** Your existing FastAPI app.
*   **Process Management:** `asyncio` subprocesses to run `speckit` commands.
*   **Frontend:** A mobile-first Web UI (HTML/JS) with tabs for each Speckit phase.

### How it works (The "Agor-like" Experience)
1.  **Tab 1: Specify (Chat):**
    *   You type: "Create a login page."
    *   Backend runs: `speckit specify "Create a login page"`
    *   UI shows: The generated Markdown spec. You click "Approve".
2.  **Tab 2: Plan (Visual Card):**
    *   Backend runs: `speckit plan`
    *   UI shows: A structured list of tech choices and architecture. You click "Refine" or "Approve".
3.  **Tab 3: Tasks (Checklist):**
    *   Backend runs: `speckit tasks`
    *   UI shows: An interactive checklist. As Speckit completes items, they turn green in real-time.
4.  **Tab 4: Implement (Terminal/Logs):**
    *   Backend runs: `speckit implement`
    *   UI shows: Real-time logs of files being edited.

### Feasibility & Cost
*   **Cost:** $0 (Uses your existing Mac + Cloud Run).
*   **Effort:** Low. We can reuse the `route_dev_proxy.py` logic. The backend just needs to stream stdout/stderr to a WebSocket.
*   **Mobile UX:** We can make big, thumb-friendly buttons for the core interactions (Approve, Next Phase).

## 4. Implementation Plan (Next Steps)
If you approve this direction, I can proceed to:
1.  **Install Speckit:** Ensure `speckit` is installed on your Mac server.
2.  **Create Wrapper:** Add a new `route_speckit.py` to your FastAPI app.
3.  **Build UI:** Create a `speckit_dashboard.html` template with the tabbed interface.

This effectively gives you "Agor for Speckit" — a structured, visual, mobile-friendly way to drive your CLI agent.
