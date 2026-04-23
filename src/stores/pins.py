from typing import Dict

from src.models import Pin


class InitializedPinStore:
    """
    A store for managing initialized Pin objects.
    This class maintains a collection of Pin objects indexed by their pin numbers,
    providing methods to retrieve and register pins.

    Attributes:
        _pins (Dict[int, Pin]): A dictionary mapping pin numbers to Pin objects.

    Methods:
        get_pin(pin_num): Retrieve a Pin object by its pin number.
        add_pin(pin_obj): Add a Pin object to the store, indexed by its pin number
    """

    _pins: Dict[int, Pin] = {}  # {pin_number: pin_obj}

    def get_pin(self, pin_num: int) -> Pin:
        pin_obj = self._pins.get(pin_num, None)
        if pin_obj is None:
            raise KeyError(f"Pin `{pin_num}` not found in initialized pins !")
        return pin_obj

    def add_pin(self, pin_obj: Pin) -> None:
        self._pins[pin_obj.pin_number] = pin_obj
