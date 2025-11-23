"""
Security module for Dev Dashboard
Handles authentication, JWT tokens, 2FA, and rate limiting
"""

from datetime import datetime, timedelta
from typing import Optional
import os
import bcrypt
from jose import JWTError, jwt
import pyotp
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from core.config import settings
import threading
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ================================
# Configuration
# ================================

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS

DASHBOARD_USERNAME = settings.DASHBOARD_USERNAME
DASHBOARD_PASSWORD_HASH = settings.DASHBOARD_PASSWORD_HASH
TOTP_SECRET = settings.TOTP_SECRET

MAX_LOGIN_ATTEMPTS = settings.MAX_LOGIN_ATTEMPTS
LOCKOUT_DURATION_MINUTES = settings.LOCKOUT_DURATION_MINUTES

# HTTP Bearer token authentication
security = HTTPBearer()

# ================================
# Rate Limiting & Lockout
# ================================

class RateLimiter:
    """Manages login attempts and account lockouts."""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(RateLimiter, cls).__new__(cls)
                cls._instance._login_attempts = {}  # {username: {"count": int, "locked_until": datetime}}
        return cls._instance

    def is_account_locked(self, username: str) -> bool:
        """Check if account is locked due to failed login attempts"""
        with self._lock:
            if username not in self._login_attempts:
                return False

            attempt_data = self._login_attempts[username]

            # Check if lockout has expired
            if "locked_until" in attempt_data:
                if datetime.now() < attempt_data["locked_until"]:
                    return True
                else:
                    # Lockout expired, reset
                    self._login_attempts[username] = {"count": 0}
                    return False
            return False

    def get_lockout_remaining_time(self, username: str) -> Optional[int]:
        """Returns remaining lockout time in minutes, or None if not locked."""
        with self._lock:
            if username not in self._login_attempts:
                return None
            attempt_data = self._login_attempts[username]
            if "locked_until" in attempt_data and datetime.now() < attempt_data["locked_until"]:
                remaining_time = attempt_data["locked_until"] - datetime.now()
                return int(remaining_time.total_seconds() / 60)
            return None

    def record_failed_login(self, username: str):
        """Record failed login attempt and lock account if threshold exceeded"""
        with self._lock:
            if username not in self._login_attempts:
                self._login_attempts[username] = {"count": 0}

            self._login_attempts[username]["count"] += 1

            if self._login_attempts[username]["count"] >= settings.MAX_LOGIN_ATTEMPTS:
                lockout_until = datetime.now() + timedelta(minutes=settings.LOCKOUT_DURATION_MINUTES)
                self._login_attempts[username]["locked_until"] = lockout_until
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Account locked due to too many failed attempts. Try again in {settings.LOCKOUT_DURATION_MINUTES} minutes."
                )

    def reset_login_attempts(self, username: str):
        """Reset login attempts after successful login"""
        with self._lock:
            if username in self._login_attempts:
                self._login_attempts[username] = {"count": 0}

rate_limiter = RateLimiter() # Instantiate the singleton


# ================================
# Password Hashing
# ================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash using bcrypt directly"""
    try:
        password_bytes = plain_password.encode('utf-8')
        hash_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hash_bytes)
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def get_password_hash(password: str) -> str:
    """Hash password using bcrypt directly"""
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        # Truncate to 72 bytes as required by bcrypt
        password_bytes = password_bytes[:72]
    salt = bcrypt.gensalt()
    hash_bytes = bcrypt.hashpw(password_bytes, salt)
    return hash_bytes.decode('utf-8')


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password meets security requirements
    Returns: (is_valid, error_message)
    """
    if len(password) < 16:
        return False, "Password must be at least 16 characters long"

    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)

    if not (has_upper and has_lower and has_digit and has_special):
        return False, "Password must contain uppercase, lowercase, numbers, and special characters"

    return True, ""


# ================================
# TOTP 2FA
# ================================

def verify_totp(token: str) -> bool:
    """Verify TOTP 2FA token"""
    if not TOTP_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="2FA not configured. Set TOTP_SECRET in .env"
        )

    totp = pyotp.TOTP(TOTP_SECRET)
    return totp.verify(token, valid_window=1)  # Allow 1 time step tolerance


def get_totp_provisioning_uri() -> str:
    """
    Get TOTP provisioning URI for QR code generation
    Use this to set up Google Authenticator
    """
    if not settings.TOTP_SECRET:
        raise ValueError("TOTP_SECRET not configured")

    totp = pyotp.TOTP(settings.TOTP_SECRET)
    return totp.provisioning_uri(
        name=settings.DASHBOARD_USERNAME,
        issuer_name="Dev Dashboard"
    )


# ================================
# JWT Token Management
# ================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token (longer expiration)"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> dict:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ================================
# Authentication Functions
# ================================

def authenticate_user(username: str = None, password: str = None, totp_token: str = None) -> bool:
    """
    Authenticate user - supports two modes:
    1. Cloud/Production: 2FA only (username/password optional, only TOTP required)
    2. Local: Skip auth entirely (handled at route level)

    Returns True if credentials are valid
    """
    # For single-user systems, just validate 2FA code
    if totp_token:
        logger.info(f"Authenticating with 2FA code...")

        # Validate TOTP 2FA token
        if not verify_totp(totp_token):
            logger.warning(f"Authentication failed: Incorrect TOTP code.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect 2FA code"
            )
        logger.info(f"2FA validation passed.")
        logger.info(f"Authentication successful")
        return True

    # Legacy support for username/password auth (if someone has it configured)
    if username and password:
        logger.info(f"Attempting legacy authentication for user: {username}")

        # Check if account is locked
        if rate_limiter.is_account_locked(username):
            remaining_minutes = rate_limiter.get_lockout_remaining_time(username)
            logger.warning(f"Authentication failed for {username}: Account is locked.")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Account locked. Try again in {remaining_minutes} minutes."
            )

        # Validate username
        if settings.DASHBOARD_USERNAME and username != settings.DASHBOARD_USERNAME:
            logger.warning(f"Authentication failed for {username}: Incorrect username.")
            rate_limiter.record_failed_login(username)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect credentials"
            )

        # Validate password
        if settings.DASHBOARD_PASSWORD_HASH and not verify_password(password, settings.DASHBOARD_PASSWORD_HASH):
            logger.warning(f"Authentication failed for {username}: Incorrect password.")
            rate_limiter.record_failed_login(username)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect credentials"
            )

        logger.info(f"Legacy authentication successful for user: {username}")
        rate_limiter.reset_login_attempts(username)
        return True

    # No valid credentials provided
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No valid credentials provided"
    )


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Dependency to validate JWT token and get current user
    Use this in protected routes: user = Depends(get_current_user)
    """
    token = credentials.credentials
    payload = verify_token(token)

    # Check token type
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )

    username = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    return {"username": username}


