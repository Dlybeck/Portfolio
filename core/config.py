from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "David Lybeck"
    PROJECT_VERSION: str = "1.0.0"
    # Throwaway visual-comparison route state. This is opt-in locally and
    # defaults off so prototype assets and controls cannot appear publicly.
    THEME_PROTOTYPE_ENABLED: bool = False


settings = Settings()
