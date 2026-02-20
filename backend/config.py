from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

# Default: <project_root>/searchAgent — works on any machine without env override
_DEFAULT_DATA_DIR = str(Path(__file__).parent.parent / "searchAgent")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="backend/.env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    anthropic_api_key: str
    openai_api_key: str
    pinecone_api_key: str
    pinecone_index_name: str = "search-agent-index"
    pinecone_environment: str = "us-east-1-aws"

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 8

    demo_password: str = "demo1234"

    data_dir: str = _DEFAULT_DATA_DIR
    model: str = "gpt-4o-mini"                # provider inferred from name prefix
    google_api_key: str = ""                  # optional — only needed for gemini-* models
    embedding_model: str = "text-embedding-3-large"
    embedding_dimensions: int = 3072
    pinecone_top_k: int = 6
    similarity_threshold: float = 0.35

    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()
