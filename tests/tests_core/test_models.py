import pytest

from src.core.models import AVAILABLE_RELATIONS
from src.core.models import Argument
from src.core.models import ModelType
from src.core.models import Order
from src.core.models import cast_relation_attr
from src.core.models import str_to_bool

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def argument_fields():
    """Fixture providing raw field values for an Argument instance."""
    return {
        "pk": 1,
        "slug": "temperature",
        "value_type": "float",
        "required": True,
        "is_option": False,
    }


@pytest.fixture
def argument(argument_fields):
    """Fixture providing a fully initialised Argument instance."""
    return Argument(**argument_fields)


@pytest.fixture
def order_fields():
    """Fixture providing raw field values for an Order instance."""
    return {
        "pk": 10,
        "slug": "read-temp",
        "action_type": "get",
        "arguments": (1, 2, 5),
    }


@pytest.fixture
def order(order_fields):
    """Fixture providing a fully initialised Order instance."""
    return Order(**order_fields)


# ---------------------------------------------------------------------------
# Tests – cast_relation_attr
# ---------------------------------------------------------------------------


class TestCastRelationAttr:
    """Tests for the cast_relation_attr helper function."""

    def test_valid_relation_returns_tuple_of_ints(self):
        """Test that a well-formed relation string yields the expected int tuple."""
        # GIVEN a valid relation string with known ids
        relation = "arguments:1,2,5"

        # WHEN we cast the relation
        result = cast_relation_attr(relation)

        # THEN a tuple of ints is returned
        assert result == (1, 2, 5)

    def test_single_id_returns_single_element_tuple(self):
        """Test that a relation with a single id returns a one-element tuple."""
        # GIVEN a relation string with one id
        relation = "arguments:42"

        # WHEN we cast the relation
        result = cast_relation_attr(relation)

        # THEN a single-element tuple is returned
        assert result == (42,)

    def test_invalid_relation_name_raises_value_error(self):
        """Test that an unknown relation name raises ValueError."""
        # GIVEN a relation string with an invalid name
        relation = "unknown:1,2"

        # WHEN / THEN a ValueError is raised
        with pytest.raises(ValueError, match="relation `unknown` is not valid"):
            cast_relation_attr(relation)

    def test_non_numeric_id_raises_value_error(self):
        """Test that non-integer ids raise ValueError."""
        # GIVEN a relation string with a non-numeric id
        relation = "arguments:a,b"

        # WHEN / THEN a ValueError is raised
        with pytest.raises(ValueError):
            cast_relation_attr(relation)

    def test_result_is_tuple_type(self):
        """Test that the return value is specifically a tuple."""
        # GIVEN a valid relation string
        relation = "arguments:3"

        # WHEN we cast the relation
        result = cast_relation_attr(relation)

        # THEN the result type is tuple
        assert isinstance(result, tuple)


# ---------------------------------------------------------------------------
# Tests – ModelType
# ---------------------------------------------------------------------------


class TestModelType:
    """Tests for the ModelType pseudo-enum."""

    def test_argument_value(self):
        """Test that ARGUMENT has the expected value."""
        # GIVEN the ModelType enum

        # WHEN we access the ARGUMENT member
        value = ModelType.ARGUMENT

        # THEN the value matches
        assert value == "Argument"

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

        # THEN both members are present
        assert "Argument" in values
        assert "Order" in values
        assert len(values) == 2


# ---------------------------------------------------------------------------
# Tests – Argument
# ---------------------------------------------------------------------------


