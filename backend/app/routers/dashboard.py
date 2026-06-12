"""Dashboard router — placeholder."""
from fastapi import APIRouter

router = APIRouter()


@router.post("/save-result")
def save_result():
    return {"message": "save-result — not implemented yet"}


@router.get("/saved-results")
def saved_results():
    return {"message": "saved-results — not implemented yet"}


@router.get("/dashboard-summary")
def dashboard_summary():
    return {"message": "dashboard-summary — not implemented yet"}
