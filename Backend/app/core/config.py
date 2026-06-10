from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    APP_NAME: str = "ecommerce-api"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    API_DOCS_ENABLED: bool = True
    API_PREFIX: str = "/api/v1"
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    FILE_BASE_URL: str = ""
    EXPORT_INLINE_THRESHOLD: int = 100
    EXPORT_DIR: str = "exports"

    DATABASE_URL: str

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14
    # Local-mode convenience: keep users logged in for a very long time and disable rate limits.
    # This is automatically ignored in production.
    LOCAL_PERSISTENT_LOGIN: bool = True
    LOCAL_ACCESS_TOKEN_EXPIRE_MINUTES: int = 5256000  # 10 years
    LOCAL_REFRESH_TOKEN_EXPIRE_DAYS: int = 3650  # 10 years
    JWT_ISSUER: str = "e-comerce-backend"
    JWT_AUDIENCE: str = ""

    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    CACHE_ENABLED: bool = True
    CACHE_TTL_SECONDS: int = 300
    CELERY_TASK_SOFT_TIME_LIMIT: int = 120
    CELERY_TASK_TIME_LIMIT: int = 180
    CELERY_TASK_MAX_RETRIES: int = 3
    CELERY_TASK_DEFAULT_RETRY_DELAY: int = 30
    INVOICE_PDF_DIR: str = "uploads/invoices"
    # When true, generate PDF during checkout response (slower). When false, Celery + GET /pdf only.
    INVOICE_PDF_SYNC: bool = True
    INVOICE_PRINT_ENABLED: bool = False
    INVOICE_PRINT_WEBHOOK_URL: str = ""

    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_LOGIN_PER_MINUTE: int = 20
    RATE_LIMIT_CHECKOUT_PER_MINUTE: int = 60

    TELEGRAM_BOT_TOKEN: str | None = None
    TELEGRAM_CHAT_ID: str | None = None
    TELEGRAM_NOTIFY_ENABLED: bool = False
    TELEGRAM_REPORT_ENABLED: bool = False
    TELEGRAM_DAILY_SALES_SUMMARY_ENABLED: bool = True
    TELEGRAM_BACKUP_ALERT_ENABLED: bool = True
    TELEGRAM_WEBHOOK_SECRET: str | None = None
    # Cambodia local time (Asia/Phnom_Penh) — Celery Beat uses SCHEDULER_TIMEZONE.
    DAILY_SALES_SUMMARY_TIME: str = "19:05"
    DAILY_SALES_WINDOW_START: str = "07:00"
    DAILY_SALES_WINDOW_END: str = "19:00"

    LOW_STOCK_ALERT_ENABLED: bool = False
    LOW_STOCK_THRESHOLD: int = 10

    GOOGLE_SHEET_ID: str | None = None
    GOOGLE_SERVICE_ACCOUNT_FILE: str | None = None
    GOOGLE_BACKUP_ENABLED: bool = False
    GOOGLE_BACKUP_TIME: str = "23:59"

    SCHEDULER_ENABLED: bool = True
    SCHEDULER_TIMEZONE: str = "Asia/Phnom_Penh"
    # Set to match root .env BACKEND_REPLICAS when API is scaled behind nginx.
    BACKEND_REPLICAS: int = 1

    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = False

    model_config = SettingsConfigDict(
        env_file=str(_BACKEND_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Backward-compatible accessors used by existing code.
    @property
    def app_name(self) -> str:
        return self.APP_NAME

    @property
    def api_prefix(self) -> str:
        return self.API_PREFIX

    @property
    def api_docs_enabled(self) -> bool:
        return self.API_DOCS_ENABLED

    @property
    def cors_origins(self) -> str:
        return self.CORS_ORIGINS

    @property
    def file_base_url(self) -> str:
        return self.FILE_BASE_URL

    @property
    def export_inline_threshold(self) -> int:
        return self.EXPORT_INLINE_THRESHOLD

    @property
    def export_dir(self) -> str:
        return self.EXPORT_DIR

    @property
    def secret_key(self) -> str:
        return self.JWT_SECRET_KEY

    @property
    def access_token_expire_minutes(self) -> int:
        if self.LOCAL_PERSISTENT_LOGIN and not self.is_production:
            return self.LOCAL_ACCESS_TOKEN_EXPIRE_MINUTES
        return self.ACCESS_TOKEN_EXPIRE_MINUTES

    @property
    def refresh_token_expire_days(self) -> int:
        if self.LOCAL_PERSISTENT_LOGIN and not self.is_production:
            return self.LOCAL_REFRESH_TOKEN_EXPIRE_DAYS
        return self.REFRESH_TOKEN_EXPIRE_DAYS

    @property
    def jwt_issuer(self) -> str:
        return self.JWT_ISSUER

    @property
    def jwt_audience(self) -> str:
        return self.JWT_AUDIENCE

    @property
    def database_url(self) -> str:
        return self.DATABASE_URL

    @property
    def redis_url(self) -> str:
        return self.REDIS_URL

    @property
    def celery_broker_url(self) -> str:
        return self.CELERY_BROKER_URL

    @property
    def celery_result_backend(self) -> str:
        return self.CELERY_RESULT_BACKEND

    @property
    def cache_enabled(self) -> bool:
        return self.CACHE_ENABLED

    @property
    def cache_ttl_seconds(self) -> int:
        return self.CACHE_TTL_SECONDS

    @property
    def invoice_pdf_dir(self) -> str:
        return self.INVOICE_PDF_DIR

    @property
    def invoice_print_enabled(self) -> bool:
        return self.INVOICE_PRINT_ENABLED

    @property
    def invoice_print_webhook_url(self) -> str:
        return (self.INVOICE_PRINT_WEBHOOK_URL or "").strip()

    @property
    def invoice_pdf_sync(self) -> bool:
        return self.INVOICE_PDF_SYNC

    @property
    def rate_limit_enabled(self) -> bool:
        if self.LOCAL_PERSISTENT_LOGIN and not self.is_production:
            return False
        return self.RATE_LIMIT_ENABLED

    @property
    def rate_limit_login_per_minute(self) -> int:
        return self.RATE_LIMIT_LOGIN_PER_MINUTE

    @property
    def rate_limit_checkout_per_minute(self) -> int:
        return self.RATE_LIMIT_CHECKOUT_PER_MINUTE

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() == "production"

    @property
    def telegram_bot_token(self) -> str | None:
        return self.TELEGRAM_BOT_TOKEN

    @property
    def telegram_chat_id(self) -> str | None:
        return self.TELEGRAM_CHAT_ID

    @property
    def telegram_notify_enabled(self) -> bool:
        return self.TELEGRAM_NOTIFY_ENABLED

    @property
    def telegram_daily_sales_summary_enabled(self) -> bool:
        return bool(
            self.TELEGRAM_DAILY_SALES_SUMMARY_ENABLED
            and self.telegram_notify_enabled
            and (self.telegram_chat_id or "").strip()
            and (self.telegram_bot_token or "").strip()
        )

    @property
    def telegram_report_enabled(self) -> bool:
        return self.TELEGRAM_REPORT_ENABLED

    @property
    def telegram_webhook_secret(self) -> str | None:
        return self.TELEGRAM_WEBHOOK_SECRET

    @property
    def google_sheet_id(self) -> str | None:
        return self.GOOGLE_SHEET_ID

    @property
    def google_service_account_file(self) -> str | None:
        return self.GOOGLE_SERVICE_ACCOUNT_FILE

    @property
    def google_backup_enabled(self) -> bool:
        return self.GOOGLE_BACKUP_ENABLED

    @property
    def google_backup_time(self) -> str:
        return self.GOOGLE_BACKUP_TIME

    @property
    def scheduler_enabled(self) -> bool:
        return self.SCHEDULER_ENABLED

    @property
    def scheduler_timezone(self) -> str:
        return self.SCHEDULER_TIMEZONE

    @property
    def backend_replicas(self) -> int:
        return max(1, int(self.BACKEND_REPLICAS))

    @property
    def log_level(self) -> str:
        return self.LOG_LEVEL

    @property
    def log_json(self) -> bool:
        return self.LOG_JSON


settings = Settings()
