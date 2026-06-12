"""Payment router — placeholder."""
from fastapi import APIRouter

router = APIRouter()


@router.post("/create-checkout")
def create_checkout():
    return {"message": "create-checkout — not implemented yet"}


@router.post("/confirm")
def confirm_payment():
    return {"message": "payment confirm — not implemented yet"}
