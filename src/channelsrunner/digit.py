from machine import Pin

from src.models import Order

__all__ = ("run_set", "run_get")


def run_set(executor: Pin, order: Order):
    val = order.ctrl_value
    if order.is_toggle_ctrl_value and val in ("1", "O"):
        if val == "1":
            executor.value(1)
        else:
            executor.value(0)
    else:
        raise ValueError(f"Invalid ctrl_value for toggle control: {val}. Expected '1' or 'O'.")


def run_get(executor: Pin) -> int:
    return executor.value()
