"""Payment schemas — placeholder."""
from pydantic import BaseModel


class CreateCheckoutRequest(BaseModel):
    plan: str       # e.g. "starter", "pro", "enterprise"
    email: str


class ConfirmPaymentRequest(BaseModel):
    session_id: str


class CheckoutResponse(BaseModel):
    checkout_url: str
