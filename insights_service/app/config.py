from pydantic import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Insights Service"
    boa_base_url: str = "http://bank-of-anthos-service"
    cache_ttl_seconds: int = 600

    class Config:
        env_file = ".env"

settings = Settings()

