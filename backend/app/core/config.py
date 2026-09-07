from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    # redis_host: str = "localhost"
    redis_host: str = "redis"
    redis_port: int = 6379
    cache_ttl_seconds: int = Field(default=60, ge=1, le=86400)

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    oss_access_key_id: str | None = None
    oss_access_key_secret: str | None = None
    oss_region: str | None = None
    oss_bucket: str | None = None
    oss_endpoint: str | None = None
    oss_domain: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
