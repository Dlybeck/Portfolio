from functools import wraps
from fastapi import Request
from fastapi.responses import RedirectResponse

def extract_token(request: Request) -> str | None:
    token = request.cookies.get("session_token")
    if token:
        return token
    
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth.replace("Bearer ", "")
    
    return request.query_params.get("tkn")

def verify_token_valid(token: str) -> bool:
    try:
        from core.security import verify_token
        payload = verify_token(token)
        return payload.get("type") == "access"
    except:
        return False

def require_auth(func):
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        token = extract_token(request)
        if not token:
            return RedirectResponse(url="/dev/login", status_code=302)
        
        if not verify_token_valid(token):
            return RedirectResponse(url="/dev/login", status_code=302)
        
        request.state.token = token
        return await func(request, *args, **kwargs)
    return wrapper
