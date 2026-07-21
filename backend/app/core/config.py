from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    app_name: str = "AI Developer Assistant"
    environment: str = "development"
    secret_key: str = "dev-secret-change-me"
    database_url: str = "sqlite+aiosqlite:///./dev.db"
    repo_storage_path: str = "./storage/repositories"
    max_repo_size_mb: int = 200
    rate_limit_import: str = "20/minute"
    allowed_origins: str = "http://localhost:8000"

    # --- Phase 2: RAG settings ---
    GROQ_API_KEY: str | None = None
    jina_api_key: str | None = None
    pinecone_api_key: str | None = None
    pinecone_index_name: str = "ai-dev-assistant"

    groq_model: str = "llama-3.3-70b-versatile"
    jina_model: str = "jina-embeddings-v3"
    embedding_dimension: int = 1024

    chunk_size_tokens: int = 500
    chunk_overlap_tokens: int = 50

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


settings = Settings()