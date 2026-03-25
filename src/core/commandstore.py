from typing import Dict

from src.core.models import Argument
from src.core.models import Order


class CommandStore:
    _args: Dict[int, Argument] = {}  # {arg_id: arg_obj}
    _orders: Dict[int, Order] = {}  # {order_id: order_obj}

    def get_arg(self, arg_id: int) -> Argument:
        arg_obj = self._args.get(arg_id, None)
        if arg_obj is None:
            raise KeyError(f"Argument `{arg_id}` not found in available arguments !")
        return arg_obj

    def get_order(self, order_id: int) -> Order:
        order_obj = self._orders.get(order_id, None)
        if order_obj is None:
            raise KeyError(f"Order `{order_id}` not found in available orders !")
        return order_obj

    def remove_arg(self, arg_id: int) -> None:
        del self._args[arg_id]

    def remove_order(self, order_id: int) -> None:
        del self._orders[order_id]

    def add_arg(self, arg_obj: Argument) -> None:
        self._args[arg_obj.pk] = arg_obj

    def add_order(self, order_obj: Order) -> None:
        self._orders[order_obj.pk] = order_obj
