from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: int = 5432
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    LLM_BASE_URL: str
    LLM_API_KEY: str
    LLM_MODEL: str = "unsloth/Qwen3.5-9B"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
