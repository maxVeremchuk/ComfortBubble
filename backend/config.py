from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    gemini_api_key: str | None = None
    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    max_upload_bytes: int = 10 * 1024 * 1024
    gemini_model: str = "gemini-3.5-flash"
    home_assistant_url: str = "http://localhost:8123"
    home_assistant_token: str | None = None
    home_assistant_thermostat: str = "climate.living_room_thermostat"
    home_assistant_thermostat_pattern: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def allowed_origins(self) -> list[str]:
        return [
            origin.strip() for origin in self.cors_origins.split(",") if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
