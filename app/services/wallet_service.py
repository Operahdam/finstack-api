
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.wallet import Wallet
from app.schemas.wallet import WalletCreate


def create_wallet(
    db: Session,
    wallet_data: WalletCreate,
    user_id: UUID,
) -> Wallet:
    wallet = Wallet(
        currency=wallet_data.currency,
        user_id=user_id,
    )

    db.add(wallet)
    db.commit()
    db.refresh(wallet)

    return wallet

def get_wallet(
    db: Session,
    wallet_id: UUID,
    user_id: UUID,
) -> Wallet | None:
    return db.query(Wallet).filter(
        Wallet.id == wallet_id,
        Wallet.user_id == user_id,
    ).first()
