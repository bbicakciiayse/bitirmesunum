"""
Training router — matches notebook training logic exactly.

Pipeline (same order as notebook):
  1. map_target + drop invalid rows
  2. drop_leakage_columns  (matches notebook drop_leakage_risk=True)
  3. add_feature_engineering  (FE before fillna — matches notebook)
  4. fillna on object columns after FE
  5. evaluate_feature_additions  → keep only ROC-AUC-improving engineered features
  6. build_final_feature_set  → final_features = raw_cols + kept_engineered
  7. select_lasso_c_by_nested_cv  → CV-optimal C
  8. build_lasso_price_probability_model  → fitted Pipeline + base_scenario
"""
from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app import state

router = APIRouter()

# ── Leakage-risk columns (mirror notebook LEAKAGE_RISK_COLUMNS / LEAKAGE_KEYWORDS) ──
_LEAKAGE_RISK_COLUMNS = {
    "Status", "Final Status", "Outcome",
    "Won Date", "Lost Date", "Close Date", "Closed Date",
    "Decision", "Win Probability", "Win Rate",
}
_LEAKAGE_KEYWORDS = {"result"}


def _drop_leakage_columns(df, target_col: str):
    """Drop columns that would leak the outcome into features (matches notebook)."""
    to_remove = set()
    for col in df.columns:
        if col in _LEAKAGE_RISK_COLUMNS:
            to_remove.add(col)
        norm = str(col).strip().lower().replace("_", " ")
        if (
            any(kw in norm for kw in _LEAKAGE_KEYWORDS)
            and col.lower() != target_col.lower()
        ):
            to_remove.add(col)
    if to_remove:
        df = df.drop(columns=sorted(to_remove), errors="ignore")
    return df


class TrainRequest(BaseModel):
    target_col: str
    price_col: str


@router.post("/train")
def train_model(req: TrainRequest):
    import pandas as pd
    from app.services import ml_engine

    ws = state.get()
    df_raw = ws.get("df_raw")

    if df_raw is None:
        raise HTTPException(status_code=400, detail="No data uploaded. Call POST /upload-data first.")
    if req.target_col not in df_raw.columns:
        raise HTTPException(status_code=400, detail=f"Target column '{req.target_col}' not found.")
    if req.price_col not in df_raw.columns:
        raise HTTPException(status_code=400, detail=f"Price column '{req.price_col}' not found.")

    # ── 1. Map target and drop invalid rows ───────────────────────────────────
    y = ml_engine.map_target(df_raw[req.target_col])
    valid_mask = ~y.isna()
    df_clean   = df_raw.loc[valid_mask].copy()
    y          = y.loc[valid_mask].astype(int).reset_index(drop=True)
    df_clean   = df_clean.reset_index(drop=True)

    if len(y) < 10:
        raise HTTPException(status_code=400, detail=f"Only {len(y)} valid rows found. Need at least 10.")

    X_raw = df_clean.drop(columns=[req.target_col]).copy()

    # ── 2. Drop leakage-risk columns (before FE — matches notebook) ───────────
    X_raw = _drop_leakage_columns(X_raw, req.target_col)

    raw_form_columns = list(X_raw.columns)

    # ── 3. Feature engineering (before fillna — matches notebook) ────────────
    X_eng, eng_cols = ml_engine.add_feature_engineering(X_raw.copy())

    # ── 4. fillna on object columns (after FE — matches notebook) ────────────
    for col in X_eng.select_dtypes(include="object").columns:
        X_eng[col] = X_eng[col].fillna("missing").astype(str)

    # ── 5. Feature selection: keep only engineered features that improve AUC ──
    data_dict = {"X": X_eng, "y": y, "engineered_columns": eng_cols}
    feature_impact_df = ml_engine.evaluate_feature_additions(data_dict)

    # ── 6. Build final feature set (raw_cols + kept_engineered) ──────────────
    final_features, _, _ = ml_engine.build_final_feature_set(data_dict, feature_impact_df)
    selected_features = final_features

    # Guarantee price_col is in selected_features
    price_col_actual = ml_engine.find_column_ignore_case(X_eng.columns, req.price_col)
    if price_col_actual is None:
        raise HTTPException(status_code=400, detail=f"Price column '{req.price_col}' not found after FE.")
    if price_col_actual not in selected_features:
        selected_features = [price_col_actual] + selected_features

    # ── 7. Nested CV to find CV-optimal C (notebook's own function) ─────────
    # Calls train_feature_subset_nested_cv("Selected Features", ...) directly
    # from Untitled37.ipynb — runs all 6 models on the selected feature set so
    # get_representative_best_params can pick the CV-optimal Lasso C.
    lasso_cv_results = ml_engine.train_feature_subset_nested_cv(
        feature_set_name="Selected Features",
        feature_names=selected_features,
        X=X_eng,
        y=y,
    )
    all_subset_results = {"Selected Features": lasso_cv_results}

    # ── 8. Fit final Lasso pipeline with CV-optimal C ─────────────────────────
    pipeline, base_scenario = ml_engine.build_lasso_price_probability_model(
        X=X_eng,
        y=y,
        selected_features=selected_features,
        all_subset_results=all_subset_results,
        price_col=price_col_actual,
    )

    if pipeline is None:
        raise HTTPException(status_code=500, detail="Model training failed.")

    # ── Price range (5th–95th percentile of training prices) ─────────────────
    price_series = pd.to_numeric(X_eng[price_col_actual], errors="coerce").dropna()
    price_min    = float(price_series.quantile(0.05))
    price_max    = float(price_series.quantile(0.95))

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


def _build_schema(X_raw, columns: List[str], price_col: str) -> List[dict]:
    import pandas as pd
    schema = []
    for col in columns:
        col_lower = col.lower()
        dtype     = X_raw[col].dtype
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
            "required": (col.lower() == price_col.lower()),
            "options":  options,
        })
    return schema
