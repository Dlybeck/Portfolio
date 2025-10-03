"""
Terminal service with PTY support
Manages interactive terminal sessions via WebSocket
"""

import os
import pty
import subprocess
import select
import struct
import fcntl
import termios
from typing import Optional


class TerminalSession:
    """Manages a PTY terminal session"""

    def __init__(self, command: str = None, working_dir: str = None):
        self.command = command or "bash"
        self.working_dir = working_dir or os.path.expanduser("~")
        self.pid = None
        self.fd = None

    def start(self):
        """Start the terminal session"""
        # Create PTY
        self.pid, self.fd = pty.fork()

        if self.pid == 0:
            # Child process
            os.chdir(self.working_dir)

            # Set environment
            env = os.environ.copy()
            env['TERM'] = 'xterm-256color'
            env['PS1'] = r'\[\e[32m\]\u@\h\[\e[0m\]:\[\e[34m\]\w\[\e[0m\]\$ '

            # Execute command
            os.execvpe(self.command, [self.command], env)
        else:
            # Parent process - set non-blocking
            flags = fcntl.fcntl(self.fd, fcntl.F_GETFL)
            fcntl.fcntl(self.fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

    def resize(self, rows: int, cols: int):
        """Resize terminal"""
        if self.fd:
            winsize = struct.pack("HHHH", rows, cols, 0, 0)
            fcntl.ioctl(self.fd, termios.TIOCSWINSZ, winsize)

    def write(self, data: str):
        """Write data to terminal"""
        if self.fd:
            os.write(self.fd, data.encode())

    def read(self, timeout: float = 0.1) -> Optional[str]:
        """Read data from terminal (non-blocking, incremental)"""
        if not self.fd:
            return None

        # Check if data available
        readable, _, _ = select.select([self.fd], [], [], timeout)

        if readable:
            try:
                # Read in smaller chunks for smoother updates
                data = os.read(self.fd, 1024)
                if data:
                    return data.decode('utf-8', errors='ignore')
            except (OSError, BlockingIOError):
                return None

        return None

    def close(self):
        """Close terminal session"""
        if self.fd:
            os.close(self.fd)
        if self.pid:
            try:
                os.kill(self.pid, 9)
            except:
                pass


# Global sessions storage (in production, use Redis or database)
terminal_sessions = {}


def get_or_create_session(session_id: str, command: str = None) -> TerminalSession:
    """Get existing session or create new one"""
    if session_id not in terminal_sessions:
        terminal_sessions[session_id] = TerminalSession(command=command)
        terminal_sessions[session_id].start()

    return terminal_sessions[session_id]


def close_session(session_id: str):
    """Close and remove session"""
    if session_id in terminal_sessions:
        terminal_sessions[session_id].close()
        del terminal_sessions[session_id]
