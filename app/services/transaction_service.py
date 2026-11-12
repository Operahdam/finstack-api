
from decimal import Decimal
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.models.wallet import Wallet
from app.models.transaction import WalletTransaction


def lock_idempotency_key(db: Session, key: str):
    db.execute(
        text(
            "SELECT pg_advisory_xact_lock("
            "hashtextextended(:key, 0))"
        ),
        {"key": key},
    )


def lock_wallets(
    db: Session,
    wallet_ids: list[UUID],
    user_id: UUID,
):
    wallets = {}

    for wallet_id in sorted(set(wallet_ids), key=str):
        wallet = db.execute(
            select(Wallet)
            .where(
                Wallet.id == wallet_id,
                Wallet.user_id == user_id,
            )
            .with_for_update()
        ).scalar_one_or_none()

        if wallet is None:
            raise HTTPException(404, detail="Wallet not found")

        wallets[wallet_id] = wallet

    return wallets


def create_transaction(
    db: Session,
    transaction_type: str,
    amount: Decimal,
    idempotency_key: str,
    user_id: UUID,
    source_id: UUID | None = None,
    destination_id: UUID | None = None,
):
    try:
        lock_idempotency_key(db, idempotency_key)

        wallet_ids = [
            wallet_id
            for wallet_id in (source_id, destination_id)
            if wallet_id is not None
        ]

        wallets = lock_wallets(
            db,
            wallet_ids,
            user_id,
        )

        source = wallets.get(source_id)
        destination = wallets.get(destination_id)

        if source and destination:
            if source.currency != destination.currency:
                raise HTTPException(
                    400,
                    detail="Wallet currencies must match",
                )

        currency = (
            destination.currency
            if destination
            else source.currency
        )

        existing = db.execute(
            select(WalletTransaction).where(
                WalletTransaction.idempotency_key == idempotency_key
            )
        ).scalar_one_or_none()

        if existing:
            same_request = (
                existing.transaction_type == transaction_type
                and existing.amount == amount
                and existing.currency == currency
                and existing.source_wallet_id == source_id
                and existing.destination_wallet_id == destination_id
            )

            if not same_request:
                raise HTTPException(
                    409,
                    detail="Idempotency key already used for another request",
                )

            db.commit()
            return existing

        if transaction_type == "CREDIT":
            destination.balance += amount

        elif transaction_type == "DEBIT":
            if source.balance < amount:
                raise HTTPException(400, detail="Insufficient balance")

            source.balance -= amount

        elif transaction_type == "TRANSFER":
            if source.balance < amount:
                raise HTTPException(400, detail="Insufficient balance")

            source.balance -= amount
            destination.balance += amount

        transaction = WalletTransaction(
            source_wallet_id=source_id,
            destination_wallet_id=destination_id,
            transaction_type=transaction_type,
            amount=amount,
            currency=currency,
            reference=str(uuid4()),
            idempotency_key=idempotency_key,
        )

        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        return transaction

    except Exception:
        db.rollback()
        raise


def credit_wallet(db, wallet_id, amount, key, user_id):
    return create_transaction(
        db,
        "CREDIT",
        amount,
        key,
        user_id=user_id,
        destination_id=wallet_id,
    )


def debit_wallet(db, wallet_id, amount, key, user_id):
    return create_transaction(
        db,
        "DEBIT",
        amount,
        key,
        user_id=user_id,
        source_id=wallet_id,
    )


def transfer_funds(
    db,
    source_id,
    destination_id,
    amount,
    key,
    user_id,
):
    if source_id == destination_id:
        raise HTTPException(
            400,
            detail="Cannot transfer to same wallet",
        )

    return create_transaction(
        db,
        "TRANSFER",
        amount,
        key,
        user_id=user_id,
        source_id=source_id,
        destination_id=destination_id,
    )


def get_wallet_transactions(
    db,
    wallet_id,
    user_id,
    skip=0,
    limit=20,
):
    wallet = db.execute(
        select(Wallet).where(
            Wallet.id == wallet_id,
            Wallet.user_id == user_id,
        )
    ).scalar_one_or_none()

    if wallet is None:
        raise HTTPException(
            404,
            detail="Wallet not found",
        )

    query = select(WalletTransaction).where(
        (WalletTransaction.source_wallet_id == wallet_id)
        | (WalletTransaction.destination_wallet_id == wallet_id)
    )

    total = db.scalar(
        select(func.count()).select_from(query.subquery())
    )

    transactions = db.execute(
        query.order_by(
            WalletTransaction.created_at.desc()
        )
        .offset(skip)
        .limit(limit)
    ).scalars().all()

    return transactions, total
