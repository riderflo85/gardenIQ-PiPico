import json

import pytest

from src.core.utils import str_to_bool
from src.models import ModelType
from src.models import Order
from src.models import Pin

# ---------------------------------------------------------------------------
# Test data
# ---------------------------------------------------------------------------

# initial_configuration dict for a digital pin GP3 (IN mode).
_PIN_INITIAL_CFG = {
    "channel_class": "Pin",
    "arguments": [
        {
            "name": "id",
            "skip_this_arg": False,
            "value_type": {
                "is_micropython_class": False,
                "mp_module_name": "",
                "mp_class_name": "",
                "garden_model": "Pin",
                "attribute_name": "pin_number",
                "check_with_json_value": True,
                "use_json_value": True,
            },
            "value": 3,
        },
        {
            "name": "mode",
            "skip_this_arg": False,
            "value_type": {
                "is_micropython_class": True,
                "mp_module_name": "machine",
                "mp_class_name": "Pin",
                "garden_model": "",
                "attribute_name": "IN",
                "check_with_json_value": False,
                "use_json_value": False,
            },
            "value": "",
        },
    ],
}


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
        "sensor": 4,
        "controller": -1,
        "is_toggle_ctrl_value": False,
        "ctrl_value": "",
    }


@pytest.fixture
def order(order_fields):
    """Fixture providing a fully initialised Order instance."""
    return Order(**order_fields)


@pytest.fixture
def pin_fields():
    """Fixture providing raw field values for a Pin instance."""
    return {
        "channel_choiced": "digit",
        "pin_number": 3,
        "initial_configuration": _PIN_INITIAL_CFG,
    }


