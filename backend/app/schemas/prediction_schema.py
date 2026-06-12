"""Prediction schemas — placeholder."""
from typing import Optional
from pydantic import BaseModel


class PredictRequest(BaseModel):
    company: Optional[str] = None
    opportunity_type: Optional[str] = None
    product: Optional[str] = None
    price: Optional[float] = None
    user_count: Optional[int] = None
    sector: Optional[str] = None
    opportunity_source: Optional[str] = None
    competition: Optional[str] = None
    partner: Optional[str] = None
    offer_date: Optional[str] = None
    estimated_project_end_quarter: Optional[str] = None


class PredictResponse(BaseModel):
    win_probability: float
    win_probability_percent: str


class SensitivityPoint(BaseModel):
    price: float
    win_probability: float


class SensitivityResponse(BaseModel):
    points: list[SensitivityPoint]
