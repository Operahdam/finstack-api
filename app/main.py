
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.routes.transactions import router as transaction_router
from app.database import get_db
from app.routes.wallets import router as wallet_router

app = FastAPI(
    title="FinStack API",
    description="A Dockerized Fintech Wallet and Transaction Management API",
    version="1.0.0",
)

app.include_router(transaction_router)
app.include_router(wallet_router)


@app.get("/")
def root():
    return {
        "message": "Welcome to FinStack API",
        "status": "running",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "application": "FinStack API",
    }


@app.get("/ready")
def readiness_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))

        return {
            "status": "ready",
            "application": "FinStack API",
            "database": "connected",
        }

    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "database": "unavailable",
            },
        ) from exc

