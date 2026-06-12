"""Upload router — real implementation."""
import io

from fastapi import APIRouter, File, HTTPException, UploadFile

from app import state

router = APIRouter()

_TARGET_HINTS = {"result", "win", "won", "lost", "outcome", "status", "label", "won/lost"}
_PRICE_HINTS  = {"price", "quoted price", "deal price", "offer price", "amount", "value"}


@router.post("/upload-data")
async def upload_data(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided.")

    suffix = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if suffix not in {"csv", "xlsx", "xls"}:
        raise HTTPException(
            status_code=400,
            detail="Only .csv, .xlsx, and .xls files are supported.",
        )

    content = await file.read()

    try:
        import pandas as pd
        from app.services import ml_engine

        if suffix == "csv":
            df = pd.read_csv(io.BytesIO(content))
        else:
            df = pd.read_excel(io.BytesIO(content))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not read file: {exc}")

    if df.empty or len(df.columns) < 2:
        raise HTTPException(status_code=400, detail="File appears empty or has too few columns.")

    df = ml_engine.standardize_column_names(df)

    cols_lower = {str(col).strip().lower(): col for col in df.columns}
    suggested_target = next(
        (original for norm, original in cols_lower.items()
         if any(hint in norm for hint in _TARGET_HINTS)), None,
    )
    suggested_price = next(
        (original for norm, original in cols_lower.items()
         if any(hint in norm for hint in _PRICE_HINTS)), None,
    )

    state.clear()
    state.update(df_raw=df, file_name=file.filename)

    preview = df.head(5).fillna("").astype(str).to_dict(orient="records")

    return {
        "file_name":        file.filename,
        "row_count":        len(df),
        "col_count":        len(df.columns),
        "columns":          list(df.columns),
        "preview":          preview,
        "suggested_target": suggested_target,
        "suggested_price":  suggested_price,
    }
