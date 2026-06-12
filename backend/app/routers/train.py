"""
Training router — fast production path.

Removed expensive operations that made the endpoint unusable on Railway:
  - evaluate_feature_additions   (5-fold CV x every engineered feature)
  - train_feature_subset_nested_cv (6 models x nested grid search)

Replaced with:
  - keep all features (raw + engineered)
  - single 80/20 train/test split for metrics
  - Lasso LogisticRegression with fixed C=1.0 (no grid search)
  - refit on full dataset

Typical wall time: 2-15 seconds instead of 10-30 minutes.
Response shape is identical to the old router.
"""
import logging
import time
from typing import List

import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app import state
from app.services import ml_engine

logger = logging.getLogger(__name__)
router = APIRouter()

_LEAKAGE_RISK_COLUMNS = {
    "Status", "Final Status", "Outcome",
    "Won Date", "Lost Date", "Close Date", "Closed Date",
    "Decision", "Win Probability", "Win Rate",
}
_LEAKAGE_KEYWORDS = {"result"}


def _drop_leakage_columns(df: pd.DataFrame, target_col: str) -> pd.DataFrame:
    to_remove: set = set()
    for col in df.columns:
        if col in _LEAKAGE_RISK_COLUMNS:
            to_remove.add(col)
        norm = str(col).strip().lower().replace("_", " ")
        if any(kw in norm for kw in _LEAKAGE_KEYWORDS) and col.lower() != target_col.lower():
            to_remove.add(col)
    if to_remove:
        df = df.drop(columns=sorted(to_remove), errors="ignore")
    return df


class TrainRequest(BaseModel):
    target_col: str
    price_col: str


