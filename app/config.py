from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    bot_token: str
    # Optional secret token Telegram echoes back in the
    # X-Telegram-Bot-Api-Secret-Token header on every webhook call
    webhook_secret: str | None = None
    public_url: str | None = None

    search_url: str  # TODO: base url + configurable params
    poll_interval_seconds: int = 180

    # Persistence (Postgres seen-set, via asyncpg).
    # Overridden in docker-compose to reach the `db` service by name.
    database_url: str = "postgresql://otodom:otodom@localhost:5432/otodom"


settings = Settings()
