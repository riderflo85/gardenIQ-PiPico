from typing import Dict

from src.core.models import Order


class CommandStore:
    """
    A store for managing Command orders.
    This class provides a centralized repository for storing and retrieving Order
    objects using their primary keys (pk) as identifiers.

    Attributes:
        _orders (Dict[int, Order]): Internal dictionary storing Order objects
            indexed by their order ID.

    Methods:
        get_order(order_id): Retrieve an Order by its ID.
        remove_order(order_id): Remove an Order from the store.
        add_order(order_obj): Add an Order to the store.
    """

    _orders: Dict[int, Order] = {}  # {order_id: order_obj}

    def get_order(self, order_id: int) -> Order:
        order_obj = self._orders.get(order_id, None)
        if order_obj is None:
            raise KeyError(f"Order `{order_id}` not found in available orders !")
        return order_obj

    def remove_order(self, order_id: int) -> None:
        del self._orders[order_id]

    def add_order(self, order_obj: Order) -> None:
        self._orders[order_obj.pk] = order_obj
