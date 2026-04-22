from src.datasheet import AVAILABLE_CHANNELS
from src.datasheet import InvalidChannelError
from src.datasheet import allowed_pins
from src.models import Pin


def validate_channel(chan: str) -> bool:
    if chan not in AVAILABLE_CHANNELS:
        raise InvalidChannelError(chan)
    return True


def validate_pin(pin_num: int, chan: str) -> bool:
    if pin_num not in allowed_pins.get_pins_by_channel_type(chan):
        raise ValueError(f"Pin number {pin_num} is not valid for channel type '{chan}'.")
    return True


def parse_str_pin_to_model(fields_values: tuple[str, ...]) -> Pin:
    """
    Parse a tuple of raw string values into a validated Pin model instance.

    Each value is cast to the type defined by Pin.fields_cfg. Once all fields
    are cast, the channel is validated against AVAILABLE_CHANNELS and the pin
    number is checked against the allowed pins for that channel type.
    Only then is the Pin instance created.

    Args:
        fields_values (tuple[str, ...]): Raw string values in the same order as
            the fields declared in Pin.fields_cfg.

    Returns:
        Pin: A fully populated and validated Pin instance.

    Raises:
        ValueError: If the number of values does not match Pin.fields_cfg,
            or if a value cannot be cast to its expected type,
            or if the pin number is not allowed for the given channel type.
        InvalidChannelError: If the channel name is not in AVAILABLE_CHANNELS.
    """
    pin_fields = Pin.fields_cfg
    pin_fields_count = len(pin_fields)

    if len(fields_values) != pin_fields_count:
        raise ValueError(f"Expected {pin_fields_count} fields, but got {len(fields_values)}. Fields: {fields_values}")

    field_values_casted = {}
    for (field_name, field_type), value in zip(Pin.fields_cfg, fields_values):
        if field_type is str:
            field_values_casted[field_name] = value
        else:
            field_values_casted[field_name] = field_type(value)

    validate_channel(field_values_casted["channel_choiced"])
    validate_pin(field_values_casted["pin_number"], field_values_casted["channel_choiced"])

    new_pin = Pin(**field_values_casted)
    return new_pin
