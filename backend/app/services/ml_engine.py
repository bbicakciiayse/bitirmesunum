"""
ml_engine.py — thin proxy to notebook_runner.

Every model function (feature engineering, training, prediction, feature
selection) is sourced directly from Untitled37.ipynb via notebook_runner.

This module adds only two API-specific helpers that have no notebook
equivalent:
    _AUTO_FEATURES           — mirrors prompt_for_full_scenario's auto_features
    build_prediction_scenario — API adapter for prompt_for_full_scenario

Do NOT add model logic here.  Edit Untitled37.ipynb instead.

Import safety
─────────────
notebook_runner is imported LAZILY inside __getattr__ so that
``import app.main`` never touches notebook_runner, pandas, numpy, or sklearn.
notebook_runner.load() (which exec-s the notebook and imports sklearn) is
only triggered the first time a notebook function is actually *called*
(i.e. when POST /train reaches its first ml_engine.* call).
"""
from __future__ import annotations

from typing import Any, Dict, List


# ── Proxy: forward any attribute access to notebook_runner ────────────────────
# notebook_runner is imported lazily here so the module import stays cheap.
# ml_engine.evaluate_feature_additions(...)  →  notebook fn, loaded on first call.

def __getattr__(name: str) -> Any:
    """Forward attribute access to the notebook namespace (lazy import)."""
    from app.services import notebook_runner  # imported only when a fn is needed
    return notebook_runner.get(name)


# ── API-specific helpers (no notebook equivalent) ─────────────────────────────

# Mirrors the auto_features set inside notebook's prompt_for_full_scenario.
# These features are always derived — they stay at base_scenario (training
# medians/modes) and are never overwritten by user form inputs.
_AUTO_FEATURES: frozenset = frozenset({
    "Price_Log",
    "Price_Per_User",
    "Price_Per_User_Log",
    "Offer_Year",
    "Offer_Month",
    "Offer_Quarter",
    "User_Log",
    "Has_Competition",
    "Competition_Count",
    "Has_Partner",
    "Product_Opportunity_Type",
    "Sector_Source",
    "Project_End_Known",
})


def build_prediction_scenario(
    user_inputs: Dict[str, Any],
    selected_features: List[str],
    base_scenario: Dict[str, Any],
    engineered_columns: List[str],
) -> Dict[str, Any]:
    """
    API adapter for the notebook's prompt_for_full_scenario.

    The notebook interactively prompts the user for raw (non-auto) feature
    values and keeps auto features at base_scenario.  This function does the
    same from a dict of form inputs:

    - Starts from base_scenario (training medians/modes for every feature).
    - For each selected feature NOT in _AUTO_FEATURES: overwrites with the
      user-supplied value, coercing to float when the base value is numeric.
    - Auto features stay at base_scenario; Price_Log / Price_Per_User* are
      recalculated per price by predict_win_probability_for_price().
    """
    scenario = base_scenario.copy()

    if not user_inputs:
        return scenario

    for col in selected_features:
        if col in _AUTO_FEATURES:
            continue                          # keep base_scenario value

        val = user_inputs.get(col)
        if val is None or str(val).strip() == "":
            continue                          # no input → keep base_scenario

        base_val = base_scenario.get(col)
        if isinstance(base_val, (int, float)):
            try:
                scenario[col] = float(str(val).replace(",", "."))
                continue
            except (TypeError, ValueError):
                pass
        scenario[col] = str(val)

    return scenario
