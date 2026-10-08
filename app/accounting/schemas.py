from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class DashboardTrendPoint(BaseModel):
    date: date
    orders: int
    paid_orders: int
    revenue: Decimal


class DashboardStatsResponse(BaseModel):
    period: str
    start_at: datetime
    end_at: datetime

    total_orders: int
    pending_payment_orders: int
    paid_orders: int
    cancelled_orders: int
    shipped_orders: int
    delivered_orders: int

    successful_payments: int
    pending_payments: int
    failed_payments: int

    total_revenue: Decimal
    average_successful_payment: Decimal

    trend: list[DashboardTrendPoint]

class ProductSalesItem(BaseModel):
    product_id: int
    product_name: str
    quantity_sold: int
    order_count: int
    revenue: Decimal


class ProductSalesResponse(BaseModel):
    period: str
    items: list[ProductSalesItem]


class SalesTimelineItem(BaseModel):
    period: str
    orders: int
    units_sold: int
    revenue: Decimal


class SalesTimelineResponse(BaseModel):
    group_by: str
    items: list[SalesTimelineItem]