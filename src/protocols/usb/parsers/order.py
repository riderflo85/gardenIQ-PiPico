from src.models import Order


def parse_str_order_to_model(fields_values: tuple[str, ...]) -> Order:
    """
    Parse a tuple of string values into an Order model instance.
    This function converts a tuple of string values into an Order object by matching
    each value to the corresponding field defined in Order.fields_cfg.
    Non-string field values are cast to their specified type.

    Args:
        fields_values (tuple[str, ...]): A tuple of string values where the order
            of elements corresponds to the order of fields in Order.fields_cfg.

    Returns:
        Order: An Order instance populated with the parsed and cast field values.

    Example:
        >>> fields_values = ('1', 'get_temp', 'get', '5', '-1', 'False', '')
        >>> order = parse_str_order_to_model(fields_values)
        >>> # Assumes Order.fields_cfg defines pk (int), slug (str), etc.
        >>> order.pk
        1
        >>> order.slug
        'get_temp'
        >>> order.action_type
        'get'
        >>> order.sensor
        5
        >>> order.controller
        -1
        >>> order.is_toggle_ctrl_value
        False
        >>> order.ctrl_value
        ''

    Raises:
        ValueError: If a cast operation fails or field count doesn't match Order.fields_cfg.
        TypeError: If a value cannot be cast to its specified field type.
    """

    data = {}
    for i, f_config in enumerate(Order.fields_cfg):
        field_name = f_config[0]
        cast = f_config[1]
        if cast is str:
            data[field_name] = fields_values[i]
        else:
            data[field_name] = cast(fields_values[i])

    new_order = Order(**data)
    return new_order
