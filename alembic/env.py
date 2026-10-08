from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine

from app.categories import models as category_models
from app.users import models as user_models
from app.products import models as product_models
from app.cart import models as cart_models
from app.orders import models as order_models
from app.payments import models as payment_models
from app.addresses.models import Address
from app.coupons.models import Coupon, CouponUsage
from app.reservations.models import Reservation
from app.store_settings import models as store_settings_models
from app.core.config import settings
from app.core.database import Base


config = context.config


if config.config_file_name is not None:
    fileConfig(config.config_file_name)


target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = settings.database_url

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={
            "paramstyle": "named",
        },
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(
        settings.database_url,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()