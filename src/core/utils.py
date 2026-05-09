def str_to_bool(value: str) -> bool:
    """Convert a string to a boolean value."""
    if value in ("True", "true"):
        return True
    elif value in ("False", "false"):
        return False
    else:
        raise ValueError(f"Cannot convert '{value}' to bool. Expected 'True' or 'False'.")
