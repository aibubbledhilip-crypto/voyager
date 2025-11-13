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
    llm_temperature: float = 0.0  # 0 for deterministic (prevents hallucination), 0.7 for creative

    # Embedding Configuration
    embedding_provider: Literal["openai", "sentence-transformers"] = "openai"
    embedding_model: str = "text-embedding-3-small"

    # Anti-Hallucination Settings
    enable_answer_validation: bool = True  # Validate answers for hallucination markers
    require_source_citation: bool = True   # Require file citations in answers

    # Vector Store
    chroma_persist_directory: str = "./data/vectorstore"

    # Upload Settings
    max_file_size_mb: int = 100
    upload_dir: str = "./data/uploads"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # AWS Configuration (for Athena)
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"
    athena_output_location: str = ""
    athena_workgroup: str = "primary"

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
