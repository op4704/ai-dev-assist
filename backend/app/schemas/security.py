from datetime import datetime
from pydantic import BaseModel


class ScanResponse(BaseModel):
    files_scanned: int
    files_skipped: int
    total_findings: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    model_config = {"from_attributes": True}


class FindingResponse(BaseModel):
    id: int
    file_id: int
    severity: str
    category: str
    title: str
    description: str
    line_number: int | None
    matched_snippet: str | None
    created_at: datetime
    model_config = {"from_attributes": True}


class FindingWithPathResponse(FindingResponse):
    file_path: str