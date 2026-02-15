"""
Configuration Management Module

This module handles all application configuration using environment variables.
It provides type-safe configuration access using Pydantic Settings.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application Settings
    
    All configuration values are loaded from environment variables (.env file).
    Provides validation and type safety for configuration.
    """
    
    # Groq AI Configuration
    GROQ_API_KEY: str
    GROQ_MODEL: str = "llama-3.3-70b-versatile"  # Default model
    GROQ_TEMPERATURE: float = 0.3  # Lower = more focused
    GROQ_MAX_TOKENS: int = 1024
    
    # Application Configuration
    APP_NAME: str = "Medical Assistant"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Wikidata SPARQL Configuration
    WIKIDATA_ENDPOINT: str = "https://query.wikidata.org/sparql"
    SPARQL_TIMEOUT: int = 30  # seconds
    
    # Server Configuration
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    
    # CORS Configuration
    CORS_ORIGINS: list[str] = ["*"]
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.DEBUG
    
    @property
    def sparql_headers(self) -> dict[str, str]:
        """Get headers for SPARQL requests"""
        return {
            "Accept": "application/sparql-results+json",
            "User-Agent": f"{self.APP_NAME}/{self.APP_VERSION}"
        }


# Global settings instance
def get_settings() -> Settings:
    """
    Get application settings instance
    
    Returns:
        Settings: Validated configuration object
    """
    return Settings()


# Create settings instance
settings = get_settings()