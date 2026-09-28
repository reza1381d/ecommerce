from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class CheckoutRequest(BaseModel):
    address_id: int


class OrderItemResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    product_id: int
    product_name: str
    unit_price: Decimal
    quantity: int
    total_price: Decimal


class OrderAddressResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    recipient_name: str
    phone: str
    province: str
    city: str
    address_line: str
    postal_code: str


class OrderResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    user_id: int
    status: str
    subtotal: Decimal
    discount_amount: Decimal
    shipping_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    address: OrderAddressResponse
    items: list[OrderItemResponse]


class OrderListResponse(BaseModel):
    items: list[OrderResponse]
    page: int
    limit: int
    total: int