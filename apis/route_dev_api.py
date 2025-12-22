"""
Dev Dashboard API Routes
"""

from fastapi import APIRouter, Depends, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, StreamingResponse
from pydantic import BaseModel
from core.security import get_current_user, get_session_user
from services.session_manager import get_or_create_persistent_session, close_persistent_session
from services.socks5_connection_manager import proxy_request
import json
import asyncio
import os
from pathlib import Path
import mimetypes
from core.config import settings
import logging

logger = logging.getLogger(__name__)

dev_api_router = APIRouter(prefix="/dev/api", tags=["Dev Dashboard - API"])


class ChatRequest(BaseModel):
    message: str
    working_dir: str = None


class DirectoryRequest(BaseModel):
    path: str


@dev_api_router.post("/list-directory")
async def list_directory(
    req: Request,
    user: dict = Depends(get_current_user)
):
    """List directories - proxy if Cloud Run, execute locally if Mac"""
    if settings.K_SERVICE is not None:
        # Cloud Run: Proxy to Mac via connection manager
        try:
            body = await req.body()
            auth_header = req.headers.get("Authorization", "")
            headers = {
                "Content-Type": "application/json",
                "Authorization": auth_header
            }
            response = await proxy_request(
                "POST",
                f"http://{settings.MAC_SERVER_IP}:{settings.MAC_SERVER_PORT}/dev/api/list-directory",
                content=body,
                headers=headers
            )
            return JSONResponse(content=response.json(), status_code=response.status_code)
        except Exception as e:
            return JSONResponse(content={"error": str(e)}, status_code=500)
    else:
        # Mac: Execute locally
        class DirectoryRequest(BaseModel):
            path: str

        try:
            body = await req.json()
            dir_req = DirectoryRequest(**body)

            # Expand ~ to home directory
            path = os.path.expanduser(dir_req.path)
            path_obj = Path(path)

            # Security: ensure path is absolute and exists
            if not path_obj.is_absolute():
                path_obj = Path.home() / path

            if not path_obj.exists() or not path_obj.is_dir():
                return JSONResponse(content={"error": "Directory not found"}, status_code=404)

            # List both directories and files (not hidden)
            directories = []
            files = []
            for item in sorted(path_obj.iterdir()):
                if item.name.startswith('.'):
                    continue
                if item.is_dir():
                    directories.append({
                        "name": item.name,
                        "path": str(item),
                        "type": "directory"
                    })
                elif item.is_file():
                    files.append({
                        "name": item.name,
                        "path": str(item),
                        "type": "file"
                    })

            response_data = {
                "directories": directories,
                "files": files,
                "current": str(path_obj),
                "is_root": path_obj == path_obj.parent
            }
            logger.debug(f"Returning {len(directories)} dirs, {len(files)} files for {path_obj}")
            return JSONResponse(content=response_data)
        except Exception as e:
            return JSONResponse(content={"error": str(e)}, status_code=500)


@dev_api_router.post("/parent-directory")
async def parent_directory(
    req: Request,
    user: dict = Depends(get_current_user)
):
    """Get parent directory - proxy if Cloud Run, execute locally if Mac"""
    if settings.K_SERVICE is not None:
        # Cloud Run: Proxy to Mac via connection manager
        try:
            body = await req.body()
            auth_header = req.headers.get("Authorization", "")
            headers = {
                "Content-Type": "application/json",
                "Authorization": auth_header
            }
            response = await proxy_request(
                "POST",
                f"http://{settings.MAC_SERVER_IP}:{settings.MAC_SERVER_PORT}/dev/api/parent-directory",
                content=body,
                headers=headers
            )
            return JSONResponse(content=response.json(), status_code=response.status_code)
        except Exception as e:
            return JSONResponse(content={"error": str(e)}, status_code=500)
    else:
        # Mac: Execute locally
        class DirectoryRequest(BaseModel):
            path: str

        try:
            body = await req.json()
            dir_req = DirectoryRequest(**body)

            path = os.path.expanduser(dir_req.path)
            path_obj = Path(path)
            parent = path_obj.parent

            return JSONResponse(content={"parent": str(parent)})
        except Exception as e:
            return JSONResponse(content={"error": str(e)}, status_code=500)


