import pytest

from src.core.enum import PseudoEnum
from src.core.enum import PseudoEnumMeta


# Fixtures
@pytest.fixture
def simple_numeric_enum():
    """Fixture for a simple enum with numeric values."""

    class SimpleEnum(metaclass=PseudoEnumMeta):
        VALUE1 = 1
        VALUE2 = 2

    return SimpleEnum


@pytest.fixture
def enum_with_private_attributes():
    """Fixture for an enum with public and private attributes."""

    class TestEnum(metaclass=PseudoEnumMeta):
        VALUE1 = 1
        VALUE2 = 2
        _PRIVATE = 3
        __DOUBLE_PRIVATE = 4

    return TestEnum


@pytest.fixture
def enum_with_methods():
    """Fixture for an enum with methods."""

    class TestEnum(metaclass=PseudoEnumMeta):
        VALUE1 = 1
        VALUE2 = 2

        def regular_method(self):
            pass

        @classmethod
        def class_method(cls):
            pass

    return TestEnum


@pytest.fixture
def string_status_enum():
    """Fixture for a status enum with string values."""

    class StatusEnum(PseudoEnum):
        ACTIVE = "ACTIVE"
        INACTIVE = "INACTIVE"
        PENDING = "PENDING"

    return StatusEnum


@pytest.fixture
def numeric_pseudoenum():
    """Fixture for a PseudoEnum with numeric values."""

    class NumericEnum(PseudoEnum):
        ONE = 1
        TWO = 2
        THREE = 3

    return NumericEnum


@pytest.fixture
def special_chars_enum():
    """Fixture for an enum with special characters."""

    class SpecialEnum(PseudoEnum):
        VALUE_ONE = "VALUE-ONE"
        VALUE_TWO = "VALUE_TWO"

    return SpecialEnum


@pytest.fixture
def mixed_types_enum():
    """Fixture for an enum with mixed value types."""

    class MixedEnum(PseudoEnum):
        STRING_VAL = "string"
        INT_VAL = 42
        FLOAT_VAL = 3.14
        BOOL_VAL = True

    return MixedEnum


class TestPseudoEnumMeta:
    """Tests for the PseudoEnumMeta metaclass."""

    def test_metaclass_creates_iterable_class(self, simple_numeric_enum):
        """Test that a class using PseudoEnumMeta is iterable."""
        # GIVEN: An enum class created with PseudoEnumMeta (from fixture)

        # WHEN: We check if the class has __iter__ method
        has_iter = hasattr(simple_numeric_enum, "__iter__")

        # THEN: The class should be iterable
        assert has_iter

    def test_iteration_returns_only_public_attributes(self, enum_with_private_attributes):
        """Test that iteration only returns public non-callable attributes."""
        # GIVEN: An enum with public and private attributes (from fixture)

        # WHEN: We iterate over the enum
        values = list(enum_with_private_attributes)

        # THEN: Only public attributes should be returned
        assert values == [1, 2]
        assert 3 not in values
        assert 4 not in values

    def test_iteration_excludes_methods(self, enum_with_methods):
        """Test that iteration excludes callable methods."""
        # GIVEN: An enum with values and methods (from fixture)

        # WHEN: We iterate over the enum
        values = list(enum_with_methods)

        # THEN: Only values should be returned, not methods
        assert values == [1, 2]
        assert len(values) == 2

    def test_members_cache_is_created(self, simple_numeric_enum):
        """Test that _members cache is created after first iteration."""
        # GIVEN: An enum that hasn't been iterated yet

        # WHEN: We iterate over it for the first time
        list(simple_numeric_enum)

        # THEN: The _members cache should be created with correct values
        assert hasattr(simple_numeric_enum, "_members")
        assert simple_numeric_enum._members == [1, 2]

    def test_members_cache_is_reused(self, simple_numeric_enum):
        """Test that subsequent iterations use the cached _members."""
        # GIVEN: An enum that has been iterated once
        first_result = list(simple_numeric_enum)
        cached_members = simple_numeric_enum._members

        # WHEN: We iterate over it again
        second_result = list(simple_numeric_enum)

        # THEN: The same cache should be reused
        assert first_result == second_result
        assert simple_numeric_enum._members is cached_members

    def test_iteration_with_string_values(self, string_status_enum):
        """Test that iteration works with string enum values."""
        # GIVEN: An enum with string values (from fixture)

        # WHEN: We iterate over the enum
        values = list(string_status_enum)

        # THEN: All string values should be returned in order
        assert values == ["ACTIVE", "INACTIVE", "PENDING"]

    def test_empty_enum_returns_empty_list(self):
        """Test that an enum with no values returns empty list."""

        # GIVEN: An empty enum class
        class EmptyEnum(metaclass=PseudoEnumMeta):
            pass

        # WHEN: We iterate over the empty enum
        values = list(EmptyEnum)

        # THEN: An empty list should be returned
        assert values == []


