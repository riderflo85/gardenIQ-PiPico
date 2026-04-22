import json
from typing import Callable

from src.datasheet import MP_MACHINE


class Pin:
    """
    Represents a physical pin on the device.
    This class defines the structure and properties of a pin, including its channel_choiced and
    associated physical pin numbers.
    It also determines the appropriate executor class from the Machine library based on the selected channel type.

    Attributes:
        channel_choiced (str): The type of channel the pin is associated with (e.g., "I2C", "SPI").
        pin_number (int): A integer representing the physical pin number associated with this pin.
        initial_configuration (dict): The initial configuration of the pin.

        fields_cfg (tuple[tuple[str, Callable], ...]): Configuration mapping field names
            to their respective cast functions for serialization/deserialization.

    """

    fields_cfg: tuple[tuple[str, Callable], ...] = (
        ("channel_choiced", str),
        ("pin_number", int),
        ("initial_configuration", json.loads),
    )

    def __init__(self, channel_choiced: str, pin_number: int, initial_configuration: dict) -> None:
        self.channel_choiced = channel_choiced
        self.pin_number = pin_number
        self.initial_configuration = initial_configuration

        # Flag to indicate if the pin has been initialized (e.g., set up with the Machine library)
        # If is done, the initial_configuration attribute is no more useful and can be set to None to save memory.
        self.init_done = False

        self.executor = self._setup_machine_pin()

    def _set_done_init(self) -> None:
        """
        Set the initialization flag to True and clear the initial configuration to save memory.
        This method should be called once the pin has been properly initialized with the Machine library.
        """
        self.init_done = True
        self.initial_configuration = None

    def _setup_machine_pin(self) -> object:
        """
        Instantiate and configure a MicroPython machine object from the pre-parsed configuration.

        The configuration dict (already parsed from JSON upstream) is read to resolve the
        target channel class and its constructor arguments via the MP_MACHINE whitelist.
        Only classes and constants explicitly declared in MP_MACHINE are accessible,
        preventing any arbitrary access to the machine module.

        Returns:
            object: An instance of the configured machine class (e.g., machine.Pin, machine.PWM).

        Raises:
            ValueError: If channel_class is not found in MP_MACHINE, attribute_name is missing,
                        the resolved value does not match the expected JSON value,
                        or the referenced module is not authorized by GardenIQ.

        Note:
            - Does nothing if initial_configuration is None or initialization is already done.
            - Sets the initialization flag to True and clears initial_configuration upon success.

        Config data structure example:
            {
                "channel_class": "Pin",
                "arguments": [
                    {
                        "name": "id",
                        "skip_this_arg": false,
                        "value_type": {
                            "is_micropython_class": false,
                            "mp_module_name": "",
                            "mp_class_name": "",
                            "garden_model": "Pin",
                            "attribute_name": "pin_number",
                            "check_with_json_value": true,
                            "use_json_value": true
                        },
                        "value": 3
                    },
                    {
                        "name": "mode",
                        "skip_this_arg": false,
                        "value_type": {
                            "is_micropython_class": true,
                            "mp_module_name": "machine",
                            "mp_class_name": "Pin",
                            "garden_model": "",
                            "attribute_name": "IN",
                            "check_with_json_value": false,
                            "use_json_value": false
                        },
                        "value": ""
                    },
                    {
                        "name": "pull",
                        "skip_this_arg": true,
                        "value_type": {
                            "is_micropython_class": true,
                            "mp_module_name": "machine",
                            "mp_class_name": "Pin",
                            "garden_model": "",
                            "attribute_name": "PULL_UP",
                            "check_with_json_value": false,
                            "use_json_value": false
                        },
                        "value": ""
                    }
                ]
            }
        """

        if self.initial_configuration is None or self.init_done:
            return

        config_data = self.initial_configuration

        channel_class = getattr(MP_MACHINE, config_data["channel_class"], None)

        if not channel_class:
            raise ValueError(f"Invalid channel class: {config_data['channel_class']} for pin {self.pin_number}")

        args_data = {}
        for arg in config_data["arguments"]:
            if arg["skip_this_arg"]:
                continue
            value = None
            val_type = arg["value_type"]
            if val_type["is_micropython_class"]:
                if val_type["mp_module_name"] == "machine":
                    mp_class = getattr(MP_MACHINE, val_type["mp_class_name"])  # can like MP_MACHINE.Pin
                    if attr_name := val_type["attribute_name"]:
                        value = getattr(mp_class, attr_name)  # can like MP_MACHINE.Pin.PULL_UP
                    else:
                        raise ValueError(
                            "Missing attribute_name for micropython class "
                            f"argument in pin config for pin {self.pin_number}"
                        )
                else:
                    raise ValueError(
                        "This module is not authorized by GardenIQ: "
                        f"{val_type['mp_module_name']} for pin {self.pin_number}"
                    )
            else:
                if val_type["garden_model"] == "Pin":
                    if attr_name := val_type["attribute_name"]:
                        value = getattr(self, attr_name)  # can like pin.pin_number
                    else:
                        raise ValueError(
                            f"Missing attribute_name for garden model argument in pin config for pin {self.pin_number}"
                        )
            if val_type["check_with_json_value"]:
                if value is not None and value != arg["value"]:
                    raise ValueError(
                        f"Value mismatch for argument in pin config for pin {self.pin_number}: "
                        f"expected {arg['value']}, got {value}"
                    )
            if val_type["use_json_value"]:
                value = arg["value"]
            args_data[arg["name"]] = value

        executor = channel_class.cls(**args_data)
        self._set_done_init()

        return executor
