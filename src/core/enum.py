class PseudoEnumMeta(type):
    """
    Metaclass for creating pseudo-enum classes.

    This metaclass enables iteration over class attributes that are considered enum members.
    During iteration, it collects all class attributes that:
        - It's not a _members array,
        - Do not start with double underscores,
        - Do not start with single underscores,
        - Are not classmethods,
        - Are not callable.

    The collected members are cached in the `_members` attribute for efficient repeated iteration.

    Usage:
        class MyEnum(metaclass=PseudoEnumMeta):
            VALUE1 = 1
            VALUE2 = 2

        for value in MyEnum:
            print(value)  # Outputs: 1, then 2
    """

    def __iter__(cls):
        # Create _members to store attributes in cache.
        if not hasattr(cls, "_members"):
            cls._members = []
            for k, v in cls.__dict__.items():
                if (
                    not k == "_members"
                    and not k.startswith("__")
                    and not k.startswith("_")
                    and not isinstance(v, classmethod)
                    and not callable(v)
                ):
                    cls._members.append(v)
        return iter(cls._members)


class PseudoEnum(metaclass=PseudoEnumMeta):
    """Does not use enum.Enum to Python standart librairie because it's not available in MicroPython :("""

    @classmethod
    def from_string(cls, value: str) -> str | None:
        """
        Converts a string to its corresponding enum member if it exists.

        Args:
            value (str): The string representation of the enum member.

        Returns:
            str | None: The matching enum member if found, otherwise None.
        """
        value = value.upper()
        for member in cls:
            if member == value:
                return member
        return None
