from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    database_url: str

    # DeepSeek — weekly card sync
    deepseek_api_key: str = ""

    # External card data API
    carddata_api_key: str = ""
    carddata_api_url: str = "https://api.carddata.io/v1"

    # App
    environment: str = "production"
    allowed_origins: str = "*"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
