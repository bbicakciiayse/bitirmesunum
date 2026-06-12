import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, payment, upload, train, predict, sensitivity, dashboard

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

# Allow both localhost and 127.0.0.1 variants so the browser doesn't block
# health-check or upload requests regardless of which loopback hostname Vite used.
_cors_origins = list({
    FRONTEND_ORIGIN,
    FRONTEND_ORIGIN.replace("localhost", "127.0.0.1"),
    FRONTEND_ORIGIN.replace("127.0.0.1", "localhost"),
})

app = FastAPI(
    title="Pricing Intelligence API",
    version="0.1.0",
    description="B2B sales win-probability and pricing intelligence backend.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,        prefix="/auth",       tags=["Auth"])
app.include_router(payment.router,     prefix="/payment",    tags=["Payment"])
app.include_router(upload.router,                            tags=["Data"])
app.include_router(train.router,                             tags=["Training"])
app.include_router(predict.router,                           tags=["Prediction"])
app.include_router(sensitivity.router,                       tags=["Sensitivity"])
app.include_router(dashboard.router,                         tags=["Dashboard"])


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}
