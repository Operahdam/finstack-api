
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class WalletCreate(BaseModel):
    currency: str = Field(
        default="NGN",
        min_length=3,
        max_length=3,
        pattern=r"^[A-Z]{3}$",
    )


class WalletResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    currency: str
    balance: Decimal


class WalletBalance(BaseModel):
    wallet_id: UUID
    currency: str
    balance: Decimal
