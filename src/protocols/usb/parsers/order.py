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
        ValueError: If any of the string values cannot be cast to the expected type
            defined in Order.fields_cfg, or if the number of fields does not match.
    """
    order_fields = Order.fields_cfg
    order_fields_count = len(order_fields)

    if len(fields_values) != order_fields_count:
        raise ValueError(f"Expected {order_fields_count} fields, but got {len(fields_values)}. Fields: {fields_values}")

    field_values_casted = {}
    for (field_name, field_type), value in zip(order_fields, fields_values):
        if field_type is str:
            field_values_casted[field_name] = value
        else:
            field_values_casted[field_name] = field_type(value)

    new_order = Order(**field_values_casted)
    return new_order
