from typing import Callable
from typing import Literal

from src.core.enum import PseudoEnum


def str_to_bool(value: str) -> bool:
    """Convert a string to a boolean value."""
    if value in ("True", "true"):
        return True
    elif value in ("False", "false"):
        return False
    else:
        raise ValueError(f"Cannot convert '{value}' to bool. Expected 'True' or 'False'.")


class ModelType(PseudoEnum):
    """Model types for frame commands."""

    ORDER = "Order"


class Order:
    """
    Represents a command order to be executed by the system.
    An Order encapsulates all the information needed to perform an action,
    such as retrieving data from a sensor or setting a configuration value.

    Attributes:
        pk (int): Primary key identifier for the order.
        slug (str): Unique slug identifier for the order.
        action_type (Literal["get", "set"]): Type of action to perform.
            - "get": Retrieve data from a resource
            - "set": Set/update a value on a resource
        fields_cfg (tuple[tuple[str, Callable], ...]): Configuration mapping field names
            to their respective cast functions for serialization/deserialization.
    """

    fields_cfg: tuple[tuple[str, Callable], ...] = (
        ("pk", int),
        ("slug", str),
        ("action_type", str),
    )

    def __init__(self, pk: int, slug: str, action_type: Literal["get", "set"]) -> None:
        self.pk = pk
        self.slug = slug
        self.action_type = action_type

    def execute(self):
        """Execute the order (e.g : get temp to sensor)"""
