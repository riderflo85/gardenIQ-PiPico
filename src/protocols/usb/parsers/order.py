from src.core.models import Order


def parse_str_order_to_model(fields_values: tuple[str, ...]) -> Order:
    """
    fields_values is a tuple string of values to fields.
    The tuple element order define the field to match with tuple[index].
    e.g:
        fields_values = ('1', 'get_temp', 'get', '{arguments:1,2}')
        Order.fields_name = (('pk', int), ('slug', str))
        fields_values[0] is a value of 'pk' Order field.
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
