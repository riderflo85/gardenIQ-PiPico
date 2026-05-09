from typing import Dict

from src.models import Order

from .base import BaseStore


class CommandStore(BaseStore[Order]):
    """
    A store for managing Command orders.
    This class provides a centralized repository for storing and retrieving Order
    objects using their primary keys (pk) as identifiers.

    Attributes:
        _items (Dict[int, Order]): Internal dictionary storing Order objects
            indexed by their order ID.

    Methods:
        get_item(unique_ref): Retrieve an Order by its ID.
        add_item(order_obj): Add an Order to the store.
        is_empty(): Check if the store has any Order objects registered.
    """

    _items: Dict[int, Order] = {}  # {order_id: order_obj}

    def add_item(self, order_obj: Order) -> None:
        """
        Add an Order object to the store, indexed by its primary key.

        Note:
        - This method overrides the BaseStore's add_item to ensure that
            the unique reference is the primary key of the Order object.
        """
        return super().add_item(order_obj.pk, order_obj)
