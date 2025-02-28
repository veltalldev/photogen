from pydantic_settings import BaseSettings
from typing import List
import secrets
from pathlib import Path

class Settings(BaseSettings):
    # Database
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    
    # Application
    APP_NAME: str
    DEBUG: bool
    LOG_LEVEL: str
    
    # API
    API_VERSION: str
    API_PREFIX: str
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALLOWED_ORIGINS: List[str]
    
    # File Storage
    UPLOAD_DIR: Path
    MAX_UPLOAD_SIZE: int

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Create global settings instance
settings = Settings()

def validate_settings() -> bool:
    """Validate critical settings and directory structure."""
    try:
        # Ensure upload directory exists
        upload_path = Path(settings.UPLOAD_DIR)
        upload_path.mkdir(exist_ok=True)
        
        # Validate database connection string can be formed
        db_url = f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
        
        # Add more validation as needed
        
        return True
    except Exception as e:
        print(f"Settings validation failed: {str(e)}")
        return False 