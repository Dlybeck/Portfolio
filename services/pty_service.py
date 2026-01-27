import asyncio
import os
import pty
import struct
import fcntl
import termios
from fastapi import WebSocket, WebSocketDisconnect
import logging

logger = logging.getLogger(__name__)

class PTYService:
    def __init__(self):
        self.sessions = {}
    
    async def handle_pty_websocket(self, websocket: WebSocket, pty_id: str, directory: str = None):
        await websocket.accept()
        logger.info(f"PTY session started: {pty_id}, dir: {directory}")
        
        if directory and not os.path.isdir(directory):
            directory = os.path.expanduser("~")
        
        master_fd, slave_fd = pty.openpty()
        
        pid = os.fork()
        if pid == 0:
            os.setsid()
            os.dup2(slave_fd, 0)
            os.dup2(slave_fd, 1)
            os.dup2(slave_fd, 2)
            
            if directory:
                os.chdir(directory)
            
            os.execvp("/bin/bash", ["/bin/bash"])
        
        os.close(slave_fd)
        
        async def read_from_pty():
            loop = asyncio.get_event_loop()
            while True:
                try:
                    data = await loop.run_in_executor(None, os.read, master_fd, 4096)
                    if not data:
                        break
                    await websocket.send_bytes(data)
                except Exception as e:
                    logger.error(f"PTY read error: {e}")
                    break
        
        async def write_to_pty():
            try:
                while True:
                    message = await websocket.receive()
                    if message.get("type") == "websocket.disconnect":
                        break
                    
                    if "bytes" in message:
                        os.write(master_fd, message["bytes"])
                    elif "text" in message:
                        import json
                        try:
                            data = json.loads(message["text"])
                            if data.get("type") == "resize":
                                rows = data.get("rows", 24)
                                cols = data.get("cols", 80)
                                winsize = struct.pack("HHHH", rows, cols, 0, 0)
                                fcntl.ioctl(master_fd, termios.TIOCSWINSZ, winsize)
                        except:
                            os.write(master_fd, message["text"].encode())
            except WebSocketDisconnect:
                pass
            except Exception as e:
                logger.error(f"PTY write error: {e}")
        
        try:
            await asyncio.gather(read_from_pty(), write_to_pty())
        finally:
            try:
                os.close(master_fd)
                os.kill(pid, 9)
                os.waitpid(pid, 0)
            except:
                pass
            logger.info(f"PTY session ended: {pty_id}")

pty_service = PTYService()
