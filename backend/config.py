import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    PROJECT_NAME: str = "AI Swarm Platform API"
    VERSION: str = "1.0.0"
    
    # Database configuration (defaults to SQLite fallback for local development)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./swarm.db")
    
    # JWT Auth configuration
    JWT_SECRET: str = os.getenv("JWT_SECRET", "super_secret_jwt_key_change_in_production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    
    # Hugging Face Token (Phase 1)
    HF_TOKEN: str = os.getenv("HF_TOKEN", "")

settings = Settings()
