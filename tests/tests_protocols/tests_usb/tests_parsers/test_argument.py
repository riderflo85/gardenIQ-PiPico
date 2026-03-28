import pytest

from src.core.models import Argument
from src.protocols.usb.parsers.argument import parse_str_arg_to_model

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def valid_str_fields():
    """Fixture providing a valid tuple of string values matching Argument.fields_cfg order."""
    # pk, slug, value_type, required, is_option
    return ("1", "temperature", "float", "True", "False")


@pytest.fixture
def parsed_argument(valid_str_fields):
    """Fixture providing an Argument instance parsed from valid string fields."""
    return parse_str_arg_to_model(valid_str_fields)


# ---------------------------------------------------------------------------
# Tests – parse_str_arg_to_model
# ---------------------------------------------------------------------------


class TestParseStrArgToModel:
    """Tests for the parse_str_arg_to_model parser function."""

    def test_returns_argument_instance(self, parsed_argument):
        """Test that the function returns an Argument instance."""
        # GIVEN valid string field values (fixture)

        # WHEN parse_str_arg_to_model is called (fixture)

        # THEN the result is an Argument instance
        assert isinstance(parsed_argument, Argument)

    def test_pk_is_cast_to_int(self, parsed_argument):
        """Test that the pk field is correctly cast from str to int."""
        # GIVEN valid string field values with pk='1' (fixture)

        # WHEN the argument is parsed (fixture)

        # THEN pk is an int with the expected value
        assert parsed_argument.pk == 1
        assert isinstance(parsed_argument.pk, int)

    def test_slug_remains_str(self, parsed_argument):
        """Test that the slug field stays as a string without extra casting."""
        # GIVEN valid string field values with slug='temperature' (fixture)

        # WHEN the argument is parsed (fixture)

        # THEN slug is the original string
        assert parsed_argument.slug == "temperature"
        assert isinstance(parsed_argument.slug, str)

    def test_value_type_remains_str(self, parsed_argument):
        """Test that the value_type field stays as a string."""
        # GIVEN valid string field values with value_type='float' (fixture)

        # WHEN the argument is parsed (fixture)

        # THEN value_type is the original string
        assert parsed_argument.value_type == "float"
        assert isinstance(parsed_argument.value_type, str)

    def test_required_is_cast_to_bool(self, parsed_argument):
        """Test that the required field is correctly cast from str to bool."""
        # GIVEN valid string field values with required='True' (fixture)

        # WHEN the argument is parsed (fixture)

        # THEN required is a bool with the expected value
        assert parsed_argument.required is True

    def test_is_option_is_cast_to_bool(self, parsed_argument):
        """Test that the is_option field is correctly cast from str to bool."""
        # GIVEN valid string field values with is_option='False' (fixture)

        # WHEN the argument is parsed (fixture)

        # THEN is_option is a bool with the expected value
        assert parsed_argument.is_option is False

    def test_all_fields_are_set(self, parsed_argument, valid_str_fields):
        """Test that every field declared in fields_cfg is present on the result."""
        # GIVEN valid string field values (fixture)

        # WHEN the argument is parsed (fixture)

        # THEN every field from fields_cfg exists as an attribute
        for field_name, _ in Argument.fields_cfg:
            assert hasattr(parsed_argument, field_name)

    def test_different_pk_value(self):
        """Test parsing with a different pk value."""
        # GIVEN string field values with pk='99'
        fields = ("99", "humidity", "int", "False", "True")

        # WHEN we parse them
        result = parse_str_arg_to_model(fields)

        # THEN pk is correctly cast
        assert result.pk == 99
        assert result.slug == "humidity"
        assert result.is_option is True

    def test_fields_count_must_match_cfg(self):
        """Test that providing fewer values than fields_cfg raises an IndexError."""
        # GIVEN a tuple with fewer elements than Argument.fields_cfg expects
        incomplete_fields = ("1", "temp")

        # WHEN / THEN an IndexError is raised
        with pytest.raises(IndexError):
            parse_str_arg_to_model(incomplete_fields)

    def test_non_numeric_pk_raises_value_error(self):
        """Test that a non-numeric pk string raises ValueError during casting."""
        # GIVEN string field values where pk is not a valid int
        bad_fields = ("abc", "slug", "str", "True", "False")

        # WHEN / THEN a ValueError is raised
        with pytest.raises(ValueError):
            parse_str_arg_to_model(bad_fields)
