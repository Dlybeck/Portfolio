"""
Persistent Session Manager
Manages persistent terminal sessions with multi-client support
Allows multiple devices to connect to the same terminal session
"""

import asyncio
import json
from typing import Set, Optional
from collections import deque
from fastapi import WebSocket
from services.terminal_service import TerminalSession
from services.session_state import SessionState
import os


class PersistentSession:
    """A persistent terminal session that supports multiple connected clients"""

    def __init__(self, session_id: str, working_dir: str = None, command: str = "bash"):
        self.session_id = session_id
        self.terminal: Optional[TerminalSession] = None
        self.connected_clients: Set[WebSocket] = set()
        self.output_buffer: deque = deque(maxlen=10000)  # Keep last 10k lines
        self.working_dir = working_dir or os.path.expanduser("~")
        self.command = command
        self.state = SessionState(session_id)

        # Start terminal session
        self._start_terminal()

    def _start_terminal(self):
        """Start the terminal session"""
        # Load saved state if exists
        saved_state = self.state.load()
        if saved_state:
            self.working_dir = saved_state.get("working_dir", self.working_dir)

        # Create terminal
        self.terminal = TerminalSession(command=self.command, working_dir=self.working_dir)
        self.terminal.start()

        print(f"[SessionManager] Started persistent session '{self.session_id}' in {self.working_dir}")

    def add_client(self, websocket: WebSocket):
        """Add a client to this session"""
        self.connected_clients.add(websocket)
        print(f"[SessionManager] Client connected to '{self.session_id}'. Total clients: {len(self.connected_clients)}")

    def remove_client(self, websocket: WebSocket):
        """Remove a client from this session (but keep terminal alive)"""
        self.connected_clients.discard(websocket)
        print(f"[SessionManager] Client disconnected from '{self.session_id}'. Remaining clients: {len(self.connected_clients)}")
        # Note: We do NOT close the terminal even if no clients connected

    async def broadcast(self, data: str):
        """Broadcast terminal output to all connected clients"""
        # Add to buffer for history
        self.output_buffer.append(data)

        # Send to all connected clients
        message = json.dumps({"type": "output", "data": data})
        disconnected = set()

        for client in self.connected_clients:
            try:
                await client.send_text(message)
            except Exception as e:
                print(f"[SessionManager] Error sending to client: {e}")
                disconnected.add(client)

        # Remove disconnected clients
        for client in disconnected:
            self.remove_client(client)

    def get_buffered_history(self) -> str:
        """Get all buffered terminal output for new clients"""
        return "".join(self.output_buffer)

    def write(self, data: str):
        """Write data to terminal"""
        if self.terminal:
            self.terminal.write(data)

    def resize(self, rows: int, cols: int):
        """Resize terminal"""
        if self.terminal:
            self.terminal.resize(rows, cols)
            # Save terminal size
            self.state.save({"terminal_rows": rows, "terminal_cols": cols})

    def update_working_dir(self, path: str):
        """Update and save working directory"""
        self.working_dir = path
        self.state.save({"working_dir": path})

    def read(self, timeout: float = 0.1) -> Optional[str]:
        """Read from terminal"""
        if self.terminal:
            return self.terminal.read(timeout)
        return None

    def close(self):
        """Explicitly close terminal session (only when requested)"""
        if self.terminal:
            self.terminal.close()
            print(f"[SessionManager] Closed persistent session '{self.session_id}'")


# Global persistent sessions storage
_persistent_sessions = {}


def get_or_create_persistent_session(
    session_id: str,
    working_dir: str = None,
    command: str = "bash"
) -> PersistentSession:
    """
    Get existing persistent session or create new one

    Args:
        session_id: Unique session identifier (e.g., "user_main_session")
        working_dir: Initial working directory
        command: Command to run (default: "bash")

    Returns:
        PersistentSession instance
    """
    if session_id not in _persistent_sessions:
        _persistent_sessions[session_id] = PersistentSession(
            session_id=session_id,
            working_dir=working_dir,
            command=command
        )

    return _persistent_sessions[session_id]


def close_persistent_session(session_id: str):
    """
    Explicitly close a persistent session
    This should only be called when user requests session termination
    """
    if session_id in _persistent_sessions:
        _persistent_sessions[session_id].close()
        del _persistent_sessions[session_id]
        print(f"[SessionManager] Removed persistent session '{session_id}'")


def get_all_sessions():
    """Get all active persistent sessions (for debugging/monitoring)"""
    return {
        sid: {
            "clients": len(session.connected_clients),
            "working_dir": session.working_dir,
            "buffer_size": len(session.output_buffer)
        }
        for sid, session in _persistent_sessions.items()
    }
