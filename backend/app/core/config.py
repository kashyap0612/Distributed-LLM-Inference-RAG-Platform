from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_env: str = "local"
    redis_url: str = "redis://localhost:6379/0"
    qdrant_url: str = "http://localhost:6333"
    postgres_dsn: str = "postgresql://postgres:postgres@localhost:5432/rag"
    vllm_small_url: str | None = None
    vllm_large_url: str | None = None
    rate_limit_per_minute: int = 60
    cache_ttl_seconds: int = 3600
    qdrant_collection: str = "documents"

    class Config:
        env_file = ".env"

settings = Settings()
