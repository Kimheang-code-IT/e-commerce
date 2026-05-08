from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Backend project root (contains `.env`, `app.db`, etc.)
_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Application settings. Override via environment variables or `Backend/.env`."""

    app_name: str = "E-Commerce Backend API"
    api_prefix: str = "/api/v1"
    secret_key: str = "change-me-in-env"
    access_token_expire_minutes: int = 1440
    refresh_token_expire_days: int = 14
    jwt_issuer: str = "e-comerce-backend"
    jwt_audience: str = ""
    sqlite_url: str = f"sqlite:///{(_BACKEND_ROOT / 'app.db').as_posix()}"
    export_inline_threshold: int = 100
    export_dir: str = "exports"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    # Absolute origin for building image URLs returned to the SPA (img src on another port).
    file_base_url: str = "http://127.0.0.1:8000"

    # Google Sheets Backup
    google_sheet_id: str | None = None
    google_service_account_file: str = "service-account.json"
    google_backup_enabled: bool = False
    google_backup_time: str = "23:59"  # HH:MM format

    # Telegram Notification
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None
    telegram_notify_enabled: bool = False
    telegram_report_enabled: bool = False
    telegram_webhook_secret: str = "secret-key-123"
    model_config = SettingsConfigDict(
        env_file=str(_BACKEND_ROOT / ".env"),
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )


settings = Settings()
