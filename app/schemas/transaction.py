
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MoneyRequest(BaseModel):
    amount: Decimal = Field(
        gt=0,
        max_digits=18,
        decimal_places=2,
    )


class TransferRequest(MoneyRequest):
    destination_wallet_id: UUID


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source_wallet_id: UUID | None
    destination_wallet_id: UUID | None
    transaction_type: Literal["CREDIT", "DEBIT", "TRANSFER"]
    amount: Decimal
    currency: str
    reference: str
    idempotency_key: str


class TransactionList(BaseModel):
    transactions: list[TransactionResponse]
    total: int
