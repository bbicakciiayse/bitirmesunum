"""Upload schemas — placeholder."""
from typing import Any
from pydantic import BaseModel


class DataPreviewResponse(BaseModel):
    columns: list[str]
    rows: list[dict[str, Any]]
    total_rows: int


class SelectTargetRequest(BaseModel):
    target_column: str
