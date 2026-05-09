import json

import pytest

from src.datasheet import InvalidChannelError
from src.models import Pin
from src.protocols.usb.parsers.pin import parse_str_pin_to_model

# ---------------------------------------------------------------------------
# Helpers – valid JSON configs per channel type
# ---------------------------------------------------------------------------

_DIGIT_CFG = json.dumps(
    {
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
)

_PWM_CFG = json.dumps(
    {
        "channel_class": "PWM",
        "arguments": [
            {
                "name": "dest",
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
                "value": 5,
            }
        ],
    }
)

_ANALOG_CFG = json.dumps(
    {
        "channel_class": "ADC",
        "arguments": [
            {
                "name": "pin",
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
                "value": 26,
            }
        ],
    }
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def valid_digit_fields():
    """Fixture providing valid string fields for a digital pin (channel='digit', pin=3)."""
    # channel_choiced, pin_number, initial_configuration
    return ("digit", "3", _DIGIT_CFG)


@pytest.fixture
def valid_pwm_fields():
    """Fixture providing valid string fields for a PWM pin (channel='pwm', pin=5)."""
    return ("pwm", "5", _PWM_CFG)


@pytest.fixture
def valid_analog_fields():
    """Fixture providing valid string fields for an analog pin (channel='analog', pin=26)."""
    return ("analog", "26", _ANALOG_CFG)


@pytest.fixture
def parsed_digit_pin(valid_digit_fields):
    """Fixture providing a parsed Pin instance from valid digital-channel fields."""
    return parse_str_pin_to_model(valid_digit_fields)


# ---------------------------------------------------------------------------
# Tests – parse_str_pin_to_model
# ---------------------------------------------------------------------------


class TestParseStrPinToModelHappyPath:
    """Tests for valid inputs across every supported channel type."""

    def test_returns_pin_instance(self, parsed_digit_pin):
        """Test that the function returns a Pin instance."""
        # GIVEN valid string fields for a digit pin (fixture)

        # WHEN parse_str_pin_to_model is called (fixture)

        # THEN a Pin instance is returned
        assert isinstance(parsed_digit_pin, Pin)

    def test_channel_choiced_remains_str(self, parsed_digit_pin):
        """Test that channel_choiced is stored as a str."""
        # GIVEN valid string fields with channel_choiced='digit' (fixture)

        # WHEN the pin is parsed (fixture)

        # THEN channel_choiced is the original string
        assert parsed_digit_pin.channel_choiced == "digit"
        assert isinstance(parsed_digit_pin.channel_choiced, str)

    def test_pin_number_is_cast_to_int(self, parsed_digit_pin):
        """Test that pin_number is correctly cast from str to int."""
        # GIVEN valid string fields with pin_number='3' (fixture)

        # WHEN the pin is parsed (fixture)

        # THEN pin_number is an int with the expected value
        assert parsed_digit_pin.pin_number == 3
        assert isinstance(parsed_digit_pin.pin_number, int)

    def test_initial_configuration_is_parsed_from_json(self, parsed_digit_pin):
        """Test that initial_configuration is deserialized from a JSON string."""
        # GIVEN valid string fields whose initial_configuration is a JSON string (fixture)

        # WHEN the pin is parsed (fixture)

        # THEN initial_configuration is a dict (already consumed by _setup_machine_pin,
        #      which sets it to None once init_done is True)
        # The field went through json.loads — confirming the cast was applied.
        assert parsed_digit_pin.init_done is True

    def test_all_fields_are_set(self, parsed_digit_pin):
        """Test that every field declared in fields_cfg is present on the result."""
        # GIVEN valid string fields (fixture)

        # WHEN the pin is parsed (fixture)

        # THEN every field from fields_cfg exists as an attribute
        for field_name, _ in Pin.fields_cfg:
            assert hasattr(parsed_digit_pin, field_name)

    def test_pwm_channel_is_valid(self, valid_pwm_fields):
        """Test that a PWM pin is parsed without error."""
        # GIVEN valid string fields for a PWM pin (channel='pwm', pin=5)

        # WHEN parse_str_pin_to_model is called
        result = parse_str_pin_to_model(valid_pwm_fields)

        # THEN a Pin instance is returned with the correct attributes
        assert isinstance(result, Pin)
        assert result.channel_choiced == "pwm"
        assert result.pin_number == 5

    def test_analog_channel_is_valid(self, valid_analog_fields):
        """Test that an analog pin is parsed without error."""
        # GIVEN valid string fields for an analog pin (channel='analog', pin=26)

        # WHEN parse_str_pin_to_model is called
        result = parse_str_pin_to_model(valid_analog_fields)

        # THEN a Pin instance is returned with the correct attributes
        assert isinstance(result, Pin)
        assert result.channel_choiced == "analog"
        assert result.pin_number == 26


class TestParseStrPinToModelFieldCountValidation:
    """Tests for field-count mismatches."""

    def test_too_few_fields_raises_value_error(self):
        """Test that providing fewer values than fields_cfg expects raises ValueError."""
        # GIVEN a tuple with only one element instead of three
        incomplete_fields = ("digit",)

        # WHEN / THEN a ValueError is raised
        with pytest.raises(ValueError):
            parse_str_pin_to_model(incomplete_fields)

    def test_too_many_fields_raises_value_error(self):
        """Test that providing more values than fields_cfg expects raises ValueError."""
        # GIVEN a tuple with four elements instead of three
        extra_fields = ("digit", "3", _DIGIT_CFG, "extra")

        # WHEN / THEN a ValueError is raised
        with pytest.raises(ValueError):
            parse_str_pin_to_model(extra_fields)

    def test_empty_tuple_raises_value_error(self):
        """Test that an empty tuple raises ValueError."""
        # GIVEN an empty tuple

        # WHEN / THEN a ValueError is raised
        with pytest.raises(ValueError):
            parse_str_pin_to_model(())


class TestParseStrPinToModelTypeCastValidation:
    """Tests for failures during field-type casting."""

    def test_non_numeric_pin_number_raises_value_error(self):
        """Test that a non-numeric pin_number string raises ValueError."""
        # GIVEN string fields where pin_number is not a valid integer
        bad_fields = ("digit", "abc", _DIGIT_CFG)

        # WHEN / THEN a ValueError is raised
        with pytest.raises(ValueError):
            parse_str_pin_to_model(bad_fields)

    def test_invalid_json_for_initial_configuration_raises_value_error(self):
        """Test that a malformed JSON string for initial_configuration raises ValueError."""
        # GIVEN string fields where initial_configuration is not valid JSON
        bad_fields = ("digit", "3", "not-valid-json{{{")

        # WHEN / THEN a ValueError is raised (json.JSONDecodeError is a subclass of ValueError)
        with pytest.raises(ValueError):
            parse_str_pin_to_model(bad_fields)


class TestParseStrPinToModelChannelValidation:
    """Tests for channel validation via validate_channel."""

    def test_unknown_channel_raises_invalid_channel_error(self):
        """Test that an unrecognised channel name raises InvalidChannelError."""
        # GIVEN string fields where channel_choiced is not in AVAILABLE_CHANNELS
        bad_fields = ("foobar", "3", _DIGIT_CFG)

        # WHEN / THEN an InvalidChannelError is raised
        with pytest.raises(InvalidChannelError):
            parse_str_pin_to_model(bad_fields)

    def test_i2c_channel_raises_invalid_channel_error(self):
        """Test that 'i2c' is not an available channel and raises InvalidChannelError."""
        # GIVEN string fields where channel_choiced='i2c' (not in AVAILABLE_CHANNELS)
        bad_fields = ("i2c", "0", _DIGIT_CFG)

        # WHEN / THEN an InvalidChannelError is raised
        with pytest.raises(InvalidChannelError):
            parse_str_pin_to_model(bad_fields)

    def test_uppercase_channel_raises_invalid_channel_error(self):
        """Test that channel names are case-sensitive ('DIGIT' != 'digit')."""
        # GIVEN string fields with an uppercase channel name
        bad_fields = ("DIGIT", "3", _DIGIT_CFG)

        # WHEN / THEN an InvalidChannelError is raised
        with pytest.raises(InvalidChannelError):
            parse_str_pin_to_model(bad_fields)


class TestParseStrPinToModelPinNumberValidation:
    """Tests for pin-number validation via validate_pin."""

    def test_pin_not_allowed_for_digit_channel_raises_value_error(self):
        """Test that a pin number outside the digit-channel set raises ValueError."""
        # GIVEN a digit channel with pin 99 (not a valid GP pin)
        bad_fields = ("digit", "99", _DIGIT_CFG)

        # WHEN / THEN a ValueError is raised
        with pytest.raises(ValueError):
            parse_str_pin_to_model(bad_fields)

    def test_analog_pin_not_in_analog_range_raises_value_error(self):
        """Test that pin 3 is not valid for the analog channel (only 26/27/28 are)."""
        # GIVEN an analog channel with pin 3 (valid for digit but not analog)
        bad_fields = ("analog", "3", _ANALOG_CFG)

        # WHEN / THEN a ValueError is raised
        with pytest.raises(ValueError):
            parse_str_pin_to_model(bad_fields)

    def test_pwm_pin_not_allowed_raises_value_error(self):
        """Test that pin 99 is not valid for the pwm channel."""
        # GIVEN a pwm channel with a pin that does not exist on the RP2040
        bad_fields = ("pwm", "99", _PWM_CFG)

        # WHEN / THEN a ValueError is raised
        with pytest.raises(ValueError):
            parse_str_pin_to_model(bad_fields)
