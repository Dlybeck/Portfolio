from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "David Lybeck"
    PROJECT_VERSION: str = "1.0.0"
    # Themes are the production experience. Environments can still opt out
    # explicitly, while THEME_LAB_ENABLED remains the local authoring shortcut.
    THEMES_ENABLED: bool = True
    # Local shortcut for exercising the complete runtime theme experience.
    THEME_LAB_ENABLED: bool = False


settings = Settings()
