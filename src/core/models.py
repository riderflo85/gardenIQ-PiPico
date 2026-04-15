from typing import Callable
from typing import Literal

from src.core.enum import PseudoEnum
from src.datasheet import BusType

AVAILABLE_RELATIONS = ("arguments",)


def cast_relation_attr(relation: str) -> tuple[int, ...]:
    """
    Parse a relation string and extract the relation name and IDs.
    Converts a relation string in the format 'relation_name:id1,id2,id3' into a tuple
    of integers representing the related object IDs.

    Args:
        relation (str): A relation string in the format 'relation_name:id1,id2,id3'
            where relation_name is a valid relation key and ids are comma-separated integers.

    Returns:
        tuple[int, ...]: A tuple of integers extracted from the relation string.

    Raises:
        ValueError: If the relation name is not found in AVAILABLE_RELATIONS.
        ValueError: If any ID cannot be converted to an integer.

    Examples:
        >>> cast_relation_attr('devices:1,2,5')
        (1, 2, 5)
        >>> cast_relation_attr('sensors:10')
        (10,)
    """
    rel_name, rel_ids = relation.split(":", 1)
    if rel_name not in AVAILABLE_RELATIONS:
        raise ValueError(f"relation `{rel_name}` is not valid.")
    str_ids = rel_ids.split(",")
    ids = [int(pk) for pk in str_ids]
    return tuple(ids)


def str_to_bool(value: str) -> bool:
    """Convert a string to a boolean value."""
    if value in ("True", "true"):
        return True
    elif value in ("False", "false"):
        return False
    else:
        raise ValueError(f"Cannot convert '{value}' to bool. Expected 'True' or 'False'.")


def int_or_none(value: str) -> int | None:
    """Convert a string to an integer or None."""
    if value.lower() in ("none", "null"):
        return None
    try:
        return int(value)
    except ValueError:
        raise ValueError(f"Cannot convert '{value}' to int or None. Expected an integer or 'None'.")


class ModelType(PseudoEnum):
    """Model types for frame commands."""

    ARGUMENT = "Argument"
    ORDER = "Order"
    PIN = "Pin"


class Pin:
    """
    Represents a physical pin on the device.
    This class defines the structure and properties of a pin, including its pk, bus_choiced and
    associated physical pin numbers.

    Attributes:
        pk (int): Primary key identifier for the pin.
        bus_choiced (str): The type of bus the pin is associated with (e.g., "I2C", "SPI").
        pin (int): A integer representing the physical pin number associated with this pin.
    """

    fields_cfg: tuple[tuple[str, Callable], ...] = (
        ("pk", int),
        ("bus_choiced", BusType.check_value),
        ("pin", int),
    )

    def __init__(self, pk: int, bus_choiced: str, pin: int) -> None:
        self.pk = pk
        self.bus_choiced = bus_choiced
        self.pin = pin


class Argument:
    """
    Represents a command argument with its configuration and metadata.
    This class defines the structure and properties of an argument that can be used
    in command definitions. It includes configuration for parsing arguments from
    various input formats.

    Attributes:
        pk (int): Primary key identifier for the argument.
        slug (str): Unique slug identifier for the argument.
        value_type (str): The expected type of the argument value.
        value_for_pin (bool): Whether this argument is intended for a pin.
        value_for_obj (bool): Whether this argument is intended for an object.
        is_logical_value (bool): Whether this argument represents a logical value.
        fields_cfg (tuple[tuple[str, Callable], ...]): Configuration mapping field names
            to their respective type conversion functions for deserialization.
    """

    fields_cfg: tuple[tuple[str, Callable], ...] = (
        ("pk", int),
        ("slug", str),
        ("value_type", str),
        ("value_for_pin", str_to_bool),
        ("value_for_obj", str_to_bool),
        ("is_logical_value", str_to_bool),
    )

    def __init__(
        self,
        pk: int,
        slug: str,
        value_type: str,
        value_for_pin: bool,
        value_for_obj: bool,
        is_logical_value: bool,
    ) -> None:
        self.pk = pk
        self.slug = slug
        self.value_type = value_type
        self.value_for_pin = value_for_pin
        self.value_for_obj = value_for_obj
        self.is_logical_value = is_logical_value


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
        arguments (tuple[int, ...]): Variable-length tuple of integer arguments
            required for executing the action.
        fields_cfg (tuple[tuple[str, Callable], ...]): Configuration mapping field names
            to their respective cast functions for serialization/deserialization.
    """

    fields_cfg: tuple[tuple[str, Callable], ...] = (
        ("pk", int),
        ("slug", str),
        ("action_type", str),
        ("arguments", cast_relation_attr),
    )

    def __init__(self, pk: int, slug: str, action_type: Literal["get", "set"], arguments: tuple[int, ...]) -> None:
        self.pk = pk
        self.slug = slug
        self.action_type = action_type
        self.arguments = arguments

    def execute(self):
        """Execute the order (e.g : get temp to sensor)"""
