from src.core.models import Order


def parse_str_order_to_model(fields_values: tuple[str, ...]) -> Order:
    """
    Parse a tuple of string values into an Order model instance.
    This function converts a tuple of string values into an Order object by matching
    each value to the corresponding field defined in Order.fields_cfg.
    String values wrapped in curly braces (e.g., "{model_relations}") are sanitized by removing the braces.
    Non-string field values are cast to their specified type.

    Args:
        fields_values (tuple[str, ...]): A tuple of string values where the order
            of elements corresponds to the order of fields in Order.fields_cfg.
            Values can optionally be wrapped in curly braces for relation fields.

    Returns:
        Order: An Order instance populated with the parsed and cast field values.

    Example:
        >>> fields_values = ('1', 'get_temp', 'get', '{model_relations:1,2}')
        >>> order = parse_str_order_to_model(fields_values)
        >>> # Assumes Order.fields_cfg defines pk (int), slug (str), etc.
        >>> order.pk
        1
        >>> order.model_relations
        'model_relations:1,2'

    Raises:
        ValueError: If a cast operation fails or field count doesn't match Order.fields_cfg.
        TypeError: If a value cannot be cast to its specified field type.
    """

    def sanitize_relation_field(value: str) -> str:
        if value.startswith("{") and value.endswith("}"):
            # remove prefix and suffix
            return value[1:-1]
        else:
            return value

    sanitize_fields_values = [sanitize_relation_field(v) for v in fields_values]
    data = {}
    for i, f_config in enumerate(Order.fields_cfg):
        field_name = f_config[0]
        cast = f_config[1]
        if cast is str:
            data[field_name] = sanitize_fields_values[i]
        else:
            data[field_name] = cast(sanitize_fields_values[i])

    new_order = Order(**data)
    return new_order
