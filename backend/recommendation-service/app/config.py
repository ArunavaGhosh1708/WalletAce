from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Internal service URL for fetching card catalogue
    cards_service_url: str = "http://localhost:8001"

    # Cache
    redis_url: str

    # DeepSeek LLM
    deepseek_api_key: str = ""

    # App
    environment: str = "production"
    allowed_origins: str = "*"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