@router.post("/train")
def train_model(req: TrainRequest):
    import numpy as np
    from sklearn.metrics import accuracy_score, roc_auc_score
    from sklearn.model_selection import train_test_split

    t0 = time.time()
    logger.info("Train started — target=%r  price=%r", req.target_col, req.price_col)

    ws = state.get()
    df_raw = ws.get("df_raw")

    if df_raw is None:
        raise HTTPException(
            status_code=400,
            detail="No data uploaded. Call POST /upload-data first.",
        )
    if req.target_col not in df_raw.columns:
        raise HTTPException(
            status_code=400,
            detail=f"Target column '{req.target_col}' not found.",
        )
    if req.price_col not in df_raw.columns:
        raise HTTPException(
            status_code=400,
            detail=f"Price column '{req.price_col}' not found.",
        )

    logger.info("Dataframe shape: %s", df_raw.shape)

    # 1. Map target, drop invalid rows
    y = ml_engine.map_target(df_raw[req.target_col])
    valid_mask = ~y.isna()
    df_clean = df_raw.loc[valid_mask].copy()
    y = y.loc[valid_mask].astype(int).reset_index(drop=True)
    df_clean = df_clean.reset_index(drop=True)

    if len(y) < 10:
        raise HTTPException(
            status_code=400,
            detail=f"Only {len(y)} valid rows after target mapping. Need at least 10.",
        )
    if y.nunique() < 2:
        raise HTTPException(
            status_code=400,
            detail=(
                "Target column contains only one class after mapping. "
                "Check that the target column has both Won and Lost values."
            ),
        )

    logger.info("Target mapped: %d valid rows (won=%d lost=%d)",
                len(y), int((y == 1).sum()), int((y == 0).sum()))

    # 2. Drop leakage-risk columns
    X_raw = df_clean.drop(columns=[req.target_col]).copy()
    X_raw = _drop_leakage_columns(X_raw, req.target_col)
    raw_form_columns = list(X_raw.columns)

    # 3. Feature engineering
    logger.info("Feature engineering started")
    X_eng, eng_cols = ml_engine.add_feature_engineering(X_raw.copy())

    # 4. fillna on object columns
    for col in X_eng.select_dtypes(include="object").columns:
        X_eng[col] = X_eng[col].fillna("missing").astype(str)

    # 5. Use all features — skip expensive AUC-based selection
    selected_features = list(X_eng.columns)

    price_col_actual = ml_engine.find_column_ignore_case(X_eng.columns, req.price_col)
    if price_col_actual is None:
        raise HTTPException(
            status_code=400,
            detail=f"Price column '{req.price_col}' not found after feature engineering.",
        )
    if price_col_actual not in selected_features:
        selected_features = [price_col_actual] + selected_features

    logger.info("Features selected: %d", len(selected_features))

    # 6. Fast training: 80/20 split for metrics + refit on full data
    logger.info("Model training started")
    try:
        pipeline = ml_engine.build_fast_pipeline(selected_features, X_eng)

        accuracy = None
        auc = None
        if len(y) >= 20:
            try:
                X_train, X_test, y_train, y_test = train_test_split(
                    X_eng[selected_features], y,
                    test_size=0.2, random_state=42, stratify=y,
                )
                pipeline.fit(X_train, y_train)
                y_pred  = pipeline.predict(X_test)
                y_proba = pipeline.predict_proba(X_test)[:, 1]
                accuracy = float(accuracy_score(y_test, y_pred))
                auc      = float(roc_auc_score(y_test, y_proba))
            except Exception as metric_err:
                logger.warning("Held-out metrics skipped: %s", metric_err)

        # Final model: refit on complete dataset
        pipeline.fit(X_eng[selected_features], y)

    except Exception as exc:
        logger.error("Training failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Model training failed: {exc}")

    elapsed = time.time() - t0
    logger.info(
        "Training complete in %.1fs — rows=%d features=%d accuracy=%s auc=%s",
        elapsed, len(y), len(selected_features),
        f"{accuracy:.3f}" if accuracy is not None else "n/a",
        f"{auc:.3f}" if auc is not None else "n/a",
    )

    # 7. Base scenario (medians / modes for prediction)
    base_scenario: dict = {}
    for col in selected_features:
        if pd.api.types.is_numeric_dtype(X_eng[col]):
            base_scenario[col] = float(pd.to_numeric(X_eng[col], errors="coerce").median())
        else:
            mode = X_eng[col].mode(dropna=True)
            base_scenario[col] = mode.iloc[0] if not mode.empty else "missing"

    # 8. Price range (5th-95th percentile)
    price_series = pd.to_numeric(X_eng[price_col_actual], errors="coerce").dropna()
    price_min = float(price_series.quantile(0.05))
    price_max = float(price_series.quantile(0.95))

    schema = _build_schema(X_raw, raw_form_columns, req.price_col)

    state.update(
        target_col=req.target_col,
        price_col=price_col_actual,
        raw_form_columns=raw_form_columns,
        X_engineered=X_eng,
        y=y,
        selected_features=selected_features,
        pipeline=pipeline,
        base_scenario=base_scenario,
        price_range=(price_min, price_max),
        engineered_columns=eng_cols,
        schema=schema,
    )

    return {
        "status":        "trained",
        "rows_used":     int(len(y)),
        "feature_count": len(selected_features),
        "price_range":   {"min": price_min, "max": price_max},
        "schema":        schema,
    }


def _build_schema(X_raw: pd.DataFrame, columns: List[str], price_col: str) -> List[dict]:
    schema = []
    for col in columns:
        col_lower = col.lower()
        dtype = X_raw[col].dtype
        if any(d in col_lower for d in ("date", "time")):
            field_type = "date"
        elif pd.api.types.is_numeric_dtype(dtype):
            field_type = "number"
        elif X_raw[col].nunique(dropna=True) <= 20:
            field_type = "select"
        else:
            field_type = "text"
        options: List[str] = []
        if field_type == "select":
            options = sorted(
                str(v) for v in X_raw[col].dropna().unique()
                if str(v).lower() not in ("missing", "nan", "")
            )
        schema.append({
            "name":     col,
            "type":     field_type,
            "required": col.lower() == price_col.lower(),
            "options":  options,
        })
    return schema
