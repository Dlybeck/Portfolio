"""
Claude Code integration service
Executes claude CLI commands and returns responses
"""

import subprocess
import os
from pathlib import Path


async def execute_claude_command(message: str, working_dir: str = None) -> dict:
    """
    Execute a claude code command and return the response

    Args:
        message: The user's message/prompt for Claude
        working_dir: Optional working directory for the command

    Returns:
        dict with 'response' and optional 'terminal_output'
    """
    if working_dir is None:
        working_dir = str(Path.home())

    try:
        # Execute claude command
        # Note: This will use the claude CLI installed on the system
        result = subprocess.run(
            ['claude', message],
            cwd=working_dir,
            capture_output=True,
            text=True,
            timeout=60  # 60 second timeout
        )

        # Combine stdout and stderr
        output = result.stdout
        if result.stderr:
            output += "\n" + result.stderr

        return {
            "response": output or "Command executed successfully",
            "terminal_output": output,
            "exit_code": result.returncode
        }

    except subprocess.TimeoutExpired:
        return {
            "response": "Command timed out after 60 seconds",
            "terminal_output": None,
            "exit_code": 124
        }
    except FileNotFoundError:
        return {
            "response": "Claude Code CLI not found. Please ensure 'claude' is installed and in your PATH.",
            "terminal_output": None,
            "exit_code": 127
        }
    except Exception as e:
        return {
            "response": f"Error executing command: {str(e)}",
            "terminal_output": None,
            "exit_code": 1
        }
