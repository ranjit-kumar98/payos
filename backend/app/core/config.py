import os

class Settings:
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "payos123")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "payos")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "postgres")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")

    REDIS_URL: str = os.getenv("REDIS_URL", "redis://:payos_redis_pass@redis:6379/0")

    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-very-secret-key")

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

settings = Settings()