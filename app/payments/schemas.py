from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class PaymentCreateRequest(BaseModel):
    order_id: int


class PaymentResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    order_id: int
    amount: Decimal
    status: str
    provider: str
    provider_payment_id: str | None