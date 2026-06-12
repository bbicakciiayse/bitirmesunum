"""Prediction router — uses the model trained by POST /train."""
import sys
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app import state

router = APIRouter()


class PredictRequest(BaseModel):
    offer: Dict[str, Any]


@router.get("/model-input-schema")
def model_input_schema():
    ws = state.get()
    if not state.ready("pipeline"):
        raise HTTPException(status_code=400, detail="No trained model. Call POST /train first.")
    return {"schema": ws.get("schema", []), "price_col": ws.get("price_col", "")}


@router.post("/predict")
def predict(req: PredictRequest):
    from app.services import ml_engine  # lazy: notebook must already be loaded by /train

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

    try:
        input_price = float(scenario.get(price_col, base_scenario.get(price_col, 0)))
    except (TypeError, ValueError):
        input_price = float(base_scenario.get(price_col, 0))

    # ── Debug trace (stderr — does not affect the response) ──────────────────
    print("[PREDICT DEBUG] ── prediction trace ──────────────────────────────", file=sys.stderr)
    print(f"[PREDICT DEBUG] 1. user_inputs:       {req.offer}", file=sys.stderr)
    print(f"[PREDICT DEBUG] 2. selected_features: {selected_features}", file=sys.stderr)
    print(f"[PREDICT DEBUG] 3. price_col:         {price_col}", file=sys.stderr)
    print(f"[PREDICT DEBUG] 4. input_price:       {input_price}", file=sys.stderr)
    print(f"[PREDICT DEBUG] 5. base_scenario:     {base_scenario}", file=sys.stderr)
    print(f"[PREDICT DEBUG] 6. final scenario:    {scenario}", file=sys.stderr)
    print(f"[PREDICT DEBUG] 7. scenario diff (user overrides):", file=sys.stderr)
    for k in selected_features:
        bv = base_scenario.get(k)
        sv = scenario.get(k)
        if bv != sv:
            print(f"[PREDICT DEBUG]       {k}: {bv!r}  →  {sv!r}", file=sys.stderr)

    try:
        win_prob = ml_engine.predict_win_probability_for_price(
            model=pipeline,
            scenario=scenario,
            selected_features=selected_features,
            price_col=price_col,
            input_price=input_price,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Prediction error: {exc}")

    print(
        f"[PREDICT DEBUG] 8. win_probability:   {win_prob:.6f}  ({win_prob * 100:.2f}%)",
        file=sys.stderr,
    )
    print("[PREDICT DEBUG] ─────────────────────────────────────────────────", file=sys.stderr)

    return {
        "predicted_label":     "Won" if win_prob >= 0.5 else "Lost",
        "win_probability":     round(win_prob, 4),
        "probability_percent": round(win_prob * 100, 1),
        "deal_price":          input_price,
        "model_used":          "Lasso Logistic Regression",
    }
