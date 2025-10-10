"""
Persistent Session Manager
Manages persistent terminal sessions with multi-client support
Allows multiple devices to connect to the same terminal session
"""

import asyncio
import json
import time
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
        self.broadcast_task: Optional[asyncio.Task] = None  # Single broadcast loop
        self.claude_started: bool = False  # Track if Claude has been auto-started
        self.claude_start_lock: asyncio.Lock = asyncio.Lock()  # Prevent race conditions
        self.last_activity: float = time.time()  # Track last activity for cleanup

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
        self.last_activity = time.time()  # Update activity
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
            self.last_activity = time.time()  # Update activity on write

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

    async def start_broadcast_loop(self):
        """Start the broadcast loop (only runs once per session)"""
        if self.broadcast_task is not None:
            return  # Already running

        async def broadcast_loop():
            """Read from terminal and broadcast to all clients"""
            print(f"[SessionManager] Starting broadcast loop for '{self.session_id}'")
            while True:
                try:
                    # Collect all available output
                    chunks = []
                    deadline = asyncio.get_event_loop().time() + 0.016  # 16ms = ~60fps

                    while asyncio.get_event_loop().time() < deadline:
                        output = self.read(timeout=0.001)
                        if output:
                            chunks.append(output)
                        else:
                            break

                    # Broadcast accumulated data to all clients
                    if chunks:
                        combined_output = "".join(chunks)
                        await self.broadcast(combined_output)

                    # Wait for next frame
                    await asyncio.sleep(0.016)
                except Exception as e:
                    print(f"[SessionManager] Broadcast loop error: {e}")
                    await asyncio.sleep(0.1)

        self.broadcast_task = asyncio.create_task(broadcast_loop())

    def is_broadcast_running(self) -> bool:
        """Check if broadcast loop is running"""
        return self.broadcast_task is not None and not self.broadcast_task.done()

    def close(self):
        """Explicitly close terminal session (only when requested)"""
        # Cancel broadcast task
        if self.broadcast_task:
            self.broadcast_task.cancel()

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
            "buffer_size": len(session.output_buffer),
            "idle_seconds": int(time.time() - session.last_activity)
        }
        for sid, session in _persistent_sessions.items()
    }


async def cleanup_idle_sessions(idle_timeout: int = 3600):
    """
    Background task to cleanup idle sessions
    Args:
        idle_timeout: Seconds of inactivity before closing session (default: 1 hour)
    """
    while True:
        try:
            current_time = time.time()
            to_close = []

            for session_id, session in _persistent_sessions.items():
                # Only cleanup sessions with no connected clients
                if len(session.connected_clients) == 0:
                    idle_time = current_time - session.last_activity
                    if idle_time > idle_timeout:
                        to_close.append(session_id)
                        print(f"[SessionManager] Closing idle session '{session_id}' (idle for {int(idle_time)}s)")

            # Close idle sessions
            for session_id in to_close:
                close_persistent_session(session_id)

            # Check every 5 minutes
            await asyncio.sleep(300)
        except Exception as e:
            print(f"[SessionManager] Cleanup error: {e}")
            await asyncio.sleep(60)
