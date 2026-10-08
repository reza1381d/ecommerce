from decimal import Decimal

from app.auth.security import create_access_token
from app.orders.models import Order, OrderAddress, OrderItem
from app.payments.models import Payment
from app.products.models import Product
from app.users.models import User


def make_user(db, *, email="customer@example.com", role="customer"):
    user = User(
        email=email,
        password_hash="unused-in-test",
        first_name="Test",
        last_name="Customer",
        role=role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def auth_headers(user):
    return {"Authorization": f"Bearer {create_access_token(user.id)}"}


def make_order(db, user, *, status="pending_payment", total=Decimal("100")):
    order = Order(
        user_id=user.id,
        status=status,
        subtotal=total,
        discount_amount=Decimal("0"),
        shipping_amount=Decimal("0"),
        tax_amount=Decimal("0"),
        total_amount=total,
    )
    db.add(order)
    db.flush()
    db.add(
        OrderAddress(
            order_id=order.id,
            recipient_name="Test Customer",
            phone="09120000000",
            province="Tehran",
            city="Tehran",
            address_line="Test street",
            postal_code="1234567890",
        )
    )
    db.commit()
    db.refresh(order)
    return order


def make_payment(db, order, *, status="successful", amount=Decimal("100"), provider="mock", created_at=None):
    payment = Payment(
        order_id=order.id,
        amount=amount,
        status=status,
        provider=provider,
        provider_payment_id=f"test-{order.id}-{status}",
        **({"created_at": created_at} if created_at is not None else {}),
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


def make_order_item(db, order, *, quantity=2):
    product = Product(
        name="Test product",
        description=None,
        price=Decimal("50"),
        stock=quantity,
        reserved_stock=0,
        is_active=True,
    )
    db.add(product)
    db.flush()
    item = OrderItem(
        order_id=order.id,
        product_id=product.id,
        product_name=product.name,
        unit_price=product.price,
        quantity=quantity,
        total_price=product.price * quantity,
    )
    db.add(item)
    db.commit()
    return item
