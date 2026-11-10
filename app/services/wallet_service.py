
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.wallet import Wallet
from app.schemas.wallet import WalletCreate


def create_wallet(db: Session, wallet_data: WalletCreate) -> Wallet:
    wallet = Wallet(currency=wallet_data.currency)

    db.add(wallet)
    db.commit()
    db.refresh(wallet)

    return wallet


def get_wallet(db: Session, wallet_id: UUID) -> Wallet | None:
    return db.get(Wallet, wallet_id)
