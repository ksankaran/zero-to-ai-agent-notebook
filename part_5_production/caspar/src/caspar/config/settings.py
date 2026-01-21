# From: Zero to AI Agent, Chapter 20, Section 20.1
# File: src/caspar/config/settings.py

"""
CASPAR Configuration Settings

This module provides centralized configuration management using Pydantic Settings.
All configuration is loaded from environment variables with sensible defaults.
"""

from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


def get_project_root() -> Path:
    """Find the project root directory (where .env lives)."""
    # Start from this file's directory and go up until we find .env or pyproject.toml
    current = Path(__file__).resolve().parent
    
    for parent in [current] + list(current.parents):
        if (parent / ".env").exists() or (parent / "pyproject.toml").exists():
            return parent
    
    # Fallback to current working directory
    return Path.cwd()


# Get path to .env file
PROJECT_ROOT = get_project_root()
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Pydantic Settings v2 configuration
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra env vars
    )
    
    # OpenAI Configuration
    openai_api_key: str = Field(..., description="OpenAI API key")
    default_model: str = Field(
        default="gpt-4o-mini",
        description="Default LLM model for most operations"
    )
    smart_model: str = Field(
        default="gpt-4o",
        description="Smarter model for complex reasoning"
    )
    
    # Database Configuration
    database_url: str = Field(
        default="postgresql://caspar:caspar_secret@localhost:5432/caspar_db",
        description="PostgreSQL connection string"
    )
    
    # Application Settings
    environment: str = Field(
        default="development",
        description="Environment (development, staging, production)"
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    
    # Agent Configuration
    max_conversation_turns: int = Field(
        default=50,
        description="Maximum turns before suggesting human handoff"
    )
    sentiment_threshold: float = Field(
        default=-0.5,
        description="Sentiment score below which to escalate"
    )
    
    # RAG Configuration
    chroma_persist_directory: str = Field(
        default="./chroma_data",
        description="Directory for ChromaDB persistence"
    )
    retrieval_k: int = Field(
        default=4,
        description="Number of documents to retrieve for RAG"
    )
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Using lru_cache ensures we only load settings once,
    improving performance and consistency.
    """
    return Settings()


# Convenience function for quick access
settings = get_settings()
