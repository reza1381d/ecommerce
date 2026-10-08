from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_admin
from app.core.database import get_db
from app.store_settings.schemas import (
    StoreSettingsResponse,
    StoreSettingsUpdate,
)
from app.store_settings.service import (
    get_store_settings,
    update_store_settings,
)
from app.users.models import User


router = APIRouter(tags=["Store Settings"])


@router.get(
    "/store/settings",
    response_model=StoreSettingsResponse,
)
def read_store_settings(
    db: Session = Depends(get_db),
):
    return get_store_settings(db)


@router.put(
    "/admin/store/settings",
    response_model=StoreSettingsResponse,
)
def save_store_settings(
    data: StoreSettingsUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return update_store_settings(
        db=db,
        data=data,
    )