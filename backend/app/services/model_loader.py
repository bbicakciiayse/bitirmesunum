"""
model_loader.py  — PARITY-TESTING / DEBUG TOOL ONLY
=====================================================
NOT used in the live product flow.

The live product flow is:
    POST /upload-data  →  POST /train  →  POST /predict / POST /price-sensitivity

This file is a one-off utility for verifying that the dynamic /train pipeline
produces results identical to the notebook.  To use it:

  1. Run notebook_export_cell.py inside Untitled37.ipynb to produce the five
     artifact files in backend/app/models/.
  2. Call load_static_model() from a test script or a parity-check endpoint
     to load the notebook's exact model into state.
  3. Send the same offer to /predict and compare against the notebook output.
  4. Once parity is confirmed, delete the artifact files from models/.

This module is NEVER called from main.py or any router.

Files expected in the models/ directory (produced by notebook_export_cell.py,
which lives in the project root):

    final_model.joblib      – fitted sklearn Pipeline
    selected_features.json  – ordered feature name list
    base_scenario.json      – training medians/modes
    target_mapping.json     – classes, won_class_index
    model_metadata.json     – C value, price_col, counts

If any file is missing the function returns False silently.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict

# ── Paths ──────────────────────────────────────────────────────────────────────
_MODELS_DIR: Path = Path(__file__).resolve().parent.parent / "models"

_REQUIRED_FILES = [
    "final_model.joblib",
    "selected_features.json",
    "base_scenario.json",
    "target_mapping.json",
    "model_metadata.json",
]


def _models_available() -> bool:
    return all((_MODELS_DIR / f).exists() for f in _REQUIRED_FILES)


def load_static_model() -> bool:
    """
    Load exported model artifacts into app.state.

    Returns True on success, False if any artifact is missing.
    Prints progress to stderr so it appears in uvicorn output.
    """
    if not _models_available():
        missing = [f for f in _REQUIRED_FILES if not (_MODELS_DIR / f).exists()]
        print(
            f"[model_loader] Static model not loaded — missing: {missing}",
            file=sys.stderr,
        )
        return False

    try:
        import joblib
        from app import state

        # ── 1. Pipeline ────────────────────────────────────────────────────────
        pipeline = joblib.load(_MODELS_DIR / "final_model.joblib")
        print(f"[model_loader] Loaded pipeline: {type(pipeline).__name__}", file=sys.stderr)

        # ── 2. Selected features ───────────────────────────────────────────────
        with open(_MODELS_DIR / "selected_features.json") as f:
            selected_features: list = json.load(f)
        print(f"[model_loader] Features ({len(selected_features)}): {selected_features[:5]}…", file=sys.stderr)

        # ── 3. Base scenario ───────────────────────────────────────────────────
        with open(_MODELS_DIR / "base_scenario.json") as f:
            base_scenario: Dict[str, Any] = json.load(f)
        print(f"[model_loader] Base scenario keys ({len(base_scenario)})", file=sys.stderr)

        # ── 4. Target mapping ──────────────────────────────────────────────────
        with open(_MODELS_DIR / "target_mapping.json") as f:
            target_mapping: Dict[str, Any] = json.load(f)

        # ── 5. Model metadata ──────────────────────────────────────────────────
        with open(_MODELS_DIR / "model_metadata.json") as f:
            metadata: Dict[str, Any] = json.load(f)

        price_col: str  = metadata["price_col"]
        target_col: str = metadata.get("target_col", "Result")
        print(f"[model_loader] price_col={price_col!r}  C={metadata['sklearn_params'].get('C')}", file=sys.stderr)

        # ── Engineered columns ─────────────────────────────────────────────────
        # build_prediction_scenario uses _AUTO_FEATURES (hardcoded frozenset) to
        # decide which features to skip, not this list.  An empty list is safe.
        eng_cols: list = []

        # ── Price range ────────────────────────────────────────────────────────
        # Prefer the 5th–95th percentile saved by the export cell.
        # Fall back to a wide estimate around the base-scenario median price.
        if "price_range" in metadata:
            price_min = float(metadata["price_range"]["min"])
            price_max = float(metadata["price_range"]["max"])
        else:
            price_base = float(base_scenario.get(price_col, 0))
            price_min  = round(price_base * 0.1, 2)
            price_max  = round(price_base * 3.0, 2)

        # ── Populate state ─────────────────────────────────────────────────────
        state.update(
            pipeline=pipeline,
            selected_features=selected_features,
            base_scenario=base_scenario,
            price_col=price_col,
            target_col=target_col,
            engineered_columns=eng_cols,
            price_range=(price_min, price_max),
            # schema and raw_form_columns are set by /upload + /train;
            # leave them unset so the form uses /train after upload.
        )

        print(
            f"[model_loader] Static model loaded ✓ — "
            f"{len(selected_features)} features, "
            f"price_col={price_col!r}",
            file=sys.stderr,
        )
        return True

    except Exception as exc:
        print(f"[model_loader] ERROR loading static model: {exc}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return False
