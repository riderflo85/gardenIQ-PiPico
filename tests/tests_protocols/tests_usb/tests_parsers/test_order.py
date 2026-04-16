import pytest

from src.core.models import Order
from src.protocols.usb.parsers.order import parse_str_order_to_model

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def valid_str_fields():
    """Fixture providing a valid tuple of string values matching Order.fields_cfg order."""
    # pk, slug, action_type
    return ("1", "get_temp", "get")


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
        fields = ("5", "set_valve", "set")

        # WHEN we parse them
        result = parse_str_order_to_model(fields)

        # THEN action_type is 'set'
        assert result.action_type == "set"

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
        bad_fields = ("abc", "slug", "get")

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
