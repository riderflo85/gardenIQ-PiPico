from src.datasheet import InvalidChannelError
from src.models import Order
from src.models import Pin
from src.stores import init_pins_store

from . import analog
from . import digit
from . import pwm


class ChannelHandler:
    """Handler for executing orders on the appropriate channels based on the order's attributes and
    the pin configuration.
    """

    def handle_order(self, order: Order) -> int | None:
        """Determine the pin number to execute based on the order's trigger type (sensor or controller).
        Fetch the pin configuration from the pins store.
        Execute the order using the appropriate channel handler (digit, pwm, analog) based on the pin's channel choice.
        """
        if order.is_trigger_sensor():
            pin_num: int = order.sensor
        elif order.is_trigger_controller() or order.is_trigger_get_controller_value():
            pin_num: int = order.controller
        else:
            raise ValueError("The order does not trigger any sensor or controller action. No pin number to handle.")

        pin_cfg = init_pins_store.get_item(pin_num)

        if pin_cfg.executor is None:
            raise ValueError(f"Pin {pin_num} is not initialized. Cannot execute order.")

        match pin_cfg.channel_choiced:
            case "digit":
                return self._handle_digit(pin_cfg, order)
            case "pwm":
                return self._handle_pwm(pin_cfg, order)
            case "analog":
                return self._handle_analog(pin_cfg)
            case _:
                raise InvalidChannelError(pin_cfg.channel_choiced)

    def _handle_digit(self, pin: Pin, order: Order) -> int | None:
        if order.action_type == Order.ACT_TYPE_GET:
            return digit.run_get(pin.executor)  # type: ignore
        elif order.action_type == Order.ACT_TYPE_SET:
            return digit.run_set(pin.executor, order)  # type: ignore

    def _handle_pwm(self, pin: Pin, order: Order) -> int | None:
        if order.action_type == Order.ACT_TYPE_GET:
            return pwm.run_get(pin.executor)  # type: ignore
        elif order.action_type == Order.ACT_TYPE_SET:
            return pwm.run_set(pin.executor, order)  # type: ignore

    def _handle_analog(self, pin: Pin) -> int:
        return analog.run_get(pin.executor)  # type: ignore