async def get_session_user(request: Request) -> dict:
    """
    Dependency to validate user via multiple auth methods (cross-domain compatible)

    Checks in order:
    1. Session cookie (for same-domain access)
    2. Authorization header (for API/cross-domain access)
    3. Query parameter 'tkn' (for redirect-based access)

    Use this for browser-based routes that need flexible authentication
    (e.g., code-server proxy routes accessed via Tailscale)
    """
    token = None

    # Try session cookie first (same-domain)
    token = request.cookies.get("session_token")

    # Try Authorization header second (cross-domain API)
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")

    # Try query parameter third (for redirects/iframes)
    if not token:
        token = request.query_params.get("tkn")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Please login first.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify token
    try:
        payload = verify_token(token)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {str(e)}"
        )

    # Check token type
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )

    username = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    return {"username": username}


# ================================
# Setup Utilities
# ================================

def generate_setup_info() -> dict:
    """
    Generate setup information for first-time configuration
    Returns QR code URI and other setup data
    """
    if not TOTP_SECRET:
        raise ValueError("TOTP_SECRET not set. Generate one with: python -c 'import pyotp; print(pyotp.random_base32())'")

    return {
        "totp_secret": TOTP_SECRET,
        "totp_uri": get_totp_provisioning_uri(),
        "username": DASHBOARD_USERNAME,
    }


def hash_password_for_env(password: str) -> str:
    """
    Helper function to generate password hash for .env file
    Usage: python -c "from core.security import hash_password_for_env; print(hash_password_for_env('your_password'))"
    """
    is_valid, error_msg = validate_password_strength(password)
    if not is_valid:
        raise ValueError(f"Password not strong enough: {error_msg}")

    return get_password_hash(password)


# ================================
# Startup Validation
# ================================

def validate_security_config():
    """Validate security configuration on startup"""
    import os

    # Check if running in Cloud Run
    is_cloud_run = settings.K_SERVICE is not None

    errors = []
    warnings = []

    if settings.SECRET_KEY == "change-this-immediately":
        errors.append("SECRET_KEY not set in .env - Generate with: openssl rand -hex 32")

    # For cloud deployment, require TOTP
    if is_cloud_run and not settings.TOTP_SECRET:
        errors.append("TOTP_SECRET not set in .env - Generate with: python -c 'import pyotp; print(pyotp.random_base32())'")

    # Password is optional (for single-user 2FA-only mode)
    if not settings.DASHBOARD_PASSWORD_HASH and not is_cloud_run:
        warnings.append("DASHBOARD_PASSWORD_HASH not set - using 2FA-only mode")

    # For local development, TOTP is optional
    if not is_cloud_run and not settings.TOTP_SECRET:
        warnings.append("TOTP_SECRET not set - authentication disabled for local development")

    if errors:
        logger.error("SECURITY CONFIGURATION ERRORS:")
        for error in errors:
            logger.error(f"  - {error}")
        logger.info("Run: python setup_security.py")
        raise ValueError("Security configuration incomplete")

    if warnings:
        logger.warning("SECURITY CONFIGURATION WARNINGS:")
        for warning in warnings:
            logger.warning(f"  - {warning}")

    if is_cloud_run:
        logger.info("Security configuration validated (Cloud Run - 2FA enabled)")
    else:
        logger.info("Security configuration validated (Local - development mode)")
