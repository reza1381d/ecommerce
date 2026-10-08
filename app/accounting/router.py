from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_admin
from app.core.database import get_db
from app.accounting.schemas import (
    DashboardStatsResponse,
    ProductSalesResponse,
    SalesTimelineResponse,
)
from app.accounting.service import (
    get_dashboard_stats,
    get_product_sales,
    get_sales_timeline,
)
from app.users.models import User


router = APIRouter(
    prefix="/admin/dashboard",
    tags=["Admin Dashboard"],
)


@router.get(
    "/stats",
    response_model=DashboardStatsResponse,
)
def read_dashboard_stats(
    period: Literal["7d", "30d", "90d"] = Query(
        default="30d"
    ),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return get_dashboard_stats(
        db=db,
        period=period,
    )


@router.get(
    "/product-sales",
    response_model=ProductSalesResponse,
)
def read_product_sales(
    period: Literal["7d", "30d", "90d"] = Query(default="30d"),
    limit: int = Query(default=10, ge=1, le=100),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return get_product_sales(
        db=db,
        period=period,
        limit=limit,
    )


@router.get(
    "/sales-timeline",
    response_model=SalesTimelineResponse,
)
def read_sales_timeline(
    group_by: Literal["day", "month", "year"] = Query(default="day"),
    limit: int = Query(default=30, ge=1, le=366),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    if (start_date is None) != (end_date is None):
        raise HTTPException(status_code=422, detail="start_date and end_date must be provided together.")
    if start_date is not None and end_date is not None:
        if start_date > end_date:
            raise HTTPException(status_code=422, detail="start_date must be on or before end_date.")
        if group_by == "day":
            bucket_count = (end_date - start_date).days + 1
        elif group_by == "month":
            bucket_count = (end_date.year - start_date.year) * 12 + end_date.month - start_date.month + 1
        else:
            bucket_count = end_date.year - start_date.year + 1
        if bucket_count > 366:
            raise HTTPException(status_code=422, detail="The selected range cannot exceed 366 periods.")

    return get_sales_timeline(
        db=db,
        group_by=group_by,
        limit=limit,
        start_date=start_date,
        end_date=end_date,
    )
