class DomainError(Exception):
    """Base class for all business/domain errors."""


class ResourceNotFoundError(DomainError):
    """Base class for resources that could not be found."""


class ConflictError(DomainError):
    """Base class for business conflicts."""


class BusinessRuleError(DomainError):
    """Base class for business rule violations."""


class AuthenticationError(DomainError):
    """Base class for authentication failures."""


# -------------------------
# Auth / Users
# -------------------------

class EmailAlreadyRegisteredError(ConflictError):
    def __init__(self):
        super().__init__("Email already registered")


class PhoneAlreadyRegisteredError(ConflictError):
    def __init__(self):
        super().__init__("Phone already registered")


class PhoneUpdateConflictError(BusinessRuleError):
    def __init__(self):
        super().__init__("Phone already registered")
        

class InvalidCredentialsError(AuthenticationError):
    def __init__(self):
        super().__init__("Invalid email or password")


class InactiveUserError(AuthenticationError):
    def __init__(self):
        super().__init__("User is inactive")


class PhoneRemovalNotAllowedError(BusinessRuleError):
    def __init__(self):
        super().__init__("Phone cannot be removed")


# -------------------------
# Categories
# -------------------------

class CategoryNotFoundError(ResourceNotFoundError):
    def __init__(self):
        super().__init__("Category not found")


class CategoryAlreadyExistsError(ConflictError):
    def __init__(self):
        super().__init__("Category name already exists")


class CategoryInactiveError(ConflictError):
    def __init__(self):
        super().__init__("Category is inactive")


# -------------------------
# Products
# -------------------------

class ProductNotFoundError(ResourceNotFoundError):
    def __init__(self):
        super().__init__("Product not found")


class ProductInactiveError(ConflictError):
    def __init__(self):
        super().__init__("Product is inactive")


class StockBelowReservedError(ConflictError):
    def __init__(self):
        super().__init__(
            "Stock cannot be lower than reserved stock"
        )


# -------------------------
# Cart
# -------------------------

class CartItemNotFoundError(ResourceNotFoundError):
    def __init__(self):
        super().__init__("Cart item not found")


class InsufficientStockError(ConflictError):
    def __init__(self):
        super().__init__("Insufficient stock")


# -------------------------
# Orders
# -------------------------

class CartEmptyError(ResourceNotFoundError):
    def __init__(self):
        super().__init__("Cart is empty")


class InvalidOrderTransitionError(ConflictError):
    def __init__(self):
        super().__init__("Invalid order status transition")


class InvalidReservationTransitionError(ConflictError):
    def __init__(self):
        super().__init__(
            "Invalid reservation status transition"
        )


class OrderNotFoundError(ResourceNotFoundError):
    def __init__(self):
        super().__init__("Order not found")


class OrderNotAwaitingPaymentError(ConflictError):
    def __init__(self):
        super().__init__(
            "Order is not awaiting payment"
        )


class OrderAlreadyPaidError(ConflictError):
    def __init__(self):
        super().__init__("Order has already been paid")


# -------------------------
# Payments
# -------------------------

class PaymentNotFoundError(ResourceNotFoundError):
    def __init__(self):
        super().__init__("Payment not found")


# -------------------------
# Addresses
# -------------------------

class AddressNotFoundError(ResourceNotFoundError):
    def __init__(self):
        super().__init__("Address not found")


# -------------------------
# Reservations
# -------------------------

class ReservationNotFoundError(ResourceNotFoundError):
    def __init__(self):
        super().__init__("Reservation not found")


class ReservationNotActiveError(ConflictError):
    def __init__(self):
        super().__init__("Reservation is not active")


class ReservationNotExpiredError(ConflictError):
    def __init__(self):
        super().__init__(
            "Reservation has not expired yet"
        )


# -------------------------
# Coupons
# -------------------------

class CouponNotFoundError(ResourceNotFoundError):
    def __init__(self):
        super().__init__("Coupon not found")


class CouponAlreadyExistsError(ConflictError):
    def __init__(self):
        super().__init__("Coupon already exists")


class CouponInactiveError(ConflictError):
    def __init__(self):
        super().__init__("Coupon is inactive")


class CouponNotStartedError(ConflictError):
    def __init__(self):
        super().__init__("Coupon has not started yet")


class CouponExpiredError(ConflictError):
    def __init__(self):
        super().__init__("Coupon has expired")


class CouponNotEligibleError(ConflictError):
    def __init__(self):
        super().__init__("Coupon is not eligible")


class CouponUsageLimitError(ConflictError):
    def __init__(self):
        super().__init__("Coupon usage limit reached")


class CouponAlreadyUsedError(ConflictError):
    def __init__(self):
        super().__init__("Coupon has already been used")
