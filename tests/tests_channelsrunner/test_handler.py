from typing import Literal

import pytest

from src.channelsrunner.handler import ChannelHandler
from src.datasheet import InvalidChannelError
from src.models.order import Order
from tests.mocks.machine import ADC as MockADC
from tests.mocks.machine import PWM as MockPWM
from tests.mocks.machine import Pin as MockMachinePin


class MockPinCfg:
    """Lightweight stand-in for src.models.Pin in handler tests."""

    def __init__(self, channel_choiced: str, executor):
        self.channel_choiced = channel_choiced
        self.executor = executor


def make_order(
    action_type: Literal["get", "set"] = "get",
    sensor: int = -1,
    controller: int = -1,
    ctrl_value: str = "",
    is_toggle: bool = False,
) -> Order:
    """Helper to build an Order for handler tests."""
    return Order(
        pk=1,
        slug="test-order",
        action_type=action_type,
        sensor=sensor,
        controller=controller,
        is_toggle_ctrl_value=is_toggle,
        ctrl_value=ctrl_value,
    )


@pytest.fixture
def handler():
    """A fresh ChannelHandler instance."""
    return ChannelHandler()


class TestHandleOrderRouting:
    """Tests for the pin selection logic in handle_order."""

    def test_uses_sensor_pin_when_order_triggers_sensor(self, handler, mocker):
        # GIVEN an order that triggers a sensor (GET + sensor >= 0)
        order = make_order(action_type="get", sensor=3)
        pin_cfg = MockPinCfg(channel_choiced="analog", executor=MockADC(pin=3))
        mock_get = mocker.patch("src.channelsrunner.handler.init_pins_store.get_item", return_value=pin_cfg)

        # WHEN handle_order is called
        handler.handle_order(order)

        # THEN get_item is called with the sensor pin number
        mock_get.assert_called_once_with(3)

    def test_uses_controller_pin_when_order_triggers_controller_set(self, handler, mocker):
        # GIVEN an order that triggers a controller SET (SET + controller >= 0 + ctrl_value valid)
        order = make_order(action_type="set", controller=5, ctrl_value="1", is_toggle=True)
        executor = MockMachinePin(id=5, mode=MockMachinePin.OUT)
        pin_cfg = MockPinCfg(channel_choiced="digit", executor=executor)
        mock_get = mocker.patch("src.channelsrunner.handler.init_pins_store.get_item", return_value=pin_cfg)

        # WHEN handle_order is called
        handler.handle_order(order)

        # THEN get_item is called with the controller pin number
        mock_get.assert_called_once_with(5)

    def test_uses_controller_pin_when_order_triggers_get_controller_value(self, handler, mocker):
        # GIVEN a GET order with controller >= 0 and no sensor (get controller value)
        order = make_order(action_type="get", sensor=-1, controller=5)
        executor = MockMachinePin(id=5, mode=MockMachinePin.OUT)
        pin_cfg = MockPinCfg(channel_choiced="digit", executor=executor)
        mock_get = mocker.patch("src.channelsrunner.handler.init_pins_store.get_item", return_value=pin_cfg)

        # WHEN handle_order is called
        handler.handle_order(order)

        # THEN get_item is called with the controller pin number
        mock_get.assert_called_once_with(5)

    def test_raises_value_error_when_order_has_no_trigger(self, handler):
        # GIVEN an order that does not trigger any sensor or controller action
        order = make_order(action_type="set", controller=-1, ctrl_value="")

        # WHEN handle_order is called
        # THEN a ValueError is raised
        with pytest.raises(ValueError, match="does not trigger any sensor or controller action"):
            handler.handle_order(order)

    def test_raises_value_error_when_executor_is_none(self, handler, mocker):
        # GIVEN a valid order but the pin executor is not initialized
        order = make_order(action_type="get", sensor=2)
        pin_cfg = MockPinCfg(channel_choiced="analog", executor=None)
        mocker.patch("src.channelsrunner.handler.init_pins_store.get_item", return_value=pin_cfg)

        # WHEN handle_order is called
        # THEN a ValueError is raised indicating the pin is not initialized
        with pytest.raises(ValueError, match="is not initialized"):
            handler.handle_order(order)

    def test_raises_invalid_channel_error_when_channel_is_unknown(self, handler, mocker):
        # GIVEN a pin with an unsupported channel type
        order = make_order(action_type="get", sensor=2)
        pin_cfg = MockPinCfg(channel_choiced="i2c", executor=mocker.MagicMock())
        mocker.patch("src.channelsrunner.handler.init_pins_store.get_item", return_value=pin_cfg)

        # WHEN handle_order is called
        # THEN an InvalidChannelError is raised
        with pytest.raises(InvalidChannelError):
            handler.handle_order(order)

    def test_raises_key_error_when_pin_not_found_in_store(self, handler, mocker):
        # GIVEN an order referencing a pin number that is not registered in the store
        order = make_order(action_type="get", sensor=99)
        mocker.patch("src.channelsrunner.handler.init_pins_store.get_item", side_effect=KeyError("99"))

        # WHEN handle_order is called
        # THEN a KeyError is raised
        with pytest.raises(KeyError):
            handler.handle_order(order)


