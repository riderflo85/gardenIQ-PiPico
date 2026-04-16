from src.core.models import Argument


def parse_str_arg_to_model(fields_values: tuple[str, ...]) -> Argument:
    """
    Parse a tuple of string values into an Argument model instance.
    This function maps string values from a tuple to their corresponding Argument fields,
    casting each value to the appropriate type as defined in Argument.fields_cfg.

    Args:
        fields_values: A tuple of string values to be assigned to Argument fields.
                      The order of elements must match the order of fields defined in
                      Argument.fields_cfg.

    Returns:
        Argument: A new Argument instance populated with the parsed and cast values.

    Example:
        >>> fields_values = ('1', '-s')
        >>> # Assuming Argument.fields_cfg = (('pk', int), ('slug', str))
        >>> arg = parse_str_arg_to_model(fields_values)
        >>> arg.pk
        1
        >>> arg.slug
        '-s'

    Raises:
        ValueError: If a value cannot be cast to its specified type.
        TypeError: If the number of values does not match the number of configured fields.
    """
    data = {}
    for i, f_config in enumerate(Argument.fields_cfg):
        field_name = f_config[0]
        cast = f_config[1]
        if cast is str:
            data[field_name] = fields_values[i]
        else:
            data[field_name] = cast(fields_values[i])

    new_arg = Argument(**data)
    return new_arg
