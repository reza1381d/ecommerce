from enum import StrEnum

from app.core.exceptions import InvalidReservationTransitionError


class ReservationStatus(StrEnum):
    ACTIVE = "active"
    CONSUMED = "consumed"
    EXPIRED = "expired"


ALLOWED_TRANSITIONS: dict[
    ReservationStatus,
    frozenset[ReservationStatus],
] = {
    ReservationStatus.ACTIVE: frozenset(
        {
            ReservationStatus.CONSUMED,
            ReservationStatus.EXPIRED,
        }
    ),
    ReservationStatus.CONSUMED: frozenset(),
    ReservationStatus.EXPIRED: frozenset(),
}


def validate_transition(
    current_status: str,
    new_status: str,
) -> None:
    try:
        current = ReservationStatus(current_status)
        new = ReservationStatus(new_status)
    except ValueError:
        raise InvalidReservationTransitionError()

    allowed_statuses = ALLOWED_TRANSITIONS[current]

    if new not in allowed_statuses:
        raise InvalidReservationTransitionError()