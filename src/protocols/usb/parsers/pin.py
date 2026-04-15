from src.core.models import Pin


def parse_str_pin_to_model(fields_values: tuple[str, ...]) -> Pin:
    """
    Parse a tuple of string values into a Pin model instance.
    This function maps string values from a tuple to their corresponding Pin fields,
    casting each value to the appropriate type as defined in Pin.fields_cfg.

    Args:
        fields_values: A tuple of string values to be assigned to Pin fields.
                      The order of elements must match the order of fields defined in
                      Pin.fields_cfg.

    Returns:
        Pin: An instance of the Pin model with fields populated from the input strings.

    Raises:
        ValueError: If any value cannot be cast to the appropriate type.
    """
    data = {}
    for i, f_config in enumerate(Pin.fields_cfg):
        field_name = f_config[0]
        cast = f_config[1]
        if cast is str:
            data[field_name] = fields_values[i]
        else:
            data[field_name] = cast(fields_values[i])

    new_pin = Pin(**data)
    return new_pin
