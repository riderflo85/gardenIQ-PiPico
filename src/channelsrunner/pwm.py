from machine import PWM

from src.models import Order

__all__ = ("run_set", "run_get")


def run_set(executor: PWM, order: Order):
    if val := order.ctrl_value:
        executor.duty_u16(int(val))
    else:
        raise ValueError(
            f"Invalid ctrl_value for PWM control: {val}. "
            "Expected a non-empty string representing an integer duty cycle value."
        )


def run_get(executor: PWM) -> int:
    return executor.duty_u16()
