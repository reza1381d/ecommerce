from sqlalchemy import select
from sqlalchemy.orm import Session

from app.store_settings.models import StoreSetting
from app.store_settings.schemas import StoreSettingsUpdate


def get_store_settings(db: Session) -> StoreSetting:
    settings = db.get(StoreSetting, 1)

    if settings is None:
        settings = StoreSetting(
            id=1,
            store_name="فروشگاه اینترنتی",
            palette="blue",
            currency_unit="toman",
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)

    return settings


def update_store_settings(
    db: Session,
    data: StoreSettingsUpdate,
) -> StoreSetting:
    settings = db.scalar(
        select(StoreSetting)
        .where(StoreSetting.id == 1)
        .with_for_update()
    )

    if settings is None:
        settings = StoreSetting(id=1)
        db.add(settings)

    settings.store_name = data.store_name
    settings.palette = data.palette
    settings.currency_unit = data.currency_unit
    settings.home_hero_badge = data.home_hero_badge
    settings.home_hero_title = data.home_hero_title
    settings.home_hero_description = data.home_hero_description
    settings.home_hero_button_label = data.home_hero_button_label

    db.commit()
    db.refresh(settings)

    return settings
