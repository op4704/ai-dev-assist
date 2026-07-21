from pydantic import BaseModel, Field


class IndexResponse(BaseModel):
    files_processed: int
    files_skipped: int
    chunks_created: int
    vectors_embedded: int
    model_config = {"from_attributes": True}


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Question about the repository")
    session_id: int | None = Field(default=None, description="Existing chat session to continue, or omit to start a new one")


class ChatResponse(BaseModel):
    session_id: int
    answer: str
    citations: list[str]
    model_config = {"from_attributes": True}