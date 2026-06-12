"""Auth schemas — placeholder."""
from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str


class MFAVerifyRequest(BaseModel):
    email: str
    code: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
