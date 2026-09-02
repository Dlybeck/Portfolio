from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "David Lybeck"
    PROJECT_VERSION: str = "1.0.0"
    THEMES_ENABLED: bool = False
    THEME_SELECTOR_ENABLED: bool = False
    # Compatibility switch for the current development environment. It turns
    # on both the engine and selector; deployment can enable them separately.
    THEME_LAB_ENABLED: bool = False


settings = Settings()
