from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_admin
from app.core.database import get_db
from app.users.admin_schemas import AdminUserListResponse
from app.users.admin_service import list_users
from app.users.models import User


router = APIRouter(
    prefix="/admin/users",
    tags=["Admin Users"],
)


@router.get(
    "",
    response_model=AdminUserListResponse,
)
def get_all_users(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None, max_length=200),
    sort_by: Literal[
        "id",
        "email",
        "first_name",
        "last_name",
        "role",
        "created_at",
    ] = Query(default="created_at"),
    sort_order: Literal["asc", "desc"] = Query(default="desc"),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    users, total = list_users(
        db=db,
        page=page,
        limit=limit,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return AdminUserListResponse(
        items=users,
        page=page,
        limit=limit,
        total=total,
    )