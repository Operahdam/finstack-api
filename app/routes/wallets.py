
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.wallet import (
    WalletBalance,
    WalletCreate,
    WalletResponse,
)
from app.services.wallet_service import create_wallet, get_wallet

router = APIRouter(prefix="/wallets", tags=["Wallets"])

from app.models.user import User
from app.routes.auth import get_current_user


@router.post(
    "",
    response_model=WalletResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_new_wallet(
    wallet_data: WalletCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_wallet(
        db,
        wallet_data,
        current_user.id,
    )

@router.get("/{wallet_id}", response_model=WalletResponse)
def retrieve_wallet(
    wallet_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    wallet = get_wallet(db, wallet_id, current_user.id)

    if wallet is None:
        raise HTTPException(
            status_code=404,
            detail="Wallet not found",
        )

    return wallet

@router.get("/{wallet_id}/balance", response_model=WalletBalance)
def retrieve_wallet_balance(
    wallet_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    wallet = get_wallet(db, wallet_id, current_user.id)

    if wallet is None:
        raise HTTPException(
            status_code=404,
            detail="Wallet not found",
        )

    return WalletBalance(
        wallet_id=wallet.id,
        currency=wallet.currency,
        balance=wallet.balance,
    )
