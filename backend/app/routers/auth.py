"""Auth router — placeholder."""
from fastapi import APIRouter

router = APIRouter()


@router.post("/login")
def login():
    return {"message": "login — not implemented yet"}


@router.post("/verify-mfa")
def verify_mfa():
    return {"message": "verify-mfa — not implemented yet"}
