from pydantic_settings import BaseSettings
from typing import List, Optional
from functools import lru_cache
from pathlib import Path

# Get the project root directory (where .env should be)
PROJECT_ROOT = Path(__file__).parent.parent


class Settings(BaseSettings):
    # Application
    app_name: str = "FastAPI Application"
    app_version: str = "1.0.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database
    database_url: str
    database_test_url: Optional[str] = None
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # CORS
    cors_origins: List[str] = ["*"]
    
    # Logging
    log_level: str = "INFO"
    
    # External APIs
    external_api_base_url: Optional[str] = None
    external_api_key: Optional[str] = None
    
    # Rate limiting
    rate_limit_requests_per_minute: int = 60
    
    # Microsoft Auth
    microsoft_tenant_id: Optional[str] = None
    microsoft_client_id: Optional[str] = None
    microsoft_audience: Optional[str] = None

    class Config:
        env_file = PROJECT_ROOT / ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
