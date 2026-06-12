"""Generic response schemas — placeholder."""
from typing import Any, Optional
from pydantic import BaseModel


class MessageResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    detail: str
    code: Optional[str] = None


class DataResponse(BaseModel):
    data: Any
    message: Optional[str] = None
