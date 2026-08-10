from datetime import datetime
from pydantic import BaseModel


class GeneratedDocResponse(BaseModel):
    id: int
    repository_id: int
    doc_type: str
    content: str
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}