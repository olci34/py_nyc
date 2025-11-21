import os
from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


def _get_env_file() -> str:
    """Determine which .env file to load based on ENV variable."""
    env = os.getenv("ENV", "development")

    # Production uses .env, others use .env.{environment}
    if env == "production":
        env_file = ".env"
    else:
        env_file = f".env.{env}"

    print(f"[Config] ENV={env}, loading from: {env_file}")
    return env_file


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Note: server.py handles loading the correct .env file based on ENV.
    This class reads from os.environ which has already been populated.

    Priority order:
    1. Environment variables (os.environ) - loaded by server.py
    2. Default values defined below
    """

    model_config = SettingsConfigDict(
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )

    # MongoDB
    mongodb_uri: str
    mongodb_db_name: str

    # NYC Open Data
    nyc_open_data_app_token: str

    # JWT Authentication
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Cloudinary
    cloudinary_url: str
    cloudinary_cloud_name: str
    cloudinary_preset_name: str
    cloudinary_api_key: str
    cloudinary_api_secret: str
    cloudinary_env: str  # 'dev', 'test', or 'prod'

    # CORS - Allowed origins (comma-separated list)
    cors_origins: str

    # Stripe
    stripe_secret_key: str
    stripe_publishable_key: str
    stripe_webhook_secret: str
    stripe_listing_price_id: str  # Stripe Price ID (e.g., price_1234abcd...)

    # Resend (Email Service)
    resend_api_key: str
    resend_from_email: str = "noreply@example.com"
    resend_from_name: str = "TLC App"
    resend_template_waitlist: str = "waitlist_en"
    resend_template_password_reset: str = "pwdreset_en"

    def get_cors_origins_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance. Only created once per application lifecycle."""
    settings = Settings()
    print(f"[Config] Settings loaded - DB: {settings.mongodb_db_name}, Cloudinary: {settings.cloudinary_env}")
    return settings
