
from fastapi import FastAPI

app = FastAPI(
    title="FinStack API",
    description="A Dockerized Fintech Wallet and Transaction Management API",
    version="1.0.0"
)


@app.get("/")
def root():
    return {
        "message": "Welcome to FinStack API",
        "status": "running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "application": "FinStack API"
    }
