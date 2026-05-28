def str_to_bool(value: str) -> bool:
    """Convert a string to a boolean value."""
    if value in ("True", "true"):
        return True
    elif value in ("False", "false"):
        return False
    else:
        raise ValueError(f"Cannot convert '{value}' to bool. Expected 'True' or 'False'.")


def format_error(error_type: str, error_msg: str) -> str:
    """Replace the spaces string in the error message with underscores `_`,
    because the frame parsing function splits the frame string using space to seperate blocks.
    """
    return f"{error_type}::{error_msg.replace(" ", "_")}"
