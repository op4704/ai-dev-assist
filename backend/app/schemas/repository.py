from datetime import datetime
from urllib.parse import urlparse
from pydantic import BaseModel, Field, field_validator
from app.models.repository import RepositoryStatus


class RepositoryImportRequest(BaseModel):
    github_url: str = Field(..., description="Public GitHub URL e.g. https://github.com/owner/repo")

    @field_validator("github_url")
    @classmethod
    def validate_github_url(cls, value: str) -> str:
        cleaned = value.strip().rstrip("/")
        parsed = urlparse(cleaned)
        if parsed.scheme != "https" or parsed.hostname != "github.com":
            raise ValueError("Must be a public GitHub URL: https://github.com/owner/repo")
        parts = [p for p in parsed.path.split("/") if p]
        if len(parts) < 2:
            raise ValueError("URL must include owner and repo name")
        return cleaned


class RepositoryProcessRequest(BaseModel):
    repository_id: int


class RepositoryResponse(BaseModel):
    id: int
    github_url: str
    owner: str
    name: str
    default_branch: str
    status: RepositoryStatus
    total_files: int
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class FileResponse(BaseModel):
    id: int
    path: str
    language: str | None
    size_bytes: int
    model_config = {"from_attributes": True}
