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
from dotenv import load_dotenv

load_dotenv()

# ================================
# Configuration
# ================================

SECRET_KEY = os.getenv("SECRET_KEY", "change-this-immediately")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "720"))  # 12 hours for long dev sessions
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

DASHBOARD_USERNAME = os.getenv("DASHBOARD_USERNAME", "admin")
DASHBOARD_PASSWORD_HASH = os.getenv("DASHBOARD_PASSWORD_HASH", "")
TOTP_SECRET = os.getenv("TOTP_SECRET", "")

MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", "20"))
LOCKOUT_DURATION_MINUTES = int(os.getenv("LOCKOUT_DURATION_MINUTES", "15"))

# HTTP Bearer token authentication
security = HTTPBearer()

# ================================
# Rate Limiting & Lockout
# ================================

login_attempts = {}  # {username: {"count": int, "locked_until": datetime}}


def is_account_locked(username: str) -> bool:
    """Check if account is locked due to failed login attempts"""
    if username not in login_attempts:
        return False

    attempt_data = login_attempts[username]

    # Check if lockout has expired
    if "locked_until" in attempt_data:
        if datetime.now() < attempt_data["locked_until"]:
            return True
        else:
            # Lockout expired, reset
            login_attempts[username] = {"count": 0}
            return False

    return False


def record_failed_login(username: str):
    """Record failed login attempt and lock account if threshold exceeded"""
    if username not in login_attempts:
        login_attempts[username] = {"count": 0}

    login_attempts[username]["count"] += 1

    if login_attempts[username]["count"] >= MAX_LOGIN_ATTEMPTS:
        lockout_until = datetime.now() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
        login_attempts[username]["locked_until"] = lockout_until
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Account locked due to too many failed attempts. Try again in {LOCKOUT_DURATION_MINUTES} minutes."
        )


def reset_login_attempts(username: str):
    """Reset login attempts after successful login"""
    if username in login_attempts:
        login_attempts[username] = {"count": 0}


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
        print(f"Password verification error: {e}")
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
    if not TOTP_SECRET:
        raise ValueError("TOTP_SECRET not configured")

    totp = pyotp.TOTP(TOTP_SECRET)
    return totp.provisioning_uri(
        name=DASHBOARD_USERNAME,
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

def authenticate_user(username: str, password: str, totp_token: str) -> bool:
    """
    Authenticate user with username, password, and 2FA token
    Returns True if all credentials are valid
    """
    print(f"Attempting to authenticate user: {username}")

    # Check if account is locked
    if is_account_locked(username):
        remaining_time = login_attempts[username]["locked_until"] - datetime.now()
        remaining_minutes = int(remaining_time.total_seconds() / 60)
        print(f"Authentication failed for {username}: Account is locked.")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Account locked. Try again in {remaining_minutes} minutes."
        )

    # Validate username
    if username != DASHBOARD_USERNAME:
        print(f"Authentication failed for {username}: Incorrect username.")
        record_failed_login(username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username, password, or 2FA code"
        )
    print(f"Username validation passed for {username}.")

    # Validate password
    if not DASHBOARD_PASSWORD_HASH:
        print(f"Authentication failed for {username}: Password hash not configured.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Dashboard password not configured. Set DASHBOARD_PASSWORD_HASH in .env"
        )

    if not verify_password(password, DASHBOARD_PASSWORD_HASH):
        print(f"Authentication failed for {username}: Incorrect password.")
        record_failed_login(username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username, password, or 2FA code"
        )
    print(f"Password validation passed for {username}.")

    # Validate TOTP 2FA token
    if not verify_totp(totp_token):
        print(f"Authentication failed for {username}: Incorrect TOTP code.")
        record_failed_login(username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username, password, or 2FA code"
        )
    print(f"TOTP validation passed for {username}.")

    # All credentials valid
    print(f"Authentication successful for user: {username}")
    reset_login_attempts(username)
    return True


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
    errors = []

    if SECRET_KEY == "change-this-immediately":
        errors.append("SECRET_KEY not set in .env - Generate with: openssl rand -hex 32")

    if not DASHBOARD_PASSWORD_HASH:
        errors.append("DASHBOARD_PASSWORD_HASH not set in .env")

    if not TOTP_SECRET:
        errors.append("TOTP_SECRET not set in .env - Generate with: python -c 'import pyotp; print(pyotp.random_base32())'")

    if errors:
        print("\n⚠️  SECURITY CONFIGURATION ERRORS:")
        for error in errors:
            print(f"  - {error}")
        print("\nSee .env.example for configuration template\n")
        raise ValueError("Security configuration incomplete")

    print("✅ Security configuration validated")
