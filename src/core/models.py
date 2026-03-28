from typing import Callable
from typing import Literal

from src.core.enum import PseudoEnum

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


class ModelType(PseudoEnum):
    """Model types for frame commands."""

    ARGUMENT = "Argument"
    ORDER = "Order"


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
        required (bool): Whether this argument is required for command execution.
        is_option (bool): Whether this argument is an optional flag/option.
        fields_cfg (tuple[tuple[str, Callable], ...]): Configuration mapping field names
            to their respective type conversion functions for deserialization.
    """

    fields_cfg: tuple[tuple[str, Callable], ...] = (
        ("pk", int),
        ("slug", str),
        ("value_type", str),
        ("required", str_to_bool),
        ("is_option", str_to_bool),
    )

    def __init__(self, pk: int, slug: str, value_type: str, required: bool, is_option: bool) -> None:
        self.pk = pk
        self.slug = slug
        self.value_type = value_type
        self.required = required
        self.is_option = is_option


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
