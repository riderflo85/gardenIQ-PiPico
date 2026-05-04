from typing import Literal

import pytest

from src.channelsrunner.pwm import run_get
from src.channelsrunner.pwm import run_set
from src.models.order import Order
from tests.mocks.machine import PWM


@pytest.fixture
def pwm():
    """A mock PWM instance with a default duty cycle of 0."""
    return PWM(dest=1, duty_u16_value=0)


def make_order(ctrl_value: str, action_type: Literal["set", "get"] = "set") -> Order:
    """Helper to build an Order for PWM tests."""
    return Order(
        pk=1,
        slug="test-order",
        action_type=action_type,
        sensor=-1,
        controller=1,
        is_toggle_ctrl_value=False,
        ctrl_value=ctrl_value,
    )


class TestRunSet:
    """Tests for the PWM run_set function."""

    def test_sets_duty_cycle_when_ctrl_value_is_valid(self, pwm):
        # GIVEN an order with a valid integer ctrl_value
        order = make_order(ctrl_value="32768")

        # WHEN run_set is called
        run_set(pwm, order)

        # THEN the duty cycle is updated on the PWM executor
        assert pwm.duty_u16() == 32768

    def test_sets_duty_cycle_to_zero_when_ctrl_value_is_zero(self, pwm):
        # GIVEN an order with ctrl_value="0" (non-empty string, truthy in Python)
        order = make_order(ctrl_value="0")
        pwm.duty_u16(512)  # start with a non-zero value

        # WHEN run_set is called
        run_set(pwm, order)

        # THEN the duty cycle is set to 0
        assert pwm.duty_u16() == 0

    def test_sets_max_duty_cycle_when_ctrl_value_is_65535(self, pwm):
        # GIVEN an order with ctrl_value at maximum 16-bit value
        order = make_order(ctrl_value="65535")

        # WHEN run_set is called
        run_set(pwm, order)

        # THEN the duty cycle is set to 65535
        assert pwm.duty_u16() == 65535

    def test_raises_value_error_when_ctrl_value_is_empty(self, pwm):
        # GIVEN an order with an empty ctrl_value
        order = make_order(ctrl_value="")

        # WHEN run_set is called
        # THEN a ValueError is raised
        with pytest.raises(ValueError, match="Invalid ctrl_value for PWM control"):
            run_set(pwm, order)

    def test_raises_value_error_when_ctrl_value_is_none_string(self, pwm):
        # GIVEN an order with ctrl_value="None"
        order = make_order(ctrl_value="None")

        # WHEN run_set is called
        # THEN a ValueError is raised because "None" is truthy but not castable to int
        with pytest.raises((ValueError, TypeError)):
            run_set(pwm, order)


class TestRunGet:
    """Tests for the PWM run_get function."""

    def test_returns_current_duty_cycle(self, pwm):
        # GIVEN a PWM executor with duty cycle set to 1024
        pwm.duty_u16(1024)

        # WHEN run_get is called
        result = run_get(pwm)

        # THEN it returns 1024
        assert result == 1024

    def test_returns_zero_when_duty_cycle_is_zero(self, pwm):
        # GIVEN a PWM executor with duty cycle set to 0
        pwm.duty_u16(0)

        # WHEN run_get is called
        result = run_get(pwm)

        # THEN it returns 0
        assert result == 0

    def test_returns_max_when_duty_cycle_is_max(self, pwm):
        # GIVEN a PWM executor with duty cycle at maximum 16-bit value
        pwm.duty_u16(65535)

        # WHEN run_get is called
        result = run_get(pwm)

        # THEN it returns 65535
        assert result == 65535

    def test_return_type_is_int(self, pwm):
        # GIVEN a PWM executor with a duty cycle value
        pwm.duty_u16(512)

        # WHEN run_get is called
        result = run_get(pwm)

        # THEN the return type is int
        assert isinstance(result, int)
