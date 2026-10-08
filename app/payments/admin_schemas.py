from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr


class AdminPaymentCustomer(BaseModel):
    id: int
    email: EmailStr
    first_name: str
    last_name: str
    phone: str | None


class AdminPaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    amount: Decimal
    status: str
    provider: str
    provider_payment_id: str | None
    created_at: datetime
    order_status: str
    customer: AdminPaymentCustomer


class AdminPaymentListResponse(BaseModel):
    items: list[AdminPaymentResponse]
    page: int
    limit: int
    total: int