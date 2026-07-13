import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    NODE_ENV: str = "development"
    DATABASE_URL: str
    REDIS_URL: str
    KAFKA_BOOTSTRAP_SERVERS: str
    JWT_SECRET: str
    
    # AI Configuration
    ENABLE_MOCK_AI: bool = True
    AI_PROVIDER: str = "mock"
    USE_REAL_GEMINI: bool = False
    GEMINI_API_KEY: str = "MOCK_MODE"
    GEMINI_MODEL: str = "gemini-1.5-flash"
    
    # Load from environment variables and fallback to files
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
