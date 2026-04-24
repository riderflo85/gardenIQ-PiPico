from typing import Dict
from typing import Generic
from typing import TypeVar

from src.models import Order
from src.models import Pin

T = TypeVar("T", Pin, Order)


class BaseStore(Generic[T]):
    """
    Base class for stores managing collections of Pin or Order objects.
    This class provides common functionality for storing and retrieving items
    based on a unique reference (e.g., pin number for Pin objects, order ID for Order objects).

    Methods:
        get_item(unique_ref): Retrieve an item (Pin or Order) by its unique reference.
        add_item(unique_ref, item): Add an item to the store with its unique reference.
        is_empty(): Check if the store has any items registered.
    """

    _items: Dict[int, T]

    def get_item(self, unique_ref: int) -> T:
        item = self._items.get(unique_ref, None)
        if item is None:
            raise KeyError(f"Item `{unique_ref}` not found in {self.__class__.__name__} !")
        return item

    def add_item(self, unique_ref: int, item: T) -> None:
        self._items[unique_ref] = item

    def is_empty(self) -> bool:
        return len(self._items) == 0
