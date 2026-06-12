"""Price sensitivity router — uses the model trained by POST /train."""
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app import state

router = APIRouter()


class SensitivityRequest(BaseModel):
    offer: Dict[str, Any]
    steps: int = 60


@router.post("/price-sensitivity")
def price_sensitivity(req: SensitivityRequest):
    from app.services import ml_engine  # lazy: notebook must already be loaded by /train

    import numpy as np

    ws = state.get()
    pipeline = ws.get("pipeline")

    if pipeline is None:
        raise HTTPException(
            status_code=400,
            detail="No trained model. Upload a file and call POST /train first.",
        )

    base_scenario     = ws["base_scenario"]
    selected_features = ws["selected_features"]
    price_col         = ws["price_col"]
    price_range       = ws["price_range"]
    eng_cols          = ws["engineered_columns"]

    try:
        scenario = ml_engine.build_prediction_scenario(
            user_inputs=req.offer,
            selected_features=selected_features,
            base_scenario=base_scenario,
            engineered_columns=eng_cols,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not process inputs: {exc}")

    price_min, price_max = price_range
    steps      = max(10, min(req.steps, 200))
    price_grid = np.linspace(price_min, price_max, steps)

    points = []
    for price in price_grid:
        prob = ml_engine.predict_win_probability_for_price(
            model=pipeline,
            scenario=scenario,
            selected_features=selected_features,
            price_col=price_col,
            input_price=float(price),
        )
        points.append({
            "price":           round(float(price), 2),
            "win_probability": round(float(prob), 4),
        })

    return {
        "price_col":   price_col,
        "price_range": {"min": price_min, "max": price_max},
        "points":      points,
    }
