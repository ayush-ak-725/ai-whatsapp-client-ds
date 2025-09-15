"""
Configuration settings for the AI Backend service
"""

import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings"""
    
    # Application settings
    APP_NAME: str = "Bakchod AI WhatsApp - AI Backend"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # Server settings
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    
    # CORS settings
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        env="ALLOWED_ORIGINS"
    )
    
    # LLM API Keys
    OPENAI_API_KEY: str = Field(default="", env="OPENAI_API_KEY")
    GEMINI_API_KEY: str = Field(default="", env="GEMINI_API_KEY")
    ANTHROPIC_API_KEY: str = Field(default="", env="ANTHROPIC_API_KEY")
    HUGGINGFACE_API_KEY: str = Field(default="", env="HUGGINGFACE_API_KEY")
    
    # Pinecone settings
    PINECONE_API_KEY: str = Field(default="", env="PINECONE_API_KEY")
    PINECONE_ENVIRONMENT: str = Field(default="us-east-1", env="PINECONE_ENVIRONMENT")
    PINECONE_INDEX_NAME: str = Field(default="bakchod-ai-whatsapp", env="PINECONE_INDEX_NAME")
    
    # Redis settings (for caching)
    REDIS_URL: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    
    # Conversation settings
    MAX_CONVERSATION_HISTORY: int = Field(default=50, env="MAX_CONVERSATION_HISTORY")
    MAX_RESPONSE_LENGTH: int = Field(default=500, env="MAX_RESPONSE_LENGTH")
    RESPONSE_TIMEOUT: int = Field(default=30, env="RESPONSE_TIMEOUT")
    
    # Character settings
    CHARACTER_EMBEDDING_DIMENSION: int = Field(default=768, env="CHARACTER_EMBEDDING_DIMENSION")
    MAX_CHARACTERS_PER_GROUP: int = Field(default=10, env="MAX_CHARACTERS_PER_GROUP")
    
    # Logging settings
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(default="json", env="LOG_FORMAT")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()