@dev_api_router.get("/read-file")
async def read_file(
    path: str,
    req: Request,
    token: str = None
):
    """
    Read file and return its content - proxy if Cloud Run, execute locally if Mac
    Supports both header-based auth and query parameter token (for window.open)
    """
    # Authenticate either via query token or Authorization header
    authenticated = False

    if token:
        # Query parameter token (for window.open)
        try:
            from core.security import verify_token
            payload = verify_token(token)
            if payload.get("type") == "access":
                authenticated = True
                logger.debug(f"Query token authenticated for user: {payload.get('sub')}")
        except Exception as e:
            logger.warning(f"Query token authentication failed: {e}")

    if not authenticated:
        # Try Authorization header
        auth_header = req.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            header_token = auth_header.replace("Bearer ", "")
            try:
                from core.security import verify_token
                payload = verify_token(header_token)
                if payload.get("type") == "access":
                    authenticated = True
                    logger.debug(f"Header token authenticated for user: {payload.get('sub')}")
            except Exception as e:
                logger.warning(f"Header token authentication failed: {e}")

        if not authenticated:
            return JSONResponse(content={"error": "Unauthorized"}, status_code=401)

    if settings.K_SERVICE is not None:
        # Cloud Run: Proxy to Mac via connection manager
        try:
            # Get the original Authorization header from the request
            auth_header = req.headers.get("Authorization", "")
            headers = {"Authorization": auth_header}
            response = await proxy_request(
                "GET",
                f"http://{settings.MAC_SERVER_IP}:{settings.MAC_SERVER_PORT}/dev/api/read-file",
                params={"path": path},
                headers=headers
            )
            # Return file content with appropriate content type and length
            content_type = response.headers.get("content-type", "application/octet-stream")
            content_length = response.headers.get("content-length")

            response_headers = {"Content-Disposition": f'inline; filename="{Path(path).name}"'}
            if content_length:
                response_headers["Content-Length"] = content_length

            return StreamingResponse(
                iter([response.content]),
                media_type=content_type,
                headers=response_headers
            )
        except Exception as e:
            return JSONResponse(content={"error": str(e)}, status_code=500)
    else:
        # Mac: Execute locally
        try:
            file_path = os.path.expanduser(path)
            path_obj = Path(file_path)

            # Security: ensure file exists and is a file
            if not path_obj.exists() or not path_obj.is_file():
                return JSONResponse(content={"error": "File not found"}, status_code=404)

            # Guess content type
            content_type, _ = mimetypes.guess_type(file_path)
            if not content_type:
                content_type = "application/octet-stream"

            return FileResponse(
                file_path,
                media_type=content_type,
                headers={"Content-Disposition": f'inline; filename="{path_obj.name}"'}
            )
        except Exception as e:
            logger.error(f"Failed to read file {path}: {e}")
            import traceback
            traceback.print_exc()
            return JSONResponse(content={"error": str(e)}, status_code=500)


@dev_api_router.post("/save-file")
async def save_file(
    req: Request,
    user: dict = Depends(get_current_user)
):
    """
    Save file content - proxy if Cloud Run, execute locally if Mac
    Requires authentication (JWT token)
    """
    if settings.K_SERVICE is not None:
        # Cloud Run: Proxy to Mac via connection manager
        try:
            body = await req.body()
            auth_header = req.headers.get("Authorization", "")
            headers = {
                "Content-Type": "application/json",
                "Authorization": auth_header
            }
            response = await proxy_request(
                "POST",
                f"http://{settings.MAC_SERVER_IP}:{settings.MAC_SERVER_PORT}/dev/api/save-file",
                content=body,
                headers=headers
            )
            return JSONResponse(content=response.json(), status_code=response.status_code)
        except Exception as e:
            return JSONResponse(content={"error": str(e)}, status_code=500)
    else:
        # Mac: Execute locally
        class SaveFileRequest(BaseModel):
            path: str
            content: str

        try:
            body = await req.json()
            save_req = SaveFileRequest(**body)

            # Security validations
            file_path = save_req.path

            # Validate file path is absolute
            if not os.path.isabs(file_path):
                return JSONResponse(
                    content={"error": "File path must be absolute"},
                    status_code=400
                )

            # Prevent directory traversal attacks
            if ".." in file_path:
                return JSONResponse(
                    content={"error": "Invalid file path (directory traversal not allowed)"},
                    status_code=400
                )

            # Expand ~ to home directory
            file_path = os.path.expanduser(file_path)
            path_obj = Path(file_path)

            # Check file exists
            if not path_obj.exists():
                return JSONResponse(
                    content={"error": "File not found"},
                    status_code=404
                )

            # Check it's a file (not a directory)
            if not path_obj.is_file():
                return JSONResponse(
                    content={"error": "Path is not a file"},
                    status_code=400
                )

            # Check file is writable
            if not os.access(file_path, os.W_OK):
                return JSONResponse(
                    content={"error": "Permission denied - file is not writable"},
                    status_code=403
                )

            # Write content to file with UTF-8 encoding
            # Preserve line endings (don't convert)
            bytes_written = path_obj.write_text(save_req.content, encoding='utf-8')

            logger.debug(f"Saved {bytes_written} bytes to {file_path}")

            return JSONResponse(content={
                "success": True,
                "message": f"File saved successfully",
                "bytes_written": bytes_written,
                "path": str(path_obj)
            })

        except PermissionError as e:
            return JSONResponse(
                content={"error": f"Permission denied: {str(e)}"},
                status_code=403
            )
        except Exception as e:
            logger.error(f"Failed to save file: {e}", exc_info=True)
            return JSONResponse(
                content={"error": str(e)},
                status_code=500
            )


@dev_api_router.post("/kill-session")
async def kill_session(
    req: Request,
    user: dict = Depends(get_current_user)
):
    """🔒 Force kill a terminal session - requires authentication"""
    # Only works on Mac (local execution)
    if settings.K_SERVICE is not None:
        return JSONResponse(
            content={"error": "Kill session only works on local Mac"},
            status_code=400
        )

    try:
        body = await req.json()
        session_id = body.get("session_id", "user_main_session")

        logger.debug(f"Force killing session '{session_id}'")
        close_persistent_session(session_id)

        return JSONResponse(content={"success": True, "session_id": session_id})
    except Exception as e:
        logger.error(f"Failed to kill session: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)
