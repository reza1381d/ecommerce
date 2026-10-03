from fastapi import FastAPI

from app.addresses.router import router as addresses_router
from app.auth.router import router as auth_router
from app.cart.router import router as cart_router
from app.categories.router import router as categories_router
from app.coupons.router import router as coupons_router
from app.orders.router import router as orders_router
from app.payments.router import router as payments_router
from app.products.router import router as products_router
from app.users.router import router as users_router

from app.core.exceptions import (
    AuthenticationError,
    BusinessRuleError,
    ConflictError,
    DomainError,
    ResourceNotFoundError,
)
from app.core.exception_handlers import (
    handle_authentication,
    handle_business_rule,
    handle_conflict,
    handle_domain_error,
    handle_resource_not_found,
)


app = FastAPI(
    title="E-Commerce API",
    version="0.1.0",
)


app.add_exception_handler(
    ResourceNotFoundError,
    handle_resource_not_found,
)

app.add_exception_handler(
    ConflictError,
    handle_conflict,
)

app.add_exception_handler(
    BusinessRuleError,
    handle_business_rule,
)

app.add_exception_handler(
    DomainError,
    handle_domain_error,
)

app.add_exception_handler(
    AuthenticationError,
    handle_authentication,
)


app.include_router(auth_router)
app.include_router(users_router)
app.include_router(categories_router)
app.include_router(products_router)
app.include_router(cart_router)
app.include_router(orders_router)
app.include_router(payments_router)
app.include_router(addresses_router)
app.include_router(coupons_router)


@app.get("/")
def root():
    return {"message": "E-Commerce API is running"}


@app.get("/health")
def health():
    return {"status": "ok"}