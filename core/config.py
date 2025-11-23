from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "David Lybeck"
    PROJECT_VERSION: str = "1.0.0"

    # Core application settings
    K_SERVICE: Optional[str] = None # Set by Cloud Run, if None, assume local
    AGOR_URL: str = "http://localhost:3030" # Default for local
    HTTPS: bool = False # Used to determine if the application is running under HTTPS
    MAC_SERVER_IP: str = "100.84.184.84"
    MAC_SERVER_PORT: int = 8888
    SOCKS5_PROXY: str = "socks5://localhost:1055"
    SOCKS5_PORT: int = 1055

    # Authentication & Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    DASHBOARD_USERNAME: str = "admin"
    DASHBOARD_PASSWORD_HASH: Optional[str] = None  # Optional - supports 2FA-only mode
    TOTP_SECRET: str
    ANTHROPIC_API_KEY: Optional[str] = None  # Not currently used, but kept for future features

    MAX_LOGIN_ATTEMPTS: int = 3
    LOCKOUT_DURATION_MINUTES: int = 15
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    MAX_DEVICES_PER_USER: int = 3

    # Tailscale Integration (for Cloud Run)
    TAILSCALE_OAUTH_CLIENT_ID: Optional[str] = None
    TAILSCALE_OAUTH_CLIENT_SECRET: Optional[str] = None

settings = Settings()
