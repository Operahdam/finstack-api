
from decimal import Decimal
from typing import Annotated
from uuid import UUID
from app.models.user import User
from app.routes.auth import get_current_user

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.transaction import (
    MoneyRequest,
    TransferRequest,
    TransactionResponse,
    TransactionList,
)
from app.services.transaction_service import (
    credit_wallet,
    debit_wallet,
    transfer_funds,
    get_wallet_transactions,
)

router = APIRouter(prefix="/transactions", tags=["Transactions"])


def require_idempotency_key(
    key: Annotated[str, Header(alias="Idempotency-Key")],
):
    if not key.strip() or len(key) > 100:
        raise HTTPException(400, detail="Invalid idempotency key")
    return key


@router.post(
    "/wallets/{wallet_id}/credit",
    response_model=TransactionResponse,
)
def credit(
    wallet_id: UUID,
    payload: MoneyRequest,
    db: Session = Depends(get_db),
    key: str = Depends(require_idempotency_key),
    current_user: User = Depends(get_current_user),
):
    return credit_wallet(
        db,
        wallet_id,
        payload.amount,
        key,
        current_user.id,
    )

@router.post(
    "/wallets/{wallet_id}/debit",
    response_model=TransactionResponse,
)
def debit(
    wallet_id: UUID,
    payload: MoneyRequest,
    db: Session = Depends(get_db),
    key: str = Depends(require_idempotency_key),
    current_user: User = Depends(get_current_user),
):
    return debit_wallet(
        db,
        wallet_id,
        payload.amount,
        key,
        current_user.id,
    )
@router.post(
    "/transfer",
    response_model=TransactionResponse,
)
def transfer(
    payload: TransferRequest,
    source_wallet_id: UUID,
    db: Session = Depends(get_db),
    key: str = Depends(require_idempotency_key),
    current_user: User = Depends(get_current_user),
):
    return transfer_funds(
        db,
        source_wallet_id,
        payload.destination_wallet_id,
        payload.amount,
        key,
        current_user.id,
    )


@router.get(
    "/wallets/{wallet_id}",
    response_model=TransactionList,
)
def wallet_history(
    wallet_id: UUID,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    transactions, total = get_wallet_transactions(
        db,
        wallet_id,
        current_user.id,
        skip,
        limit,
    )

    return {
        "transactions": transactions,
        "total": total,
    }