class TestPseudoEnum:
    """Tests for the PseudoEnum class."""

    def test_pseudoenum_is_iterable(self):
        """Test that PseudoEnum subclasses are iterable."""

        # GIVEN: A PseudoEnum subclass
        class MyEnum(PseudoEnum):
            VALUE1 = 1
            VALUE2 = 2

        # WHEN: We check if it's iterable and iterate over it
        has_iter = hasattr(MyEnum, "__iter__")
        values = list(MyEnum)

        # THEN: It should be iterable and return correct values
        assert has_iter
        assert values == [1, 2]

    def test_from_string_finds_matching_value(self, string_status_enum):
        """Test that from_string returns the matching enum member."""
        # GIVEN: A status enum with string values (from fixture)

        # WHEN: We call from_string with a lowercase string
        result = string_status_enum.from_string("active")

        # THEN: It should return the matching uppercase value
        assert result == "ACTIVE"

    def test_from_string_is_case_insensitive(self, string_status_enum):
        """Test that from_string converts to uppercase for comparison."""
        # GIVEN: A status enum with uppercase values (from fixture)

        # WHEN: We call from_string with different case variations
        result_lower = string_status_enum.from_string("active")
        result_title = string_status_enum.from_string("Active")
        result_upper = string_status_enum.from_string("ACTIVE")
        result_mixed = string_status_enum.from_string("AcTiVe")

        # THEN: All variations should return the same uppercase value
        assert result_lower == "ACTIVE"
        assert result_title == "ACTIVE"
        assert result_upper == "ACTIVE"
        assert result_mixed == "ACTIVE"

    def test_from_string_returns_none_for_invalid_value(self, string_status_enum):
        """Test that from_string returns None for non-existent values."""
        # GIVEN: A status enum with defined values (from fixture)

        # WHEN: We call from_string with an invalid value
        result = string_status_enum.from_string("invalid")

        # THEN: None should be returned
        assert result is None

    def test_from_string_with_numeric_values(self, numeric_pseudoenum):
        """Test that from_string works with numeric enum values."""
        # GIVEN: An enum with numeric values (from fixture)

        # WHEN: We try to find a numeric value as string
        result = numeric_pseudoenum.from_string("1")

        # THEN: It should return None (string "1" != integer 1)
        assert result is None

    def test_from_string_with_empty_string(self):
        """Test that from_string handles empty strings."""

        # GIVEN: An enum with an empty string value
        class StatusEnum(PseudoEnum):
            ACTIVE = "ACTIVE"
            EMPTY = ""

        # WHEN: We call from_string with an empty string
        result = StatusEnum.from_string("")

        # THEN: It should return the empty string value
        assert result == ""

    def test_from_string_with_special_characters(self, special_chars_enum):
        """Test that from_string handles special characters."""
        # GIVEN: An enum with special characters in values (from fixture)

        # WHEN: We call from_string with a lowercase value containing special chars
        result = special_chars_enum.from_string("value-one")

        # THEN: It should return the matching uppercase value with special chars
        assert result == "VALUE-ONE"

    def test_multiple_enums_dont_share_cache(self):
        """Test that different enum classes have separate member caches."""

        # GIVEN: Two different enum classes
        class Enum1(PseudoEnum):
            A = "A"
            B = "B"

        class Enum2(PseudoEnum):
            X = "X"
            Y = "Y"

        # WHEN: We iterate over both enums
        list(Enum1)
        list(Enum2)

        # THEN: Each should have its own separate cache
        assert Enum1._members == ["A", "B"]
        assert Enum2._members == ["X", "Y"]

    def test_enum_with_mixed_types(self, mixed_types_enum):
        """Test enum with different value types."""
        # GIVEN: An enum with mixed value types (from fixture)

        # WHEN: We iterate over the enum
        values = list(mixed_types_enum)

        # THEN: All values of different types should be present
        assert "string" in values
        assert 42 in values
        assert 3.14 in values
        assert True in values
        assert len(values) == 4

    def test_from_string_preserves_original_value_type(self):
        """Test that from_string returns the original value, not converted."""

        # GIVEN: An enum with string values
        class StatusEnum(PseudoEnum):
            ACTIVE = "ACTIVE"
            CODE_42 = "CODE_42"

        # WHEN: We call from_string with a lowercase string
        result = StatusEnum.from_string("active")

        # THEN: It should return the original string value with correct type
        assert result == "ACTIVE"
        assert isinstance(result, str)
