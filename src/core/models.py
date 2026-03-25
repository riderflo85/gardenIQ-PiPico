from typing import Callable
from typing import Literal

from src.core.enum import PseudoEnum

AVAILABLE_RELATIONS = ("arguments",)


def cast_relation_attr(relation: str) -> tuple[int, ...]:
    """
    relation can like 'relation_name:1,2,5'
    return like (1, 2, 5,)
    """
    rel_name, rel_ids = relation.split(":", 1)
    if rel_name not in AVAILABLE_RELATIONS:
        raise ValueError(f"relation `{rel_name}` is not valid.")
    str_ids = rel_ids.split(",")
    ids = [int(pk) for pk in str_ids]
    return tuple(ids)


class ModelType(PseudoEnum):
    """Model types for frame commands."""

    ARGUMENT = "Argument"
    ORDER = "Order"


class Argument:
    fields_cfg: tuple[tuple[str, Callable], ...] = (
        ("pk", int),
        ("slug", str),
        ("value_type", str),
        ("required", bool),
        ("is_option", bool),
    )

    def __init__(self, pk: int, slug: str, value_type: str, required: bool, is_option: bool) -> None:
        self.pk = pk
        self.slug = slug
        self.value_type = value_type
        self.required = required
        self.is_option = is_option


class Order:
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