@pytest.fixture
def pin(pin_fields):
    """Fixture providing a fully initialised Pin instance."""
    return Pin(**pin_fields)


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

    def test_pin_value(self):
        """Test that PIN has the expected value."""
        # GIVEN the ModelType enum

        # WHEN we access the PIN member
        value = ModelType.PIN

        # THEN the value matches
        assert value == "Pin"

    def test_iteration_returns_all_members(self):
        """Test that iterating over ModelType yields all members."""
        # GIVEN the ModelType enum

        # WHEN we collect all values via iteration
        values = list(ModelType)

        # THEN both Order and Pin members are present
        assert "Order" in values
        assert "Pin" in values
        assert len(values) == 2


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
        assert order.sensor == order_fields["sensor"]
        assert order.controller == order_fields["controller"]
        assert order.is_toggle_ctrl_value == order_fields["is_toggle_ctrl_value"]
        assert order.ctrl_value == order_fields["ctrl_value"]

    def test_fields_cfg_contains_expected_entries(self):
        """Test that fields_cfg declares the correct field names and casters."""
        # GIVEN the Order class

        # WHEN we read fields_cfg
        field_names = [name for name, _ in Order.fields_cfg]

        # THEN the expected fields are present in order
        assert field_names == [
            "pk",
            "slug",
            "action_type",
            "sensor",
            "controller",
            "is_toggle_ctrl_value",
            "ctrl_value",
        ]

    def test_action_type_get(self):
        """Test that an Order can be created with action_type 'get'."""
        # GIVEN valid parameters with action_type 'get'
        order = Order(
            pk=1, slug="read", action_type="get", sensor=4, controller=-1, is_toggle_ctrl_value=False, ctrl_value=""
        )

        # WHEN we read the action_type
        # THEN it equals 'get'
        assert order.action_type == "get"

    def test_action_type_set(self):
        """Test that an Order can be created with action_type 'set'."""
        # GIVEN valid parameters with action_type 'set'
        order = Order(
            pk=2, slug="write", action_type="set", sensor=-1, controller=5, is_toggle_ctrl_value=False, ctrl_value="on"
        )

        # WHEN we read the action_type
        # THEN it equals 'set'
        assert order.action_type == "set"

    def test_invalid_action_type_raises_value_error(self):
        """Test that an invalid action_type raises ValueError."""
        # GIVEN an invalid action_type

        # WHEN / THEN a ValueError is raised
        with pytest.raises(ValueError, match="Invalid action_type"):
            Order(
                pk=1,
                slug="bad",
                action_type="delete",  # type: ignore
                sensor=0,
                controller=0,
                is_toggle_ctrl_value=False,
                ctrl_value="",
            )

    def test_class_constants(self):
        """Test that class-level constants are correctly defined."""
        # GIVEN the Order class

        # WHEN we access the constants
        # THEN they have the expected values
        assert Order.ACT_TYPE_GET == "get"
        assert Order.ACT_TYPE_SET == "set"
        assert Order.ACTION_TYPES == ("get", "set")
        assert Order.EMPTY_CTRL_VALUE == ("", "None", "none", "NULL", "null")

    def test_execute_method_exists(self, order):
        """Test that Order instances expose an execute method."""
        # GIVEN an Order instance (fixture)

        # WHEN we check for the execute method
        # THEN it is callable
        assert callable(order.execute)

    # -- _is_trigger_sensor ------------------------------------------------

    def test_is_trigger_sensor_true_when_get_and_sensor_positive(self):
        """Test _is_trigger_sensor returns True for a 'get' order with a valid sensor."""
        # GIVEN an order with action_type 'get' and a positive sensor pin
        order = Order(
            pk=1, slug="temp", action_type="get", sensor=4, controller=-1, is_toggle_ctrl_value=False, ctrl_value=""
        )

        # WHEN we check if it triggers a sensor
        # THEN it returns True
        assert order._is_trigger_sensor() is True

    def test_is_trigger_sensor_true_when_sensor_is_zero(self):
        """Test _is_trigger_sensor returns True when sensor pin is 0 (valid pin)."""
        # GIVEN an order with action_type 'get' and sensor pin 0
        order = Order(
            pk=1, slug="temp", action_type="get", sensor=0, controller=-1, is_toggle_ctrl_value=False, ctrl_value=""
        )

        # WHEN we check if it triggers a sensor
        # THEN it returns True (pin 0 is valid)
        assert order._is_trigger_sensor() is True

    def test_is_trigger_sensor_false_when_set(self):
        """Test _is_trigger_sensor returns False for a 'set' order."""
        # GIVEN an order with action_type 'set'
        order = Order(
            pk=1, slug="ctrl", action_type="set", sensor=4, controller=5, is_toggle_ctrl_value=False, ctrl_value="on"
        )

        # WHEN we check if it triggers a sensor
        # THEN it returns False
        assert order._is_trigger_sensor() is False

    def test_is_trigger_sensor_false_when_no_sensor(self):
        """Test _is_trigger_sensor returns False when sensor is -1."""
        # GIVEN an order with action_type 'get' but no sensor (pin -1)
        order = Order(
            pk=1, slug="temp", action_type="get", sensor=-1, controller=-1, is_toggle_ctrl_value=False, ctrl_value=""
        )

        # WHEN we check if it triggers a sensor
        # THEN it returns False
        assert order._is_trigger_sensor() is False

    # -- _is_trigger_controller --------------------------------------------

    def test_is_trigger_controller_true_when_set_and_valid(self):
        """Test _is_trigger_controller returns True for a 'set' order with valid controller and ctrl_value."""
        # GIVEN an order with action_type 'set', a valid controller and a non-empty ctrl_value
        order = Order(
            pk=1, slug="ctrl", action_type="set", sensor=-1, controller=5, is_toggle_ctrl_value=False, ctrl_value="on"
        )

        # WHEN we check if it triggers a controller
        # THEN it returns True
        assert order._is_trigger_controller() is True

    def test_is_trigger_controller_false_when_get(self):
        """Test _is_trigger_controller returns False for a 'get' order."""
        # GIVEN an order with action_type 'get'
        order = Order(
            pk=1, slug="temp", action_type="get", sensor=4, controller=5, is_toggle_ctrl_value=False, ctrl_value="on"
        )

        # WHEN we check if it triggers a controller
        # THEN it returns False
        assert order._is_trigger_controller() is False

    def test_is_trigger_controller_false_when_no_controller(self):
        """Test _is_trigger_controller returns False when controller is -1."""
        # GIVEN an order with action_type 'set' but no controller
        order = Order(
            pk=1, slug="ctrl", action_type="set", sensor=-1, controller=-1, is_toggle_ctrl_value=False, ctrl_value="on"
        )

        # WHEN we check if it triggers a controller
        # THEN it returns False
        assert order._is_trigger_controller() is False

    @pytest.mark.parametrize("empty_value", ["", "None", "none", "NULL", "null"])
    def test_is_trigger_controller_false_when_ctrl_value_empty(self, empty_value):
        """Test _is_trigger_controller returns False when ctrl_value is an empty-like value."""
        # GIVEN an order with action_type 'set' but an empty ctrl_value
        order = Order(
            pk=1,
            slug="ctrl",
            action_type="set",
            sensor=-1,
            controller=5,
            is_toggle_ctrl_value=False,
            ctrl_value=empty_value,
        )

        # WHEN we check if it triggers a controller
        # THEN it returns False
        assert order._is_trigger_controller() is False


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


