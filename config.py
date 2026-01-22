from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    redis_host: str = "localhost"
    redis_port: int = 6379
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    class Config:
        env_file = ".env"

settings = Settings()