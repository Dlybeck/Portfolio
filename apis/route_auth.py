"""
Authentication routes for Dev Dashboard
Handles login, logout, token refresh, and 2FA setup
"""

from fastapi import APIRouter, HTTPException, status, Depends, Response
from pydantic import BaseModel
from datetime import timedelta
from core.security import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    verify_token,
    get_current_user,
    generate_setup_info,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


# ================================
# Request/Response Models
# ================================

class LoginRequest(BaseModel):
    username: str
    password: str
    totp_code: str  # 6-digit 2FA code


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshRequest(BaseModel):
    refresh_token: str


class SetupInfoResponse(BaseModel):
    message: str
    totp_uri: str
    username: str


# ================================
# Routes
# ================================

@auth_router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, response: Response):
    """
    Login with username, password, and 2FA code
    Returns JWT access and refresh tokens
    Also sets session cookie for browser-based auth
    """
    # Authenticate user (validates all credentials + 2FA)
    authenticate_user(request.username, request.password, request.totp_code)

    # Create tokens
    access_token = create_access_token(
        data={"sub": request.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = create_refresh_token(data={"sub": request.username})

    # Set session cookie for browser-based authentication
    # This allows redirects and iframe content to stay authenticated
    response.set_cookie(
        key="session_token",
        value=access_token,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,  # Prevent JavaScript access
        secure=True,    # Require HTTPS (self-signed cert is fine)
        samesite="none" # Allow cross-domain cookies (required for Tailscale IP)
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@auth_router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshRequest):
    """
    Refresh access token using refresh token
    """
    # Verify refresh token
    payload = verify_token(request.refresh_token)

    # Check token type
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )

    username = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    # Create new tokens
    access_token = create_access_token(
        data={"sub": username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    new_refresh_token = create_refresh_token(data={"sub": username})

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@auth_router.get("/verify")
async def verify_authentication(user: dict = Depends(get_current_user)):
    """
    Verify current authentication status
    Protected route - requires valid JWT token
    """
    return {
        "authenticated": True,
        "username": user["username"],
        "message": "Token is valid"
    }


@auth_router.post("/logout")
async def logout(user: dict = Depends(get_current_user)):
    """
    Logout user
    Note: Since we're using JWT, actual logout is handled client-side by deleting tokens
    This endpoint is for logging/audit purposes
    """
    return {
        "message": f"User {user['username']} logged out successfully"
    }


@auth_router.get("/setup", response_model=SetupInfoResponse)
async def get_setup_info(user: dict = Depends(get_current_user)):
    """
    Get 2FA setup information (TOTP QR code URI)
    🔒 PROTECTED: Requires authentication
    Use this to reconfigure 2FA for authenticated users
    """
    try:
        setup_info = generate_setup_info()
        return SetupInfoResponse(
            message="Scan this QR code with Google Authenticator",
            totp_uri=setup_info["totp_uri"],
            username=setup_info["username"]
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
