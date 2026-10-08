from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.orders.schemas import OrderResponse


class AdminOrderCustomer(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str


class AdminOrderPayment(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: Decimal
    status: str
    provider: str
    provider_payment_id: str | None


class AdminOrderResponse(OrderResponse):
    customer: AdminOrderCustomer
    payment_status: str
    latest_payment: AdminOrderPayment | None


class AdminOrderListResponse(BaseModel):
    items: list[AdminOrderResponse]
    page: int
    limit: int
    total: int