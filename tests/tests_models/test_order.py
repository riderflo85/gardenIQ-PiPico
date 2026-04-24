import pytest

from src.models import Order


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
