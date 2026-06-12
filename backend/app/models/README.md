# backend/app/models/

Place the notebook-exported model artifacts here.

Run the **export cell** inside `Untitled37.ipynb` (see instructions below).
That cell produces these four files — copy them into this directory:

| File | Contents |
|---|---|
| `final_model.joblib` | Fitted sklearn Pipeline (preprocessor → Lasso LR with CV-optimal C) |
| `selected_features.json` | Ordered list of feature names used by the model |
| `base_scenario.json` | Training-data medians/modes for every selected feature |
| `target_mapping.json` | `model.classes_`, `won_class_index`, target label mapping |
| `model_metadata.json` | C value, price_col, feature count, training rows |

Once these files are present the `/predict` and `/price-sensitivity` endpoints
switch automatically to the notebook model (exact parity).