class TestArgument:
    """Tests for the Argument model."""

    def test_init_sets_all_attributes(self, argument, argument_fields):
        """Test that the constructor stores every field correctly."""
        # GIVEN an Argument built from known fields (fixture)

        # WHEN we inspect each attribute
        # THEN every attribute matches the input
        assert argument.pk == argument_fields["pk"]
        assert argument.slug == argument_fields["slug"]
        assert argument.value_type == argument_fields["value_type"]
        assert argument.required == argument_fields["required"]
        assert argument.is_option == argument_fields["is_option"]

    def test_fields_cfg_contains_expected_entries(self):
        """Test that fields_cfg declares the correct field names and casters."""
        # GIVEN the Argument class

        # WHEN we read fields_cfg
        field_names = [name for name, _ in Argument.fields_cfg]

        # THEN the expected fields are present in order
        assert field_names == ["pk", "slug", "value_type", "required", "is_option"]

    def test_fields_cfg_casters_types(self):
        """Test that each caster in fields_cfg is the expected callable."""
        # GIVEN the Argument class

        # WHEN we extract the casters
        casters = {name: caster for name, caster in Argument.fields_cfg}

        # THEN each caster matches
        assert casters["pk"] is int
        assert casters["slug"] is str
        assert casters["value_type"] is str
        assert casters["required"] is str_to_bool
        assert casters["is_option"] is str_to_bool


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
        assert order.arguments == order_fields["arguments"]

    def test_fields_cfg_contains_expected_entries(self):
        """Test that fields_cfg declares the correct field names and casters."""
        # GIVEN the Order class

        # WHEN we read fields_cfg
        field_names = [name for name, _ in Order.fields_cfg]

        # THEN the expected fields are present in order
        assert field_names == ["pk", "slug", "action_type", "arguments"]

    def test_fields_cfg_arguments_caster_is_cast_relation_attr(self):
        """Test that the arguments field uses cast_relation_attr as its caster."""
        # GIVEN the Order class

        # WHEN we extract the caster for 'arguments'
        casters = {name: caster for name, caster in Order.fields_cfg}

        # THEN it points to cast_relation_attr
        assert casters["arguments"] is cast_relation_attr

    def test_action_type_get(self):
        """Test that an Order can be created with action_type 'get'."""
        # GIVEN valid parameters with action_type 'get'
        order = Order(pk=1, slug="read", action_type="get", arguments=(1,))

        # WHEN we read the action_type
        # THEN it equals 'get'
        assert order.action_type == "get"

    def test_action_type_set(self):
        """Test that an Order can be created with action_type 'set'."""
        # GIVEN valid parameters with action_type 'set'
        order = Order(pk=2, slug="write", action_type="set", arguments=(3, 4))

        # WHEN we read the action_type
        # THEN it equals 'set'
        assert order.action_type == "set"

    def test_execute_method_exists(self, order):
        """Test that Order instances expose an execute method."""
        # GIVEN an Order instance (fixture)

        # WHEN we check for the execute method
        # THEN it is callable
        assert callable(order.execute)

    def test_arguments_stored_as_tuple(self, order):
        """Test that arguments are stored as a tuple."""
        # GIVEN an Order instance (fixture)

        # WHEN we check the type of arguments
        # THEN it is a tuple
        assert isinstance(order.arguments, tuple)


# ---------------------------------------------------------------------------
# Tests – AVAILABLE_RELATIONS constant
# ---------------------------------------------------------------------------


class TestAvailableRelations:
    """Tests for the AVAILABLE_RELATIONS module-level constant."""

    def test_contains_arguments(self):
        """Test that 'arguments' is in AVAILABLE_RELATIONS."""
        # GIVEN the module constant

        # WHEN we check membership
        # THEN 'arguments' is present
        assert "arguments" in AVAILABLE_RELATIONS

    def test_is_tuple(self):
        """Test that AVAILABLE_RELATIONS is a tuple."""
        # GIVEN the module constant

        # WHEN we check its type
        # THEN it is a tuple
        assert isinstance(AVAILABLE_RELATIONS, tuple)


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

        # WHEN we check membership
        # THEN 'arguments' is present
        assert "arguments" in AVAILABLE_RELATIONS

    def test_is_tuple(self):
        """Test that AVAILABLE_RELATIONS is a tuple."""
        # GIVEN the module constant

        # WHEN we check its type
        # THEN it is a tuple
        assert isinstance(AVAILABLE_RELATIONS, tuple)
