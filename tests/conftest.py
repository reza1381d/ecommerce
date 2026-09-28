from sqlalchemy import create_engine, delete
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool
from pydantic_settings import BaseSettings, SettingsConfigDict
from fastapi.testclient import TestClient
import pytest

from app.cart.models import Cart, CartItem
from app.categories.models import Category
from app.core.database import Base, get_db
from app.coupons.models import Coupon, CouponUsage
from app.addresses.models import Address
from app.main import app
from app.orders.models import Order, OrderItem
from app.payments.models import Payment
from app.products.models import Product
from app.users.models import User
from app.reservations.models import Reservation


class TestSettings(BaseSettings):
    test_database_url: str

    model_config = SettingsConfigDict(
        env_file=".env.test",
        env_file_encoding="utf-8",
    )


test_settings = TestSettings()


engine = create_engine(
    test_settings.test_database_url,
    poolclass=NullPool,
)


TestingSessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(
        bind=engine,
    )

    yield

    Base.metadata.drop_all(
        bind=engine,
    )

    engine.dispose()


@pytest.fixture
def db():
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db: Session):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def clean_database():
    yield

    with TestingSessionLocal() as session:
        session.execute(delete(Payment))
        session.execute(delete(CouponUsage))
        session.execute(delete(Reservation))
        session.execute(delete(OrderItem))
        session.execute(delete(Order))
        session.execute(delete(CartItem))
        session.execute(delete(Cart))
        session.execute(delete(Address))
        session.execute(delete(Coupon))
        session.execute(delete(Product))
        session.execute(delete(Category))
        session.execute(delete(User))

        session.commit()