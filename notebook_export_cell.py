# ============================================================
# PARITY-TEST EXPORT CELL  (debug / validation only)
# ─────────────────────────────────────────────────────────────
# This cell is NOT part of the live product flow.
#
# The live product flow is:
#   User uploads Excel → POST /train trains a fresh model →
#   POST /predict / POST /price-sensitivity use that model.
#
# Use this cell only to verify that the dynamic /train pipeline
# matches the notebook.  Steps:
#   1. Run the notebook main cell to completion.
#   2. Add this as a new cell below and run it once.
#   3. Restart the backend, upload the same Excel, POST /train.
#   4. POST /predict with the same offer and compare results.
#   5. Delete the artifact files from backend/app/models/ when done.
# ============================================================
import json
import joblib
from pathlib import Path

# ── Set the export directory ─────────────────────────────────
# Assumes the notebook is run from the project root
# (the folder that contains backend/).
# Adjust the path if needed.
EXPORT_DIR = Path.cwd() / "backend" / "app" / "models"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)
print(f"Export directory: {EXPORT_DIR.resolve()}")

# ── Rebuild the final Lasso model ────────────────────────────
# Uses the same all_subset_results that were computed by the
# main cell — this gives the CV-optimal C, not the default 1.0.
print("\nBuilding final Lasso model for export …")
export_pipeline, export_base_scenario = build_lasso_price_probability_model(
    X=X,
    y=y,
    selected_features=final_features,
    all_subset_results=all_subset_results,
    price_col=data["price_col"],
)

if export_pipeline is None:
    raise RuntimeError(
        "Model build failed — price_col not found in selected_features.\n"
        "Check that data['price_col'] is in final_features."
    )


# ── Helper: convert numpy scalars to plain Python types ──────
def _to_python(v):
    if hasattr(v, "item"):    # numpy scalar (int64, float64, …)
        return v.item()
    if hasattr(v, "tolist"):  # numpy array
        return v.tolist()
    return v


# ── 1. Save fitted pipeline ───────────────────────────────────
model_path = EXPORT_DIR / "final_model.joblib"
joblib.dump(export_pipeline, model_path)
print(f"Saved: {model_path}")

# ── 2. Save selected features ─────────────────────────────────
features_path = EXPORT_DIR / "selected_features.json"
with open(features_path, "w") as f:
    json.dump(final_features, f, indent=2)
print(f"Saved: {features_path}")

# ── 3. Save base scenario ─────────────────────────────────────
scenario_path = EXPORT_DIR / "base_scenario.json"
serializable_scenario = {k: _to_python(v) for k, v in export_base_scenario.items()}
with open(scenario_path, "w") as f:
    json.dump(serializable_scenario, f, indent=2)
print(f"Saved: {scenario_path}")

# ── 4. Save target mapping + model.classes_ ───────────────────
classes  = export_pipeline.named_steps["classifier"].classes_.tolist()
won_idx  = classes.index(1)   # 1 = Won (from map_target)
target_path = EXPORT_DIR / "target_mapping.json"
with open(target_path, "w") as f:
    json.dump({
        "classes":         classes,
        "won_class_index": won_idx,
        "won_class_value": 1,
        "mapping":         {
            "won": 1, "win": 1, "yes": 1, "1": 1, "true": 1,
            "lost": 0, "loss": 0, "no": 0, "0": 0, "false": 0,
        },
    }, f, indent=2)
print(f"Saved: {target_path}")

# ── 5. Save model metadata (includes price range + target_col) ──
lasso_results = all_subset_results.get("Selected Features", {}).get("Lasso Logistic Regression")
best_params   = get_representative_best_params(lasso_results) if lasso_results else {}

# Price range: 5th–95th percentile of training data (mirrors train.py)
_price_series = pd.to_numeric(X[data["price_col"]], errors="coerce").dropna()
_price_min    = float(_price_series.quantile(0.05))
_price_max    = float(_price_series.quantile(0.95))

meta_path     = EXPORT_DIR / "model_metadata.json"
with open(meta_path, "w") as f:
    json.dump({
        "model_type": "Lasso Logistic Regression",
        "sklearn_params": {
            "penalty":      "l1",
            "solver":       "liblinear",
            "class_weight": "balanced",
            "max_iter":     5000,
            "C":            best_params.get("classifier__C", 1.0),
            "random_state": RANDOM_STATE,
        },
        "price_col":     data["price_col"],
        "target_col":    data.get("target_col", TARGET_COLUMN),
        "feature_count": len(final_features),
        "training_rows": int(len(y)),
        "classes":       classes,
        "won_class_index": won_idx,
        "price_range": {
            "min": _price_min,
            "max": _price_max,
        },
    }, f, indent=2)
print(f"Saved: {meta_path}")


# ── Parity verification ───────────────────────────────────────
print("\n── Export summary ───────────────────────────────────────────")
print(f"model.classes_       = {classes}")
print(f"Won class index      = {won_idx}")
print(f"CV-optimal C         = {best_params.get('classifier__C', 1.0)}")
print(f"price_col            = {data['price_col']!r}")
print(f"Selected features ({len(final_features)}):")
for feat in final_features:
    print(f"  {feat}")

# ── In-notebook parity test (expected ~80.35%) ────────────────
print("\n── Parity test ──────────────────────────────────────────────")
print("Input: Opportunity Type=Renewal, Price=8955, Product=Securify Access,")
print("       User=200, Company=Lentatech, Sector=Defence,")
print("       Opportunity Source=Direct Lead Nurturing, Partner=Cyberwise")
print("Expected: 80.35%")

# Build the test scenario the same way the backend does:
#  - start from base_scenario (training medians/modes)
#  - override only raw (non-auto) features with test values
_AUTO = {
    "Price_Log", "Price_Per_User", "Price_Per_User_Log",
    "Offer_Year", "Offer_Month", "Offer_Quarter",
    "User_Log", "Has_Competition", "Competition_Count",
    "Has_Partner", "Product_Opportunity_Type", "Sector_Source",
    "Project_End_Known",
}
_TEST_INPUTS = {
    "Opportunity Type":    "Renewal",
    "Product":             "Securify Access",
    "Price":               8955,
    "User":                200,
    "Company":             "Lentatech",
    "Sector":              "Defence",
    "Opportunity Source":  "Direct Lead Nurturing",
    "Partner":             "Cyberwise",
    "Competition":         "",
}

test_scenario = export_base_scenario.copy()
for col in final_features:
    if col in _AUTO:
        continue
    val = _TEST_INPUTS.get(col)
    if val is None or str(val).strip() == "":
        continue
    base_val = export_base_scenario.get(col)
    if isinstance(base_val, (int, float)):
        try:
            test_scenario[col] = float(str(val).replace(",", "."))
            continue
        except (TypeError, ValueError):
            pass
    test_scenario[col] = str(val)

test_prob = predict_win_probability_for_price(
    model=export_pipeline,
    scenario=test_scenario,
    selected_features=final_features,
    price_col=data["price_col"],
    input_price=8955.0,
)

print(f"\nNotebook result:  {test_prob * 100:.2f}%")
print(f"Expected:          80.35%")
match = abs(test_prob * 100 - 80.35) < 0.5   # 0.5% tolerance for rounding
print(f"Parity check:      {'PASS ✓' if match else 'FAIL — check inputs or feature list'}")

print("\nExport complete.")
