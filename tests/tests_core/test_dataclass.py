import pytest

from src.core.dataclass import FrozenDataclass

# ---------------------------------------------------------------------------
# Helper subclasses used across tests
# ---------------------------------------------------------------------------


class Point(FrozenDataclass):
    """A simple frozen dataclass with two numeric fields."""

    __slots__ = ("x", "y")


class Person(FrozenDataclass):
    """A frozen dataclass with mixed-type fields."""

    __slots__ = ("name", "age")


class SingleField(FrozenDataclass):
    """A frozen dataclass with a single field."""

    __slots__ = ("value",)


# ---------------------------------------------------------------------------
# Tests – instantiation
# ---------------------------------------------------------------------------


class TestFrozenDataclassInstantiation:
    """Tests verifying correct object creation."""

    def test_instantiation_with_valid_kwargs(self):
        """Verify that a subclass can be instantiated with valid keyword arguments."""
        # GIVEN: A FrozenDataclass subclass defining two slots
        # WHEN: Creating an instance with matching keyword arguments
        point = Point(x=1, y=2)

        # THEN: The instance is created successfully
        assert isinstance(point, FrozenDataclass)

    def test_field_values_are_stored_correctly(self):
        """Verify that field values are accessible and correct after instantiation."""
        # GIVEN: A FrozenDataclass subclass with fields 'name' and 'age'
        # WHEN: Creating an instance with specific values
        person = Person(name="Alice", age=30)

        # THEN: The stored values match what was provided
        assert person.name == "Alice"
        assert person.age == 30

    def test_instantiation_with_single_field(self):
        """Verify that a subclass with a single slot can be instantiated."""
        # GIVEN: A FrozenDataclass subclass defining exactly one slot
        # WHEN: Creating an instance with one keyword argument
        obj = SingleField(value=42)

        # THEN: The single field is stored correctly
        assert obj.value == 42

    def test_instantiation_with_none_value(self):
        """Verify that None is a valid field value."""
        # GIVEN: A FrozenDataclass subclass with a 'value' slot
        # WHEN: Creating an instance with None as the value
        obj = SingleField(value=None)

        # THEN: The field stores None without error
        assert obj.value is None

    def test_instantiation_with_various_types(self):
        """Verify that fields can hold any Python type."""
        # GIVEN: A FrozenDataclass subclass with two slots
        # WHEN: Creating an instance with mixed types (list, dict)
        point = Point(x=[1, 2, 3], y={"key": "val"})

        # THEN: The field values are stored as-is
        assert point.x == [1, 2, 3]
        assert point.y == {"key": "val"}


# ---------------------------------------------------------------------------
# Tests – immutability (attribute modification)
# ---------------------------------------------------------------------------


class TestFrozenDataclassImmutability:
    """Tests verifying that frozen instances cannot be mutated."""

    def test_setattr_raises_attribute_error(self):
        """Verify that modifying a field after instantiation raises AttributeError."""
        # GIVEN: An already instantiated frozen object
        point = Point(x=0, y=0)

        # WHEN: Attempting to overwrite an existing field
        # THEN: An AttributeError is raised
        with pytest.raises(AttributeError):
            point.x = 99

    def test_setattr_error_message_contains_field_name(self):
        """Verify that the AttributeError message references the field name."""
        # GIVEN: An already instantiated frozen object
        person = Person(name="Bob", age=25)

        # WHEN: Attempting to modify the 'name' field
        # THEN: The error message mentions the field name
        with pytest.raises(AttributeError, match="name"):
            person.name = "Charlie"

    def test_setattr_raises_for_new_attribute(self):
        """Verify that adding a new attribute to a frozen instance raises AttributeError."""
        # GIVEN: An already instantiated frozen object
        point = Point(x=1, y=2)

        # WHEN: Attempting to set a brand-new attribute not in __slots__
        # THEN: An AttributeError is raised
        with pytest.raises(AttributeError):
            point.z = 3

    def test_multiple_fields_are_all_immutable(self):
        """Verify that every field on a multi-field instance is immutable."""
        # GIVEN: A frozen instance with two fields
        person = Person(name="Alice", age=30)

        # WHEN / THEN: Both fields raise AttributeError when modified
        with pytest.raises(AttributeError):
            person.name = "Eve"

        with pytest.raises(AttributeError):
            person.age = 99


# ---------------------------------------------------------------------------
# Tests – immutability (attribute deletion)
# ---------------------------------------------------------------------------


class TestFrozenDataclassDeletion:
    """Tests verifying that frozen instances cannot have attributes deleted."""

    def test_delattr_raises_attribute_error(self):
        """Verify that deleting a field raises AttributeError."""
        # GIVEN: An already instantiated frozen object
        point = Point(x=5, y=10)

        # WHEN: Attempting to delete an existing field
        # THEN: An AttributeError is raised
        with pytest.raises(AttributeError):
            del point.x

    def test_delattr_error_message_contains_field_name(self):
        """Verify that the AttributeError message references the field name."""
        # GIVEN: An already instantiated frozen object
        person = Person(name="Alice", age=30)

        # WHEN: Attempting to delete the 'age' field
        # THEN: The error message mentions the field name
        with pytest.raises(AttributeError, match="age"):
            del person.age


# ---------------------------------------------------------------------------
# Tests – subclass contract enforcement
# ---------------------------------------------------------------------------


class TestFrozenDataclassSlotContract:
    """Tests verifying that subclasses must define __slots__."""

    def test_base_class_instantiation_raises_assertion_error(self):
        """Verify that instantiating FrozenDataclass directly raises AssertionError."""
        # GIVEN: The FrozenDataclass base class with empty __slots__
        # WHEN: Attempting to instantiate it directly with a keyword argument
        # THEN: An AssertionError is raised because __slots__ is empty
        with pytest.raises(AssertionError):
            FrozenDataclass(field="value")

    def test_subclass_without_slots_raises_assertion_error(self):
        """Verify that a subclass that does not define __slots__ raises AssertionError."""

        # GIVEN: A subclass that omits __slots__
        class NoSlots(FrozenDataclass):
            pass

        # WHEN: Attempting to instantiate the subclass
        # THEN: An AssertionError is raised
        with pytest.raises(AssertionError):
            NoSlots(field="value")

    def test_assertion_error_message_is_informative(self):
        """Verify that the AssertionError message provides guidance on how to fix the issue."""
        # GIVEN: The FrozenDataclass base class with empty __slots__
        # WHEN: Attempting to instantiate it directly
        # THEN: The error message mentions __slots__
        with pytest.raises(AssertionError, match="__slots__"):
            FrozenDataclass(field="value")
