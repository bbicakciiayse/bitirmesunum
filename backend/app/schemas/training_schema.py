"""Training schemas — placeholder."""
from pydantic import BaseModel


class TrainRequest(BaseModel):
    target_column: str
    drop_leakage: bool = True


class ModelMetricsResponse(BaseModel):
    roc_auc: float
    accuracy: float
    precision: float
    recall: float
    f1_score: float
