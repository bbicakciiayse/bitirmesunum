import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, payment, upload, train, predict, sensitivity, dashboard


FRONTEND_ORIGIN = os.getenv(
    "FRONTEND_ORIGIN",
    "https://resilient-unity-production-db61.up.railway.app"
)

app = FastAPI(
    title="Pricing Intelligence API",
    version="0.1.0",
    description="B2B sales win-probability and pricing intelligence backend.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://resilient-unity-production-db61.up.railway.app",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        FRONTEND_ORIGIN,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(payment.router, prefix="/payment", tags=["Payment"])
app.include_router(upload.router, tags=["Data"])
app.include_router(train.router, tags=["Training"])
app.include_router(predict.router, tags=["Prediction"])
app.include_router(sensitivity.router, tags=["Sensitivity"])
app.include_router(dashboard.router, tags=["Dashboard"])


@app.get("/", tags=["Root"])
def root():
    return {"status": "ok", "message": "Winsight backend is running"}


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}
