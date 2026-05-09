from typing import Dict

from src.models import Pin

from .base import BaseStore


class InitializedPinStore(BaseStore[Pin]):
    """
    A store for managing initialized Pin objects.
    This class maintains a collection of Pin objects indexed by their pin numbers,
    providing methods to retrieve and register pins and check if the store is empty.

    Attributes:
        _items (Dict[int, Pin]): A dictionary mapping pin numbers to Pin objects.

    Methods:
        get_item(unique_ref): Retrieve a Pin object by its pin number.
        add_item(pin_obj): Add a Pin object to the store, indexed by its pin number
        is_empty(): Check if the store has any Pin objects registered.
    """

    _items: Dict[int, Pin] = {}  # {pin_number: pin_obj}

    def add_item(self, pin_obj: Pin):
        """
        Add a Pin object to the store, indexed by its pin number.

        Note:
        - This method overrides the BaseStore's add_item to ensure that
            the unique reference is the pin number of the Pin object.
        """
        return super().add_item(pin_obj.pin_number, pin_obj)
