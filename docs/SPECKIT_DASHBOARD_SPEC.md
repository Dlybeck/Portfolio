# Speckit Mobile Dashboard - Design Spec

## 1. Architecture Overview
This is a custom Web UI wrapper around the `speckit` CLI tool, hosted on the user's Mac and proxied via Cloud Run. It is designed for mobile-first, visual interaction with AI development workflows.

## 2. Multi-Model Support (Hot-Swapping)
*   **Mechanism:** Speckit supports the `--ai` flag (e.g., `specify init --ai claude` or `specify init --ai gemini`).
*   **Hot-Swapping:** Since Speckit's state is maintained in the filesystem (via `.specify/` directory and Markdown files), switching models is effectively stateless for the tool itself. The backend wrapper will simply invoke the CLI with the user's chosen model flag for each command.
*   **Dashboard UI:** A global dropdown in the top navbar allows toggling between "Claude Code" and "Gemini CLI". This selection persists in the session and dynamically alters the CLI command sent to the backend (e.g., injecting `--ai claude` vs `--ai gemini`).

## 3. The "Card" UI Concept
This is **NOT** a complex drag-and-drop builder like Agor. It is a **State Visualizer**.

*   **Visual Metaphor:** Think "Trello Card" or "GitHub Issue", not "Wix Builder".
*   **Static vs. Interactive:**
    *   **Plan Phase:** Displays a list of proposed files/architectural decisions. Interactive elements are simple toggles (Check/Uncheck to include/exclude) or a text field for "Refinement Feedback".
    *   **Task Phase:** A dynamic checklist. Items turn green/red based on CLI output. You can tap a task to "Retry" or "Skip", but you don't drag them around.
    *   **Why:** Drag-and-drop is finicky on mobile. Big tap targets and clear state changes are better.

## 4. User Flow (Mobile)
1.  **Goal Input:** Simple chat box. "Create a dark mode toggle."
2.  **Spec Card:** A card appears summarizing the requirements.
    *   *Action:* [Edit] [Approve]
3.  **Plan Card:** A structured list of files to create/modify.
    *   *Action:* [Regenerate] [Approve]
4.  **Execution View:** The card collapses into a progress bar. Real-time logs stream below.
    *   *State:* "Implementing 1/5 tasks..."

## 5. Implementation Details
*   **Backend:** `route_speckit.py` (FastAPI) using `asyncio` to run `speckit` subprocesses.
*   **Parsing:** Regex/Markdown parsing of CLI `stdout` to populate the JSON data for the frontend cards.
*   **State:** Redis or in-memory dict to track the current "Active Card" state for the session.
