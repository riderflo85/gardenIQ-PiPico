from typing import Literal

import pytest

from src.channelsrunner.digit import run_get
from src.channelsrunner.digit import run_set
from src.models.order import Order
from tests.mocks.machine import Pin


@pytest.fixture
def pin():
    """A mock Pin instance initialized with value 0."""
    return Pin(id=1, mode=Pin.OUT)


def make_order(is_toggle: bool, ctrl_value: str, action_type: Literal["get", "set"] = "set") -> Order:
    """Helper to build an Order for digit tests."""
    return Order(
        pk=1,
        slug="test-order",
        action_type=action_type,
        sensor=-1,
        controller=1,
        is_toggle_ctrl_value=is_toggle,
        ctrl_value=ctrl_value,
    )


class TestRunSet:
    """Tests for the run_set function."""

    def test_set_value_high_when_ctrl_value_is_one(self, pin):
        # GIVEN an order with is_toggle_ctrl_value=True and ctrl_value="1"
        order = make_order(is_toggle=True, ctrl_value="1")

        # WHEN run_set is called
        run_set(pin, order)

        # THEN the pin value is set to 1
        assert pin.value() == 1

    def test_set_value_low_when_ctrl_value_is_O(self, pin):
        # GIVEN an order with is_toggle_ctrl_value=True and ctrl_value="O"
        order = make_order(is_toggle=True, ctrl_value="O")
        pin.value(1)  # start high

        # WHEN run_set is called
        run_set(pin, order)

        # THEN the pin value is set to 0
        assert pin.value() == 0

    def test_raises_value_error_when_not_toggle(self, pin):
        # GIVEN an order with is_toggle_ctrl_value=False
        order = make_order(is_toggle=False, ctrl_value="1")

        # WHEN run_set is called
        # THEN a ValueError is raised
        with pytest.raises(ValueError, match="Invalid ctrl_value for toggle control"):
            run_set(pin, order)

    def test_raises_value_error_when_ctrl_value_is_invalid(self, pin):
        # GIVEN an order with is_toggle_ctrl_value=True but an unsupported ctrl_value
        order = make_order(is_toggle=True, ctrl_value="on")

        # WHEN run_set is called
        # THEN a ValueError is raised
        with pytest.raises(ValueError, match="Invalid ctrl_value for toggle control"):
            run_set(pin, order)


class TestRunGet:
    """Tests for the run_get function."""

    def test_returns_current_pin_value_when_low(self, pin):
        # GIVEN a pin whose current value is 0
        pin.value(0)

        # WHEN run_get is called
        result = run_get(pin)

        # THEN it returns 0
        assert result == 0

    def test_returns_current_pin_value_when_high(self, pin):
        # GIVEN a pin whose current value is 1
        pin.value(1)

        # WHEN run_get is called
        result = run_get(pin)

        # THEN it returns 1
        assert result == 1
