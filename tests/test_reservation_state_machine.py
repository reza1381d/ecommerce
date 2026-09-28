import pytest

from app.core.exceptions import InvalidReservationTransitionError
from app.reservations.state_machine import (
    ALLOWED_TRANSITIONS,
    ReservationStatus,
    validate_transition,
)


class TestReservationStatus:

    def test_all_statuses_exist(self):
        assert ReservationStatus.ACTIVE.value == "active"
        assert ReservationStatus.CONSUMED.value == "consumed"
        assert ReservationStatus.EXPIRED.value == "expired"


class TestReservationTransitions:

    def test_active_can_be_consumed(self):
        validate_transition(
            current_status=ReservationStatus.ACTIVE,
            new_status=ReservationStatus.CONSUMED,
        )

    def test_active_can_be_expired(self):
        validate_transition(
            current_status=ReservationStatus.ACTIVE,
            new_status=ReservationStatus.EXPIRED,
        )

    @pytest.mark.parametrize(
        ("current_status", "new_status"),
        [
            (ReservationStatus.ACTIVE, ReservationStatus.ACTIVE),
            (ReservationStatus.CONSUMED, ReservationStatus.ACTIVE),
            (ReservationStatus.CONSUMED, ReservationStatus.CONSUMED),
            (ReservationStatus.CONSUMED, ReservationStatus.EXPIRED),
            (ReservationStatus.EXPIRED, ReservationStatus.ACTIVE),
            (ReservationStatus.EXPIRED, ReservationStatus.CONSUMED),
            (ReservationStatus.EXPIRED, ReservationStatus.EXPIRED),
        ],
    )
    def test_invalid_transitions(
        self,
        current_status,
        new_status,
    ):
        with pytest.raises(InvalidReservationTransitionError):
            validate_transition(
                current_status=current_status,
                new_status=new_status,
            )


class TestReservationInvalidStatus:

    @pytest.mark.parametrize(
        ("current_status", "new_status"),
        [
            ("unknown", ReservationStatus.CONSUMED),
            (ReservationStatus.ACTIVE, "unknown"),
            ("unknown", "another_unknown"),
        ],
    )
    def test_invalid_status_values(
        self,
        current_status,
        new_status,
    ):
        with pytest.raises(InvalidReservationTransitionError):
            validate_transition(
                current_status=current_status,
                new_status=new_status,
            )


class TestAllowedTransitions:

    def test_active_has_two_allowed_transitions(self):
        assert ALLOWED_TRANSITIONS[ReservationStatus.ACTIVE] == frozenset(
            {
                ReservationStatus.CONSUMED,
                ReservationStatus.EXPIRED,
            }
        )

    def test_consumed_has_no_allowed_transitions(self):
        assert ALLOWED_TRANSITIONS[ReservationStatus.CONSUMED] == frozenset()

    def test_expired_has_no_allowed_transitions(self):
        assert ALLOWED_TRANSITIONS[ReservationStatus.EXPIRED] == frozenset()