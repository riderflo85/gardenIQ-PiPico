from src.core.models import Argument


def parse_str_arg_to_model(fields_values: tuple[str, ...]) -> Argument:
    """
    fields_values is a tuple string of values to fields.
    The tuple element order define the field to match with tuple[index].
    e.g:
        fields_values = ('1', '-s')
        Argument.fields_name = (('pk', int), ('slug', str))
        fields_values[0] is a value of 'pk' Argument field.
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
