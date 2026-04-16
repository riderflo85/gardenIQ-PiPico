import pytest

from src.core.models import Order
from src.protocols.usb.parsers.order import parse_str_order_to_model

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def valid_str_fields():
    """Fixture providing a valid tuple of string values matching Order.fields_cfg order."""
    # pk, slug, action_type, arguments (with braces)
    return ("1", "get_temp", "get", "{arguments:1,2}")


@pytest.fixture
def parsed_order(valid_str_fields):
    """Fixture providing an Order instance parsed from valid string fields."""
    return parse_str_order_to_model(valid_str_fields)


# ---------------------------------------------------------------------------
# Tests – parse_str_order_to_model
# ---------------------------------------------------------------------------


class TestParseStrOrderToModel:
    """Tests for the parse_str_order_to_model parser function."""

    def test_returns_order_instance(self, parsed_order):
        """Test that the function returns an Order instance."""
        # GIVEN valid string field values (fixture)

        # WHEN parse_str_order_to_model is called (fixture)

        # THEN the result is an Order instance
        assert isinstance(parsed_order, Order)

    def test_pk_is_cast_to_int(self, parsed_order):
        """Test that the pk field is correctly cast from str to int."""
        # GIVEN valid string field values with pk='1' (fixture)

        # WHEN the order is parsed (fixture)

        # THEN pk is an int with the expected value
        assert parsed_order.pk == 1
        assert isinstance(parsed_order.pk, int)

    def test_slug_remains_str(self, parsed_order):
        """Test that the slug field stays as a string without extra casting."""
        # GIVEN valid string field values with slug='get_temp' (fixture)

        # WHEN the order is parsed (fixture)

        # THEN slug is the original string
        assert parsed_order.slug == "get_temp"
        assert isinstance(parsed_order.slug, str)

    def test_action_type_remains_str(self, parsed_order):
        """Test that the action_type field stays as a string."""
        # GIVEN valid string field values with action_type='get' (fixture)

        # WHEN the order is parsed (fixture)

        # THEN action_type is the original string
        assert parsed_order.action_type == "get"
        assert isinstance(parsed_order.action_type, str)

    def test_arguments_parsed_from_braces(self, parsed_order):
        """Test that the arguments field is parsed and braces are stripped."""
        # GIVEN valid string field values with arguments='{arguments:1,2}' (fixture)

        # WHEN the order is parsed (fixture)

        # THEN arguments is a tuple of ints with braces removed
        assert parsed_order.arguments == (1, 2)

    def test_arguments_is_tuple(self, parsed_order):
        """Test that the arguments field is stored as a tuple."""
        # GIVEN valid string field values (fixture)

        # WHEN the order is parsed (fixture)

        # THEN arguments is a tuple
        assert isinstance(parsed_order.arguments, tuple)

    def test_all_fields_are_set(self, parsed_order):
        """Test that every field declared in fields_cfg is present on the result."""
        # GIVEN valid string field values (fixture)

        # WHEN the order is parsed (fixture)

        # THEN every field from fields_cfg exists as an attribute
        for field_name, _ in Order.fields_cfg:
            assert hasattr(parsed_order, field_name)

    def test_action_type_set(self):
        """Test parsing an order with action_type 'set'."""
        # GIVEN string field values with action_type='set'
        fields = ("5", "set_valve", "set", "{arguments:3}")

        # WHEN we parse them
        result = parse_str_order_to_model(fields)

        # THEN action_type is 'set' and arguments are correct
        assert result.action_type == "set"
        assert result.arguments == (3,)

    def test_multiple_arguments(self):
        """Test parsing an order with many argument ids."""
        # GIVEN string field values with several argument ids
        fields = ("2", "read_all", "get", "{arguments:10,20,30,40}")

        # WHEN we parse them
        result = parse_str_order_to_model(fields)

        # THEN all argument ids are present
        assert result.arguments == (10, 20, 30, 40)

    def test_sanitize_removes_braces(self):
        """Test that braces are stripped from the relation field before casting."""
        # GIVEN a field value wrapped in braces
        fields = ("1", "cmd", "get", "{arguments:7}")

        # WHEN we parse them
        result = parse_str_order_to_model(fields)

        # THEN the braces are removed and the value is correctly parsed
        assert result.arguments == (7,)

    def test_field_without_braces_is_kept(self):
        """Test that non-brace fields are not altered by sanitize."""
        # GIVEN field values where no field has braces
        fields = ("3", "my_slug", "get", "arguments:5")

        # WHEN we parse them
        result = parse_str_order_to_model(fields)

        # THEN the relation field is still correctly parsed
        assert result.arguments == (5,)
        assert result.slug == "my_slug"

    def test_fields_count_must_match_cfg(self):
        """Test that providing fewer values than fields_cfg raises an IndexError."""
        # GIVEN a tuple with fewer elements than Order.fields_cfg expects
        incomplete_fields = ("1", "slug")

        # WHEN / THEN an IndexError is raised
        with pytest.raises(IndexError):
            parse_str_order_to_model(incomplete_fields)

    def test_non_numeric_pk_raises_value_error(self):
        """Test that a non-numeric pk string raises ValueError during casting."""
        # GIVEN string field values where pk is not a valid int
        bad_fields = ("abc", "slug", "get", "{arguments:1}")

        # WHEN / THEN a ValueError is raised
        with pytest.raises(ValueError):
            parse_str_order_to_model(bad_fields)

    def test_invalid_relation_name_raises_value_error(self):
        """Test that an invalid relation name raises ValueError."""
        # GIVEN a relation field with an unknown relation name
        bad_fields = ("1", "slug", "get", "{unknown:1,2}")

        # WHEN / THEN a ValueError is raised
        with pytest.raises(ValueError, match="relation `unknown` is not valid"):
            parse_str_order_to_model(bad_fields)
