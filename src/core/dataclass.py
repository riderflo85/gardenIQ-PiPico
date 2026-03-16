class FrozenDataclass:
    """
    A base class for creating immutable (frozen) dataclass objects.
    This class enforces immutability by preventing modification or deletion of attributes
    after initialization. Subclasses must define __slots__ to specify allowed fields.

    Attributes:
        __slots__ (tuple): Must be overridden in subclasses to define the fields of the dataclass.
                          Example: __slots__ = ('field1', 'field2')

    Raises:
        AssertionError: If a subclass does not define __slots__.
        AttributeError: If an attempt is made to modify or delete any field after initialization.

    Example:
        >>> class Person(FrozenDataclass):
            __slots__ = ('name', 'age')
        person = Person(name='Alice', age=30)
        person.name = 'Bob'  # Raises AttributeError
        del person.name  # Raises AttributeError
    """

    __slots__ = ()

    def __init__(self, **kwargs):
        assert len(self.__slots__) > 0, (
            "Define __slots__ in your subclass. " "Example: __slots__ = ('field1', 'field2')"
        )

        # Bypass __setattr__ to allow setting attributes during initialization
        for key, value in kwargs.items():
            object.__setattr__(self, key, value)

    def __setattr__(self, name: str, value) -> None:
        raise AttributeError(f"Cannot modify frozen dataclass field '{name}'.")

    def __delattr__(self, name: str) -> None:
        raise AttributeError(f"Cannot delete frozen dataclass field '{name}'.")
