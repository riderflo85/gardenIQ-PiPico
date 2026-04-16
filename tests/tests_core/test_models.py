import pytest

from src.core.models import ModelType
from src.core.models import Order
from src.core.models import str_to_bool

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def order_fields():
    """Fixture providing raw field values for an Order instance."""
    return {
        "pk": 10,
        "slug": "read-temp",
        "action_type": "get",
    }


@pytest.fixture
def order(order_fields):
    """Fixture providing a fully initialised Order instance."""
    return Order(**order_fields)


# ---------------------------------------------------------------------------
# Tests – ModelType
# ---------------------------------------------------------------------------


class TestModelType:
    """Tests for the ModelType pseudo-enum."""

    def test_order_value(self):
        """Test that ORDER has the expected value."""
        # GIVEN the ModelType enum

        # WHEN we access the ORDER member
        value = ModelType.ORDER

        # THEN the value matches
        assert value == "Order"

    def test_iteration_returns_all_members(self):
        """Test that iterating over ModelType yields all members."""
        # GIVEN the ModelType enum

        # WHEN we collect all values via iteration
        values = list(ModelType)

        # THEN only the Order member is present
        assert "Order" in values
        assert len(values) == 1


# ---------------------------------------------------------------------------
# Tests – Order
# ---------------------------------------------------------------------------


class TestOrder:
    """Tests for the Order model."""

    def test_init_sets_all_attributes(self, order, order_fields):
        """Test that the constructor stores every field correctly."""
        # GIVEN an Order built from known fields (fixture)

        # WHEN we inspect each attribute
        # THEN every attribute matches the input
        assert order.pk == order_fields["pk"]
        assert order.slug == order_fields["slug"]
        assert order.action_type == order_fields["action_type"]

    def test_fields_cfg_contains_expected_entries(self):
        """Test that fields_cfg declares the correct field names and casters."""
        # GIVEN the Order class

        # WHEN we read fields_cfg
        field_names = [name for name, _ in Order.fields_cfg]

        # THEN the expected fields are present in order
        assert field_names == ["pk", "slug", "action_type"]

    def test_action_type_get(self):
        """Test that an Order can be created with action_type 'get'."""
        # GIVEN valid parameters with action_type 'get'
        order = Order(pk=1, slug="read", action_type="get")

        # WHEN we read the action_type
        # THEN it equals 'get'
        assert order.action_type == "get"

    def test_action_type_set(self):
        """Test that an Order can be created with action_type 'set'."""
        # GIVEN valid parameters with action_type 'set'
        order = Order(pk=2, slug="write", action_type="set")

        # WHEN we read the action_type
        # THEN it equals 'set'
        assert order.action_type == "set"

    def test_execute_method_exists(self, order):
        """Test that Order instances expose an execute method."""
        # GIVEN an Order instance (fixture)

        # WHEN we check for the execute method
        # THEN it is callable
        assert callable(order.execute)


# ---------------------------------------------------------------------------
# Tests – str_to_bool
# ---------------------------------------------------------------------------


class TestStrToBool:
    """Tests for the str_to_bool helper function."""

    def test_true_string_returns_true(self):
        """Test that 'True' is converted to True."""
        # GIVEN the string 'True'

        # WHEN we convert it
        result = str_to_bool("True")

        # THEN it returns True
        assert result is True

    def test_lowercase_true_returns_true(self):
        """Test that 'true' is converted to True."""
        # GIVEN the string 'true'

        # WHEN we convert it
        result = str_to_bool("true")

        # THEN it returns True
        assert result is True

    def test_false_string_returns_false(self):
        """Test that 'False' is converted to False."""
        # GIVEN the string 'False'

        # WHEN we convert it
        result = str_to_bool("False")

        # THEN it returns False
        assert result is False

    def test_lowercase_false_returns_false(self):
        """Test that 'false' is converted to False."""
        # GIVEN the string 'false'

        # WHEN we convert it
        result = str_to_bool("false")

        # THEN it returns False
        assert result is False

    def test_invalid_string_raises_value_error(self):
        """Test that an invalid string raises ValueError."""
        # GIVEN an invalid string

        # WHEN / THEN a ValueError is raised
        with pytest.raises(ValueError, match="Cannot convert"):
            str_to_bool("yes")

    def test_empty_string_raises_value_error(self):
        """Test that an empty string raises ValueError."""
        # GIVEN an empty string

        # WHEN / THEN a ValueError is raised
        with pytest.raises(ValueError):
            str_to_bool("")

    def test_return_type_is_bool(self):
        """Test that the return type is always bool."""
        # GIVEN valid inputs

        # WHEN we convert them
        # THEN the return type is bool
        assert isinstance(str_to_bool("True"), bool)
        assert isinstance(str_to_bool("False"), bool)
