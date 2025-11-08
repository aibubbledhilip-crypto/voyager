"""
Configuration management for the RAG Data Analysis Tool
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    """Application settings"""

    # LLM Configuration
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    llm_provider: Literal["openai", "anthropic"] = "openai"
    llm_model: str = "gpt-4-turbo-preview"

    # Embedding Configuration
    embedding_provider: Literal["openai", "sentence-transformers"] = "openai"
    embedding_model: str = "text-embedding-3-small"

    # Vector Store
    chroma_persist_directory: str = "./data/vectorstore"

    # Upload Settings
    max_file_size_mb: int = 100
    upload_dir: str = "./data/uploads"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    class Config:
        env_file = ".env"
        case_sensitive = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure directories exist
        Path(self.upload_dir).mkdir(parents=True, exist_ok=True)
        Path(self.chroma_persist_directory).mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
