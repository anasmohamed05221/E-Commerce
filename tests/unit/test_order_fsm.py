"""Unit tests for the order status FSM (finite state machine).

The FSM defines which OrderStatus transitions are allowed. These tests
exercise the transition rule in isolation — no DB, no HTTP, no fixtures.
Every state combination is enumerated explicitly so a regression in the
allowed-transitions map is caught immediately.
"""
from models.enums import OrderStatus
from services.orders import OrderService


# --- Allowed transitions from PENDING ---

def test_pending_to_confirmed_is_allowed():
    assert OrderService._is_allowed_status_transition(
        OrderStatus.PENDING, OrderStatus.CONFIRMED
    ) is True


def test_pending_to_cancelled_is_not_in_fsm():
    """Cancellation is a separate operation, not an FSM transition."""
    assert OrderService._is_allowed_status_transition(
        OrderStatus.PENDING, OrderStatus.CANCELLED
    ) is False


# --- Disallowed transitions from PENDING ---

def test_pending_to_completed_is_not_allowed():
    """Cannot skip CONFIRMED — orders must be confirmed before completion."""
    assert OrderService._is_allowed_status_transition(
        OrderStatus.PENDING, OrderStatus.COMPLETED
    ) is False


# --- Allowed transitions from CONFIRMED ---

def test_confirmed_to_shipped_is_allowed():
    assert OrderService._is_allowed_status_transition(
        OrderStatus.CONFIRMED, OrderStatus.SHIPPED
    ) is True


def test_confirmed_to_completed_is_not_allowed():
    """Must go through SHIPPED before COMPLETED."""
    assert OrderService._is_allowed_status_transition(
        OrderStatus.CONFIRMED, OrderStatus.COMPLETED
    ) is False


def test_confirmed_to_cancelled_is_not_in_fsm():
    """Cancellation is a separate operation, not an FSM transition."""
    assert OrderService._is_allowed_status_transition(
        OrderStatus.CONFIRMED, OrderStatus.CANCELLED
    ) is False


# --- Disallowed transitions from CONFIRMED ---

def test_confirmed_to_pending_is_not_allowed():
    """Status transitions move forward; cannot revert to PENDING."""
    assert OrderService._is_allowed_status_transition(
        OrderStatus.CONFIRMED, OrderStatus.PENDING
    ) is False


# --- COMPLETED is a terminal state ---

def test_completed_to_pending_is_not_allowed():
    assert OrderService._is_allowed_status_transition(
        OrderStatus.COMPLETED, OrderStatus.PENDING
    ) is False


def test_completed_to_confirmed_is_not_allowed():
    assert OrderService._is_allowed_status_transition(
        OrderStatus.COMPLETED, OrderStatus.CONFIRMED
    ) is False


def test_completed_to_cancelled_is_not_allowed():
    """A completed order cannot be cancelled — it has already been fulfilled."""
    assert OrderService._is_allowed_status_transition(
        OrderStatus.COMPLETED, OrderStatus.CANCELLED
    ) is False


# --- CANCELLED is a terminal state ---

def test_cancelled_to_pending_is_not_allowed():
    assert OrderService._is_allowed_status_transition(
        OrderStatus.CANCELLED, OrderStatus.PENDING
    ) is False


def test_cancelled_to_confirmed_is_not_allowed():
    assert OrderService._is_allowed_status_transition(
        OrderStatus.CANCELLED, OrderStatus.CONFIRMED
    ) is False


def test_cancelled_to_completed_is_not_allowed():
    assert OrderService._is_allowed_status_transition(
        OrderStatus.CANCELLED, OrderStatus.COMPLETED
    ) is False


# --- Same-status checks ---
# The FSM treats same-status as "not in allowed list" → False.
# The service layer raises 409 separately for the explicit same-status case;
# the FSM itself just answers "is this transition in my allowed map?".

def test_pending_to_pending_is_not_allowed():
    assert OrderService._is_allowed_status_transition(
        OrderStatus.PENDING, OrderStatus.PENDING
    ) is False


def test_confirmed_to_confirmed_is_not_allowed():
    assert OrderService._is_allowed_status_transition(
        OrderStatus.CONFIRMED, OrderStatus.CONFIRMED
    ) is False


def test_completed_to_completed_is_not_allowed():
    assert OrderService._is_allowed_status_transition(
        OrderStatus.COMPLETED, OrderStatus.COMPLETED
    ) is False


def test_cancelled_to_cancelled_is_not_allowed():
    assert OrderService._is_allowed_status_transition(
        OrderStatus.CANCELLED, OrderStatus.CANCELLED
    ) is False


# --- Allowed transitions from SHIPPED ---

def test_shipped_to_completed_is_allowed():
    assert OrderService._is_allowed_status_transition(
        OrderStatus.SHIPPED, OrderStatus.COMPLETED
    ) is True


# --- Disallowed transitions from SHIPPED ---

def test_shipped_to_pending_is_not_allowed():
    assert OrderService._is_allowed_status_transition(
        OrderStatus.SHIPPED, OrderStatus.PENDING
    ) is False


def test_shipped_to_confirmed_is_not_allowed():
    assert OrderService._is_allowed_status_transition(
        OrderStatus.SHIPPED, OrderStatus.CONFIRMED
    ) is False


def test_shipped_to_cancelled_is_not_in_fsm():
    """Cancellation is a separate operation, not an FSM transition."""
    assert OrderService._is_allowed_status_transition(
        OrderStatus.SHIPPED, OrderStatus.CANCELLED
    ) is False


def test_shipped_to_shipped_is_not_allowed():
    assert OrderService._is_allowed_status_transition(
        OrderStatus.SHIPPED, OrderStatus.SHIPPED
    ) is False