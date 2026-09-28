import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import (
    ReservationNotActiveError,
    ReservationNotExpiredError,
    ReservationNotFoundError,
)
from app.inventory.service import InventoryService
from app.orders.models import OrderItem
from app.reservations.models import Reservation
from app.reservations.state_machine import (
    ReservationStatus,
    validate_transition,
)

logger = logging.getLogger(__name__)


class ReservationService:

    @staticmethod
    def expire_reservation(
        db: Session,
        reservation_id: int,
    ) -> Reservation:

        reservation = db.scalar(
            select(Reservation)
            .options(
                selectinload(Reservation.order_item)
            )
            .where(
                Reservation.id == reservation_id
            )
            .with_for_update()
        )

        if reservation is None:
            raise ReservationNotFoundError()

        if reservation.status != ReservationStatus.ACTIVE.value:
            raise ReservationNotActiveError()

        now = datetime.now(timezone.utc)

        if reservation.expires_at > now:
            raise ReservationNotExpiredError()

        order_item: OrderItem = reservation.order_item

        InventoryService.release(
            db=db,
            product_id=order_item.product_id,
            quantity=reservation.quantity,
        )

        validate_transition(
            current_status=reservation.status,
            new_status=ReservationStatus.EXPIRED,
        )

        reservation.status = ReservationStatus.EXPIRED.value

        try:
            db.commit()
            db.refresh(reservation)

            return reservation

        except Exception:
            db.rollback()
            raise

    @staticmethod
    def expire_due_reservations(
        db: Session,
    ) -> int:

        now = datetime.now(timezone.utc)

        reservation_ids = db.scalars(
            select(Reservation.id)
            .where(
                Reservation.status == ReservationStatus.ACTIVE.value,
                Reservation.expires_at <= now,
            )
        ).all()

        expired_count = 0

        for reservation_id in reservation_ids:
            try:
                ReservationService.expire_reservation(
                    db=db,
                    reservation_id=reservation_id,
                )

                expired_count += 1

            except Exception:
                logger.exception(
                    "Failed to expire reservation %s",
                    reservation_id,
                )

        return expired_count