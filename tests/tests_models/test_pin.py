import json
from copy import deepcopy
from typing import Any
from typing import cast

import pytest

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

    def test_executor_is_configured_with_expected_values(self, pin):
        """Test that executor receives the expected translated constructor values."""
        # GIVEN a fully initialised Pin (fixture)

        # WHEN we inspect the machine.Pin mock instance
        # THEN id uses JSON value and mode resolves to machine.Pin.IN
        assert pin.executor.id == 3
        assert pin.executor.mode == 1

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

    # -- _setup_machine_pin ----------------------------------------------

    def test_setup_machine_pin_returns_none_when_initial_configuration_is_none(self):
        """Test that setup exits early when initial_configuration is None."""
        # GIVEN a Pin created without initial configuration
        pin = Pin(channel_choiced="digit", pin_number=3, initial_configuration=None)  # type: ignore

        # WHEN __init__ runs _setup_machine_pin
        # THEN executor remains None and init_done stays False
        assert pin.executor is None
        assert pin.init_done is False

    def test_setup_machine_pin_returns_none_when_init_is_already_done(self, pin):
        """Test that setup exits early when init_done is already True."""
        # GIVEN a fully initialised Pin where init_done is already True
        pin.initial_configuration = deepcopy(_PIN_INITIAL_CFG)
        pin.init_done = True

        # WHEN _setup_machine_pin is called again
        result = pin._setup_machine_pin()

        # THEN it returns None and does not consume the configuration
        assert result is None
        assert pin.initial_configuration is not None

    def test_setup_machine_pin_invalid_channel_class_raises_value_error(self):
        """Test that an unknown channel_class raises ValueError."""
        # GIVEN an initial_configuration with an invalid channel_class
        bad_cfg = deepcopy(_PIN_INITIAL_CFG)
        bad_cfg["channel_class"] = "NOT_A_MACHINE_CLASS"

        # WHEN / THEN a ValueError is raised
        with pytest.raises(ValueError, match="Invalid channel class"):
            Pin(channel_choiced="digit", pin_number=3, initial_configuration=bad_cfg)

    def test_setup_machine_pin_unauthorized_module_raises_value_error(self):
        """Test that a non-whitelisted MicroPython module raises ValueError."""
        # GIVEN an argument pointing to a forbidden MicroPython module
        bad_cfg = deepcopy(_PIN_INITIAL_CFG)
        bad_cfg["arguments"][1]["value_type"]["mp_module_name"] = "network"

        # WHEN / THEN a ValueError is raised
        with pytest.raises(ValueError, match="not authorized"):
            Pin(channel_choiced="digit", pin_number=3, initial_configuration=bad_cfg)

    def test_setup_machine_pin_missing_micropython_attribute_name_raises_value_error(self):
        """Test that a missing attribute_name for MicroPython class arguments raises ValueError."""
        # GIVEN a MicroPython-class argument with an empty attribute_name
        bad_cfg = deepcopy(_PIN_INITIAL_CFG)
        bad_cfg["arguments"][1]["value_type"]["attribute_name"] = ""

        # WHEN / THEN a ValueError is raised
        with pytest.raises(ValueError, match="Missing attribute_name for micropython class"):
            Pin(channel_choiced="digit", pin_number=3, initial_configuration=bad_cfg)

    def test_setup_machine_pin_missing_garden_model_attribute_name_raises_value_error(self):
        """Test that a missing attribute_name for garden model arguments raises ValueError."""
        # GIVEN a garden-model argument with an empty attribute_name
        bad_cfg = deepcopy(_PIN_INITIAL_CFG)
        bad_cfg["arguments"][0]["value_type"]["attribute_name"] = ""

        # WHEN / THEN a ValueError is raised
        with pytest.raises(ValueError, match="Missing attribute_name for garden model argument"):
            Pin(channel_choiced="digit", pin_number=3, initial_configuration=bad_cfg)

    def test_setup_machine_pin_value_mismatch_raises_value_error(self):
        """Test that check_with_json_value raises when resolved value differs from JSON value."""
        # GIVEN an argument where resolved value != JSON value
        bad_cfg = deepcopy(_PIN_INITIAL_CFG)
        bad_cfg["arguments"][0]["value_type"]["check_with_json_value"] = True
        bad_cfg["arguments"][0]["value_type"]["use_json_value"] = False
        bad_cfg["arguments"][0]["value"] = 99

        # WHEN / THEN a ValueError is raised
        with pytest.raises(ValueError, match="Value mismatch for argument"):
            Pin(channel_choiced="digit", pin_number=3, initial_configuration=bad_cfg)

    def test_setup_machine_pin_use_json_value_overrides_resolved_value(self):
        """Test that use_json_value forces the constructor argument to the JSON value."""
        # GIVEN an id argument with a JSON value different from pin_number
        cfg = deepcopy(_PIN_INITIAL_CFG)
        cfg["arguments"][0]["value_type"]["check_with_json_value"] = False
        cfg["arguments"][0]["value_type"]["use_json_value"] = True
        cfg["arguments"][0]["value"] = 7

        # WHEN a Pin is initialised
        pin = Pin(channel_choiced="digit", pin_number=3, initial_configuration=cfg)
        # Use cast to Any to access the mock executor's attributes without type errors,
        # since it's a dynamic mock object
        executor = cast(Any, pin.executor)

        # THEN executor.id uses JSON value (7), not the model attribute (3)
        assert executor.id == 7

    def test_setup_machine_pin_skips_argument_marked_with_skip_this_arg(self):
        """Test that arguments marked skip_this_arg=True are ignored."""
        # GIVEN a config with an optional 'pull' argument explicitly marked as skipped
        cfg = deepcopy(_PIN_INITIAL_CFG)
        cfg["arguments"].append(
            {
                "name": "pull",
                "skip_this_arg": True,
                "value_type": {
                    "is_micropython_class": True,
                    "mp_module_name": "machine",
                    "mp_class_name": "Pin",
                    "garden_model": "",
                    "attribute_name": "PULL_UP",
                    "check_with_json_value": False,
                    "use_json_value": False,
                },
                "value": "",
            }
        )

        # WHEN a Pin is initialised
        pin = Pin(channel_choiced="digit", pin_number=3, initial_configuration=cfg)
        # Use cast to Any to access the mock executor's attributes without type errors,
        # since it's a dynamic mock object
        executor = cast(Any, pin.executor)

        # THEN pull was not provided and keeps constructor default None
        assert executor.pull is None

    def test_setup_machine_pin_non_pin_garden_model_keeps_none_value(self):
        """Test that non-'Pin' garden_model arguments keep value=None when not overridden."""
        # GIVEN a config with an optional 'pull' argument from an unknown garden model
        cfg = deepcopy(_PIN_INITIAL_CFG)
        cfg["arguments"].append(
            {
                "name": "pull",
                "skip_this_arg": False,
                "value_type": {
                    "is_micropython_class": False,
                    "mp_module_name": "",
                    "mp_class_name": "",
                    "garden_model": "UnknownModel",
                    "attribute_name": "ignored",
                    "check_with_json_value": False,
                    "use_json_value": False,
                },
                "value": "",
            }
        )

        # WHEN a Pin is initialised
        pin = Pin(channel_choiced="digit", pin_number=3, initial_configuration=cfg)
        # Use cast to Any to access the mock executor's attributes without type errors,
        # since it's a dynamic mock object
        executor = cast(Any, pin.executor)

        # THEN unresolved value stays None and is passed as-is
        assert executor.pull is None
