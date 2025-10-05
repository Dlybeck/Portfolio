"""
Session State Persistence
Saves and loads session metadata to/from disk
Allows sessions to persist across server restarts
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime


class SessionState:
    """Manages persistent state for a terminal session"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.storage_dir = Path.home() / ".dev_portal_sessions"
        self.state_file = self.storage_dir / f"{session_id}.json"

        # Create storage directory if it doesn't exist
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save(self, state_data: Dict):
        """
        Save session state to disk

        Args:
            state_data: Dictionary containing state to save
                       (e.g., {"working_dir": "/path", "terminal_rows": 24, ...})
        """
        # Load existing state
        existing_state = self.load() or {}

        # Merge with new data
        existing_state.update(state_data)
        existing_state["last_updated"] = datetime.now().isoformat()

        # Write to disk
        try:
            with open(self.state_file, 'w') as f:
                json.dump(existing_state, f, indent=2)
            print(f"[SessionState] Saved state for '{self.session_id}': {state_data}")
        except Exception as e:
            print(f"[SessionState] Error saving state: {e}")

    def load(self) -> Optional[Dict]:
        """
        Load session state from disk

        Returns:
            Dictionary containing session state, or None if no saved state
        """
        if not self.state_file.exists():
            return None

        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
            print(f"[SessionState] Loaded state for '{self.session_id}': {state}")
            return state
        except Exception as e:
            print(f"[SessionState] Error loading state: {e}")
            return None

    def delete(self):
        """Delete saved state file"""
        if self.state_file.exists():
            self.state_file.unlink()
            print(f"[SessionState] Deleted state for '{self.session_id}'")

    def get_working_dir(self) -> Optional[str]:
        """Get saved working directory"""
        state = self.load()
        return state.get("working_dir") if state else None

    def get_terminal_size(self) -> Optional[tuple]:
        """Get saved terminal size (rows, cols)"""
        state = self.load()
        if state and "terminal_rows" in state and "terminal_cols" in state:
            return (state["terminal_rows"], state["terminal_cols"])
        return None

    def is_claude_running(self) -> bool:
        """Check if Claude was running in last session"""
        state = self.load()
        return state.get("claude_running", False) if state else False

    def set_claude_status(self, running: bool):
        """Save Claude running status"""
        self.save({"claude_running": running})
