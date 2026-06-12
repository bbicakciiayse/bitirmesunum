"""
model_store.py — Loads and caches the notebook-exported model artifacts.

Call load() before reading any of the nb_* module-level values.
available() returns True only after a successful load.

Expected files in backend/app/models/:
    final_model.joblib       – fitted sklearn Pipeline
    selected_features.json   – List[str]
    base_scenario.json       – Dict[str, Any]  (training medians/modes)
    target_mapping.json      – model.classes_, won_class_index
    model_metadata.json      – price_col, C, training rows, etc.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

_MODELS_DIR = Path(__file__).resolve().parent.parent / "models"

# Public state — populated by load()
nb_pipeline:  Any                    = None
nb_features:  Optional[List[str]]    = None
nb_scenario:  Optional[Dict[str, Any]] = None
nb_price_col: str                    = "Price"
nb_won_index: int                    = 1

_loaded: bool = False


def available() -> bool:
    """True iff the notebook model is loaded and ready for predictions."""
    return (
        _loaded
        and nb_pipeline  is not None
        and nb_features  is not None
        and nb_scenario  is not None
    )


def load() -> bool:
    """
    Load all notebook-exported artifacts once; no-op on subsequent calls.
    Returns True on success, False if final_model.joblib is absent.
    """
    global nb_pipeline, nb_features, nb_scenario, nb_price_col, nb_won_index, _loaded

    if _loaded:
        return available()

    model_path    = _MODELS_DIR / "final_model.joblib"
    features_path = _MODELS_DIR / "selected_features.json"
    scenario_path = _MODELS_DIR / "base_scenario.json"
    target_path   = _MODELS_DIR / "target_mapping.json"
    meta_path     = _MODELS_DIR / "model_metadata.json"

    if not model_path.exists():
        print(
            f"[MODEL] final_model.joblib not found at {model_path}.\n"
            "[MODEL] Run the export cell in Untitled37.ipynb and copy the "
            "artifacts to backend/app/models/.",
            file=sys.stderr,
        )
        _loaded = True
        return False

    # ── Load pipeline ─────────────────────────────────────────────────────────
    try:
        import joblib
        nb_pipeline = joblib.load(model_path)
    except Exception as exc:
        print(f"[MODEL] Failed to load final_model.joblib: {exc}", file=sys.stderr)
        _loaded = True
        return False

    # ── Load selected features ────────────────────────────────────────────────
    try:
        if features_path.exists():
            with open(features_path) as f:
                nb_features = json.load(f)
    except Exception as exc:
        print(f"[MODEL] Failed to load selected_features.json: {exc}", file=sys.stderr)

    # ── Load base scenario ────────────────────────────────────────────────────
    try:
        if scenario_path.exists():
            with open(scenario_path) as f:
                nb_scenario = json.load(f)
    except Exception as exc:
        print(f"[MODEL] Failed to load base_scenario.json: {exc}", file=sys.stderr)

    # ── Load target mapping (won class index) ─────────────────────────────────
    try:
        if target_path.exists():
            with open(target_path) as f:
                info = json.load(f)
            nb_won_index = int(info.get("won_class_index", 1))
    except Exception as exc:
        print(f"[MODEL] Failed to load target_mapping.json: {exc}", file=sys.stderr)

    # ── Load price_col from metadata ──────────────────────────────────────────
    try:
        if meta_path.exists():
            with open(meta_path) as f:
                meta = json.load(f)
            nb_price_col = meta.get("price_col", "Price")
    except Exception as exc:
        print(f"[MODEL] Failed to load model_metadata.json: {exc}", file=sys.stderr)

    _loaded = True
    print(
        f"[MODEL] Notebook model loaded. "
        f"Features: {len(nb_features or [])}. "
        f"Price col: {nb_price_col!r}. "
        f"Won index: {nb_won_index}.",
        file=sys.stderr,
    )
    return True