class TestHandleDigit:
    """Tests for the digit channel dispatch via handle_order."""

    def test_returns_pin_value_when_action_is_get(self, handler, mocker):
        # GIVEN a GET order on a digit controller pin whose value is 1
        order = make_order(action_type="get", sensor=-1, controller=4)
        executor = MockMachinePin(id=4, mode=MockMachinePin.OUT)
        executor.value(1)
        pin_cfg = MockPinCfg(channel_choiced="digit", executor=executor)
        mocker.patch("src.channelsrunner.handler.init_pins_store.get_item", return_value=pin_cfg)

        # WHEN handle_order is called
        result = handler.handle_order(order)

        # THEN the current pin value is returned
        assert result == 1

    def test_sets_pin_high_when_action_is_set_with_value_one(self, handler, mocker):
        # GIVEN a SET order on a digit controller pin with ctrl_value="1"
        order = make_order(action_type="set", controller=4, ctrl_value="1", is_toggle=True)
        executor = MockMachinePin(id=4, mode=MockMachinePin.OUT)
        pin_cfg = MockPinCfg(channel_choiced="digit", executor=executor)
        mocker.patch("src.channelsrunner.handler.init_pins_store.get_item", return_value=pin_cfg)

        # WHEN handle_order is called
        handler.handle_order(order)

        # THEN the pin value is set to 1
        assert executor.value() == 1

    def test_sets_pin_low_when_action_is_set_with_value_O(self, handler, mocker):
        # GIVEN a SET order on a digit controller pin with ctrl_value="O"
        order = make_order(action_type="set", controller=4, ctrl_value="O", is_toggle=True)
        executor = MockMachinePin(id=4, mode=MockMachinePin.OUT)
        executor.value(1)
        pin_cfg = MockPinCfg(channel_choiced="digit", executor=executor)
        mocker.patch("src.channelsrunner.handler.init_pins_store.get_item", return_value=pin_cfg)

        # WHEN handle_order is called
        handler.handle_order(order)

        # THEN the pin value is set to 0
        assert executor.value() == 0


class TestHandlePwm:
    """Tests for the PWM channel dispatch via handle_order."""

    def test_returns_duty_cycle_when_action_is_get(self, handler, mocker):
        # GIVEN a GET order on a PWM controller pin with duty cycle 2048
        order = make_order(action_type="get", sensor=-1, controller=6)
        executor = MockPWM(dest=6, duty_u16_value=2048)
        pin_cfg = MockPinCfg(channel_choiced="pwm", executor=executor)
        mocker.patch("src.channelsrunner.handler.init_pins_store.get_item", return_value=pin_cfg)

        # WHEN handle_order is called
        result = handler.handle_order(order)

        # THEN the current duty cycle is returned
        assert result == 2048

    def test_updates_duty_cycle_when_action_is_set(self, handler, mocker):
        # GIVEN a SET order on a PWM controller pin with ctrl_value="4096"
        order = make_order(action_type="set", controller=6, ctrl_value="4096")
        executor = MockPWM(dest=6, duty_u16_value=0)
        pin_cfg = MockPinCfg(channel_choiced="pwm", executor=executor)
        mocker.patch("src.channelsrunner.handler.init_pins_store.get_item", return_value=pin_cfg)

        # WHEN handle_order is called
        handler.handle_order(order)

        # THEN the duty cycle is updated to 4096
        assert executor.duty_u16() == 4096


class TestHandleAnalog:
    """Tests for the analog channel dispatch via handle_order."""

    def test_returns_adc_reading_when_channel_is_analog(self, handler, mocker):
        # GIVEN a GET order on an analog sensor pin that reads 54321
        order = make_order(action_type="get", sensor=7)
        executor = MockADC(pin=7, read_u16_value=54321)
        pin_cfg = MockPinCfg(channel_choiced="analog", executor=executor)
        mocker.patch("src.channelsrunner.handler.init_pins_store.get_item", return_value=pin_cfg)

        # WHEN handle_order is called
        result = handler.handle_order(order)

        # THEN the ADC reading is returned
        assert result == 54321

    def test_returns_zero_when_adc_reads_zero(self, handler, mocker):
        # GIVEN a GET order on an analog sensor pin that reads 0
        order = make_order(action_type="get", sensor=7)
        executor = MockADC(pin=7, read_u16_value=0)
        pin_cfg = MockPinCfg(channel_choiced="analog", executor=executor)
        mocker.patch("src.channelsrunner.handler.init_pins_store.get_item", return_value=pin_cfg)

        # WHEN handle_order is called
        result = handler.handle_order(order)

        # THEN 0 is returned
        assert result == 0