# ---------------------------------------------------------------------------
# Tests – Pin
# ---------------------------------------------------------------------------


class TestPin:
    """Tests for the Pin model."""

    def test_init_sets_channel_choiced(self, pin, pin_fields):
        """Test that the constructor stores channel_choiced correctly."""
        # GIVEN a Pin built from known fields (fixture)

        # WHEN we inspect channel_choiced
        # THEN it matches the input
        assert pin.channel_choiced == pin_fields["channel_choiced"]

    def test_init_sets_pin_number(self, pin, pin_fields):
        """Test that the constructor stores pin_number correctly."""
        # GIVEN a Pin built from known fields (fixture)

        # WHEN we inspect pin_number
        # THEN it matches the input
        assert pin.pin_number == pin_fields["pin_number"]

    def test_init_done_is_true_after_setup(self, pin):
        """Test that init_done is True after the machine pin is configured during __init__."""
        # GIVEN a fully initialised Pin (fixture)

        # WHEN we check init_done
        # THEN it is True (set by _set_done_init inside _setup_machine_pin)
        assert pin.init_done is True

    def test_initial_configuration_is_none_after_setup(self, pin):
        """Test that initial_configuration is cleared to None after successful setup."""
        # GIVEN a fully initialised Pin (fixture)

        # WHEN we check initial_configuration
        # THEN it has been cleared to None to save memory
        assert pin.initial_configuration is None

    def test_executor_is_set_after_setup(self, pin):
        """Test that executor is populated after the machine pin is configured."""
        # GIVEN a fully initialised Pin (fixture)

        # WHEN we check executor
        # THEN it is not None
        assert pin.executor is not None

    def test_fields_cfg_contains_expected_entries(self):
        """Test that fields_cfg declares the correct field names in order."""
        # GIVEN the Pin class

        # WHEN we read fields_cfg
        field_names = [name for name, _ in Pin.fields_cfg]

        # THEN the expected fields are present in order
        assert field_names == ["channel_choiced", "pin_number", "initial_configuration"]

    def test_fields_cfg_casters(self):
        """Test that fields_cfg uses the correct cast functions."""
        # GIVEN the Pin class

        # WHEN we read the casters from fields_cfg
        casters = [caster for _, caster in Pin.fields_cfg]

        # THEN they match str, int, json.loads in order
        assert casters[0] is str
        assert casters[1] is int
        assert casters[2] is json.loads

    # -- _set_done_init ----------------------------------------------------

    def test_set_done_init_sets_flag(self, pin):
        """Test that _set_done_init sets init_done to True."""
        # GIVEN a Pin with init_done manually reset
        pin.init_done = False

        # WHEN we call _set_done_init
        pin._set_done_init()

        # THEN init_done is True
        assert pin.init_done is True

    def test_set_done_init_clears_configuration(self, pin):
        """Test that _set_done_init clears initial_configuration to None."""
        # GIVEN a Pin with a config manually restored
        pin.initial_configuration = {"some": "config"}

        # WHEN we call _set_done_init
        pin._set_done_init()

        # THEN initial_configuration is None
        assert pin.initial_configuration is None
