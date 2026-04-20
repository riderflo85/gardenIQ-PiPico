from typing import Callable
from typing import Literal

from src.core.utils import str_to_bool


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
        sensor (int): Physical pin number of the sensor involved in the order.
        controller (int): Physical pin number of the controller involved in the order.
        is_toggle_ctrl_value (bool): Indicates if the control value should be toggled or set to On or Off.
        ctrl_value (str): The value to set for the controller when action_type is "set".

        fields_cfg (tuple[tuple[str, Callable], ...]): Configuration mapping field names
            to their respective cast functions for serialization/deserialization.

    Methods:
        __init__: Initializes an Order instance with the provided attributes.
        _is_trigger_sensor: Determines if the order is a sensor data retrieval action.
        _is_trigger_controller: Determines if the order is a controller action.
        execute: Executes the order (e.g., get temperature from a sensor).

    Raises:
        ValueError: If action_type is not "get" or "set".
    """

    ACT_TYPE_GET = "get"
    ACT_TYPE_SET = "set"
    ACTION_TYPES = (ACT_TYPE_GET, ACT_TYPE_SET)
    EMPTY_CTRL_VALUE = ("", "None", "none", "NULL", "null")

    fields_cfg: tuple[tuple[str, Callable], ...] = (
        ("pk", int),
        ("slug", str),
        ("action_type", str),
        # Value of sensor and controller must be a integer representing
        #   the physical Pin number of the sensor or controller on the microcontroller.
        ("sensor", int),  # If -1 -> no sensor involved in the order (like None value)
        ("controller", int),  # If -1 -> no controller involved in the order (like None value)
        ("is_toggle_ctrl_value", str_to_bool),
        ("ctrl_value", str),
    )

    def __init__(
        self,
        pk: int,
        slug: str,
        action_type: Literal["get", "set"],
        sensor: int,
        controller: int,
        is_toggle_ctrl_value: bool,
        ctrl_value: str,
    ) -> None:
        self.pk = pk
        self.slug = slug
        if action_type not in self.ACTION_TYPES:
            raise ValueError(f"Invalid action_type: {action_type}. Expected one of {self.ACTION_TYPES}.")
        self.action_type = action_type
        self.sensor = sensor
        self.controller = controller
        self.is_toggle_ctrl_value = is_toggle_ctrl_value
        self.ctrl_value = ctrl_value

    def _is_trigger_sensor(self) -> bool:
        """Determine if the order is a sensor data retrieval action."""
        return self.action_type == self.ACT_TYPE_GET and self.sensor >= 0

    def _is_trigger_controller(self) -> bool:
        """Determine if the order is a controller action."""
        return (
            self.action_type == self.ACT_TYPE_SET
            and self.controller >= 0
            and self.ctrl_value not in self.EMPTY_CTRL_VALUE
        )

    def execute(self):
        """Execute the order (e.g : get temp to sensor)"""
