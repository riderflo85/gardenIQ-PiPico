import pytest

from src.core.models import ModelType
from src.protocols.errors import CommandError
from src.protocols.usb.frame import CommandState
from src.protocols.usb.frame import Frame
from src.protocols.usb.frame import FrameType


# Fixtures
@pytest.fixture
def basic_command_frame_data():
    """Fixture providing basic data for a command frame."""
    return {
        "frame_type": FrameType.CMD,
        "device_uid": "DEV123",
        "command_id": 1,
        "command_slug": "test_command",
    }


@pytest.fixture
def master_frame_data():
    """Fixture providing data for a frame from master."""
    source_data = "CMD DEV456 2 master_command value1"
    calculated_checksum = Frame.build_checksum(source_data.encode())
    checksum_hex = format(calculated_checksum, "02X")
    return {
        "frame_type": FrameType.CMD,
        "device_uid": "DEV456",
        "command_id": 2,
        "command_slug": "master_command",
        "from_master": True,
        "checksum": checksum_hex,
        "source_frame_from_master": source_data,
    }


@pytest.fixture
def ack_frame_data():
    """Fixture providing data for an ACK frame."""
    return {
        "frame_type": FrameType.ACK,
        "device_uid": "DEV789",
        "command_id": 3,
        "command_slug": "ack_command",
        "command_state": CommandState.OK,
        "ok_data": "Success",
    }


@pytest.fixture
def error_frame_data():
    """Fixture providing data for an error frame."""
    return {
        "frame_type": FrameType.ACK,
        "device_uid": "DEV999",
        "command_id": 4,
        "command_slug": "error_command",
        "command_state": CommandState.ERROR,
        "err_msg": CommandError.INVALID_PARAM,
    }


@pytest.fixture
def ping_frame_data():
    """Fixture providing data for a ping frame (response from device)."""
    return {
        "frame_type": FrameType.ACK,
        "device_uid": "DEV111",
        "command_id": 0,
        "command_slug": "ping",
        "gd_fw_version": "1.0.0",
        "mp_fw_version": "1.20.0",
    }


@pytest.fixture
def ping_order_frame_data():
    """Fixture providing data for a ping order frame (from master)."""
    source_data = "PING DEV222 0"
    calculated_checksum = Frame.build_checksum(source_data.encode())
    checksum_hex = format(calculated_checksum, "02X")
    return {
        "frame_type": FrameType.PING,
        "device_uid": "DEV222",
        "command_id": 0,
        "command_slug": "ping",
        "from_master": True,
        "checksum": checksum_hex,
        "source_frame_from_master": source_data,
    }


@pytest.fixture
def lg_init_frame_data():
    """Fixture providing data for a LG_INIT frame (from master)."""
    source_data = "LG_INIT DEV333 -1 Order language fr"
    calculated_checksum = Frame.build_checksum(source_data.encode())
    checksum_hex = format(calculated_checksum, "02X")
    return {
        "frame_type": FrameType.LG_INIT,
        "device_uid": "DEV333",
        "command_id": -1,
        "command_slug": None,
        "from_master": True,
        "model": ModelType.ORDER,
        "model_attrs_values": ("language", "fr"),
        "checksum": checksum_hex,
        "source_frame_from_master": source_data,
    }


class TestFrameType:
    """Tests for the FrameType enum."""

    def test_frame_type_has_cmd(self):
        """Test that FrameType has CMD value."""
        # GIVEN: The FrameType enum

        # WHEN: We access the CMD attribute
        cmd_type = FrameType.CMD

        # THEN: It should equal "CMD"
        assert cmd_type == "CMD"

    def test_frame_type_has_ack(self):
        """Test that FrameType has ACK value."""
        # GIVEN: The FrameType enum

        # WHEN: We access the ACK attribute
        ack_type = FrameType.ACK

        # THEN: It should equal "ACK"
        assert ack_type == "ACK"

    def test_frame_type_has_ping(self):
        """Test that FrameType has PING value."""
        # GIVEN: The FrameType enum

        # WHEN: We access the PING attribute
        ping_type = FrameType.PING

        # THEN: It should equal "PING"
        assert ping_type == "PING"

    def test_frame_type_has_lg_init(self):
        """Test that FrameType has LG_INIT value."""
        # GIVEN: The FrameType enum

        # WHEN: We access the LG_INIT attribute
        lg_init_type = FrameType.LG_INIT

        # THEN: It should equal "LG_INIT"
        assert lg_init_type == "LG_INIT"

    def test_frame_type_iteration(self):
        """Test that FrameType can be iterated."""
        # GIVEN: The FrameType enum

        # WHEN: We iterate over FrameType
        values = list(FrameType)

        # THEN: It should contain all frame types
        assert "CMD" in values
        assert "PING" in values
        assert "ACK" in values
        assert "LG_INIT" in values
        assert len(values) == 4


class TestModelType:
    """Tests for the ModelType enum."""

    def test_model_type_has_order(self):
        """Test that ModelType has ORDER value."""
        # GIVEN: The ModelType enum

        # WHEN: We access the ORDER attribute
        order_type = ModelType.ORDER

        # THEN: It should equal "Order"
        assert order_type == "Order"

    def test_model_type_iteration(self):
        """Test that ModelType can be iterated."""
        # GIVEN: The ModelType enum

        # WHEN: We iterate over ModelType
        values = list(ModelType)

        # THEN: It should contain all model types
        assert "Order" in values
        assert len(values) == 1


class TestCommandState:
    """Tests for the CommandState enum."""

    def test_command_state_has_ok(self):
        """Test that CommandState has OK value."""
        # GIVEN: The CommandState enum

        # WHEN: We access the OK attribute
        ok_state = CommandState.OK

        # THEN: It should equal "OK"
        assert ok_state == "OK"

    def test_command_state_has_error(self):
        """Test that CommandState has ERROR value."""
        # GIVEN: The CommandState enum

        # WHEN: We access the ERROR attribute
        error_state = CommandState.ERROR

        # THEN: It should equal "ERR"
        assert error_state == "ERR"

    def test_command_state_iteration(self):
        """Test that CommandState can be iterated."""
        # GIVEN: The CommandState enum

        # WHEN: We iterate over CommandState
        values = list(CommandState)

        # THEN: It should contain all command states
        assert "OK" in values
        assert "ERR" in values
        assert len(values) == 2


class TestFrameInitialization:
    """Tests for Frame initialization."""

    def test_frame_creation_with_minimal_data(self, basic_command_frame_data):
        """Test creating a frame with minimal required data."""
        # GIVEN: Basic frame data (from fixture)

        # WHEN: We create a Frame instance
        frame = Frame(**basic_command_frame_data)

        # THEN: The frame should be created with correct attributes
        assert frame.frame_type == FrameType.CMD
        assert frame.device_uid == "DEV123"
        assert frame.command_id == 1
        assert frame.command_slug == "test_command"
        assert frame.from_master is False
        assert frame.model is None
        assert frame.model_attrs_values == ()
        assert frame.command_state is None
        assert frame.ok_data is None
        assert frame.err_msg is None

    def test_frame_creation_with_all_optional_fields(self):
        """Test creating a frame with all optional fields."""
        # GIVEN: Complete frame data with all optional fields
        data = {
            "frame_type": FrameType.ACK,
            "device_uid": "DEV_FULL",
            "command_id": 10,
            "command_slug": "full_command",
            "from_master": True,
            "command_state": CommandState.OK,
            "ok_data": "result_data",
            "err_msg": None,
            "gd_fw_version": "2.0.0",
            "mp_fw_version": "1.21.0",
            "checksum": "FF",
            "source_frame_from_master": "test_frame_data",
        }

        # WHEN: We create a Frame instance
        frame = Frame(**data)

        # THEN: All attributes should be set correctly
        assert frame.frame_type == FrameType.ACK
        assert frame.device_uid == "DEV_FULL"
        assert frame.command_id == 10
        assert frame.command_slug == "full_command"
        assert frame.from_master is True
        assert frame.command_state == CommandState.OK
        assert frame.ok_data == "result_data"
        assert frame.err_msg is None
        assert frame.gd_fw_version == "2.0.0"
        assert frame.mp_fw_version == "1.21.0"
        assert frame.checksum == "FF"
        assert frame.source_frame_from_master == "test_frame_data"

    def test_frame_creation_with_error_state(self, error_frame_data):
        """Test creating a frame with error state."""
        # GIVEN: Error frame data (from fixture)

        # WHEN: We create a Frame instance
        frame = Frame(**error_frame_data)

        # THEN: The frame should have error state and message
        assert frame.command_state == CommandState.ERROR
        assert frame.err_msg == CommandError.INVALID_PARAM

    def test_frame_creation_with_firmware_versions(self, ping_frame_data):
        """Test creating a frame with firmware versions."""
        # GIVEN: Ping frame data with firmware versions (from fixture)

        # WHEN: We create a Frame instance
        frame = Frame(**ping_frame_data)

        # THEN: Firmware versions should be set correctly
        assert frame.gd_fw_version == "1.0.0"
        assert frame.mp_fw_version == "1.20.0"

    def test_frame_creation_with_lg_init(self, lg_init_frame_data):
        """Test creating a LG_INIT frame."""
        # GIVEN: LG_INIT frame data (from fixture)

        # WHEN: We create a Frame instance
        frame = Frame(**lg_init_frame_data)

        # THEN: LG_INIT attributes should be set correctly
        assert frame.frame_type == FrameType.LG_INIT
        assert frame.command_id == -1
        assert frame.from_master is True
        assert frame.model == ModelType.ORDER
        assert frame.model_attrs_values == ("language", "fr")


class TestFrameValidation:
    """Tests for Frame validation."""

    def test_validation_fails_when_master_frame_missing_checksum(self, basic_command_frame_data):
        """Test that validation fails when from_master is True but checksum is None."""
        # GIVEN: Frame data from master without checksum
        data = {**basic_command_frame_data, "from_master": True}

        # WHEN/THEN: Creating the frame should raise ValueError
        with pytest.raises(ValueError, match="checksum required"):
            Frame(**data)

    def test_validation_fails_when_master_frame_missing_source_frame(self, basic_command_frame_data):
        """Test that validation fails when from_master is True but source_frame is None."""
        # GIVEN: Frame data from master with checksum but without source frame
        data = {**basic_command_frame_data, "from_master": True, "checksum": "A5"}

        # WHEN/THEN: Creating the frame should raise ValueError
        with pytest.raises(ValueError, match="source_frame required"):
            Frame(**data)

    def test_validation_passes_when_master_frame_has_required_fields(self, master_frame_data):
        """Test that validation passes when from_master frame has all required fields."""
        # GIVEN: Complete master frame data (from fixture)

        # WHEN: We create a Frame instance
        frame = Frame(**master_frame_data)

        # THEN: The frame should be created successfully
        assert frame.from_master is True
        assert frame.checksum is not None
        assert frame.source_frame_from_master == "CMD DEV456 2 master_command value1"

    def test_validation_passes_for_non_master_frame_without_checksum(self, basic_command_frame_data):
        """Test that validation passes for non-master frames without checksum."""
        # GIVEN: Frame data not from master (from fixture)

        # WHEN: We create a Frame instance without checksum
        frame = Frame(**basic_command_frame_data)

        # THEN: The frame should be created successfully
        assert frame.from_master is False
        assert frame.checksum is None
        assert frame.source_frame_from_master is None

    def test_validation_fails_when_ping_missing_gd_firmware_version(self):
        """Test that validation fails for ping (command_id=0) without GardenIQ firmware version."""
        # GIVEN: Ping frame data without gd_fw_version
        data = {
            "frame_type": FrameType.ACK,
            "device_uid": "DEV111",
            "command_id": 0,
            "command_slug": "ping",
            "mp_fw_version": "1.20.0",
        }

        # WHEN/THEN: Creating the frame should raise ValueError
        with pytest.raises(ValueError, match="Firmware versions required for ping command"):
            Frame(**data)

    def test_validation_fails_when_ping_missing_mp_firmware_version(self):
        """Test that validation fails for ping (command_id=0) without MicroPython firmware version."""
        # GIVEN: Ping frame data without mp_fw_version
        data = {
            "frame_type": FrameType.ACK,
            "device_uid": "DEV111",
            "command_id": 0,
            "command_slug": "ping",
            "gd_fw_version": "1.0.0",
        }

        # WHEN/THEN: Creating the frame should raise ValueError
        with pytest.raises(ValueError, match="Firmware versions required for ping command"):
            Frame(**data)

    def test_validation_fails_when_ping_has_invalid_gd_firmware_version_format(self):
        """Test that validation fails for ping with invalid GardenIQ firmware version format."""
        # GIVEN: Ping frame data with invalid gd_fw_version format
        data = {
            "frame_type": FrameType.ACK,
            "device_uid": "DEV111",
            "command_id": 0,
            "command_slug": "ping",
            "gd_fw_version": "1.0",  # Invalid format (should be X.Y.Z)
            "mp_fw_version": "1.20.0",
        }

        # WHEN/THEN: Creating the frame should raise ValueError
        with pytest.raises(ValueError, match="Invalid GardenIQ firmware version format"):
            Frame(**data)

    def test_validation_fails_when_ping_has_invalid_mp_firmware_version_format(self):
        """Test that validation fails for ping with invalid MicroPython firmware version format."""
        # GIVEN: Ping frame data with invalid mp_fw_version format
        data = {
            "frame_type": FrameType.ACK,
            "device_uid": "DEV111",
            "command_id": 0,
            "command_slug": "ping",
            "gd_fw_version": "1.0.0",
            "mp_fw_version": "1.20.0.1",  # Invalid format (too many parts)
        }

        # WHEN/THEN: Creating the frame should raise ValueError
        with pytest.raises(ValueError, match="Invalid MicroPython firmware version format"):
            Frame(**data)

    def test_validation_passes_when_ping_has_valid_firmware_versions(self, ping_frame_data):
        """Test that validation passes for ping with valid firmware versions."""
        # GIVEN: Ping frame data with valid firmware versions (from fixture)

        # WHEN: We create a Frame instance
        frame = Frame(**ping_frame_data)

        # THEN: The frame should be created successfully
        assert frame.command_id == 0
        assert frame.gd_fw_version == "1.0.0"
        assert frame.mp_fw_version == "1.20.0"

    def test_validation_fails_with_invalid_model_type(self, basic_command_frame_data):
        """Test that validation fails with an invalid model type."""
        # GIVEN: Frame data with invalid model type
        data = {**basic_command_frame_data, "model": "InvalidModel"}

        # WHEN/THEN: Creating the frame should raise ValueError
        with pytest.raises(ValueError, match="Invalid model type"):
            Frame(**data)

    def test_validation_passes_with_valid_model_type(self, basic_command_frame_data):
        """Test that validation passes with a valid model type."""
        # GIVEN: Frame data with valid model type
        data = {**basic_command_frame_data, "model": ModelType.ORDER}

        # WHEN: We create a Frame instance
        frame = Frame(**data)

        # THEN: The frame should be created successfully
        assert frame.model == ModelType.ORDER

    def test_validation_fails_when_lg_init_from_master_without_model(self):
        """Test that validation fails for LG_INIT from master without model."""
        # GIVEN: LG_INIT frame data from master without model
        source_data = "LG_INIT DEV444 -1"
        calculated_checksum = Frame.build_checksum(source_data.encode())
        checksum_hex = format(calculated_checksum, "02X")
        data = {
            "frame_type": FrameType.LG_INIT,
            "device_uid": "DEV444",
            "command_id": -1,
            "from_master": True,
            "checksum": checksum_hex,
            "source_frame_from_master": source_data,
        }

        # WHEN/THEN: Creating the frame should raise ValueError
        with pytest.raises(ValueError, match="model must be provided if command_id is -1 and from_master is True"):
            Frame(**data)

    def test_validation_passes_when_lg_init_from_master_with_model(self, lg_init_frame_data):
        """Test that validation passes for LG_INIT from master with model."""
        # GIVEN: LG_INIT frame data from master with model (from fixture)

        # WHEN: We create a Frame instance
        frame = Frame(**lg_init_frame_data)

        # THEN: The frame should be created successfully
        assert frame.command_id == -1
        assert frame.from_master is True
        assert frame.model == ModelType.ORDER


class TestBuildChecksum:
    """Tests for the build_checksum static method."""

    def test_build_checksum_with_simple_data(self):
        """Test checksum calculation with simple data."""
        # GIVEN: Simple byte data
        data = b"hello"

        # WHEN: We calculate the checksum
        checksum = Frame.build_checksum(data)

        # THEN: It should return an integer between 0 and 255
        assert isinstance(checksum, int)
        assert 0 <= checksum <= 255

    def test_build_checksum_with_empty_data(self):
        """Test checksum calculation with empty data."""
        # GIVEN: Empty byte data
        data = b""

        # WHEN: We calculate the checksum
        checksum = Frame.build_checksum(data)

        # THEN: It should return 0
        assert checksum == 0

    def test_build_checksum_is_deterministic(self):
        """Test that checksum calculation is deterministic."""
        # GIVEN: Same byte data
        data = b"test_data_123"

        # WHEN: We calculate the checksum multiple times
        checksum1 = Frame.build_checksum(data)
        checksum2 = Frame.build_checksum(data)
        checksum3 = Frame.build_checksum(data)

        # THEN: All checksums should be identical
        assert checksum1 == checksum2 == checksum3

    def test_build_checksum_different_data_gives_different_result(self):
        """Test that different data produces different checksums."""
        # GIVEN: Two different byte data
        data1 = b"data_one"
        data2 = b"data_two"

        # WHEN: We calculate checksums for both
        checksum1 = Frame.build_checksum(data1)
        checksum2 = Frame.build_checksum(data2)

        # THEN: Checksums should be different
        assert checksum1 != checksum2

    def test_build_checksum_with_special_characters(self):
        """Test checksum calculation with special characters."""
        # GIVEN: Byte data with special characters
        data = b"CMD DEV123 1 test arg1,arg2"

        # WHEN: We calculate the checksum
        checksum = Frame.build_checksum(data)

        # THEN: It should return a valid checksum
        assert isinstance(checksum, int)
        assert 0 <= checksum <= 255

    def test_build_checksum_returns_8_bit_value(self):
        """Test that checksum is always 8-bit (0-255)."""
        # GIVEN: Various byte data inputs
        test_cases = [
            b"a",
            b"test",
            b"long_string_with_many_characters_to_test_overflow",
            b"\x00\xff\xaa\x55",
        ]

        # WHEN/THEN: All checksums should be within 8-bit range
        for data in test_cases:
            checksum = Frame.build_checksum(data)
            assert 0 <= checksum <= 255


class TestVerifyChecksum:
    """Tests for the verify_checksum method."""

    def test_verify_checksum_returns_false_for_non_master_frame(self, basic_command_frame_data):
        """Test that verify_checksum returns False for non-master frames."""
        # GIVEN: A frame not from master
        frame = Frame(**basic_command_frame_data)

        # WHEN: We verify the checksum
        result = frame.verify_checksum()

        # THEN: It should return False
        assert result is False

    def test_verify_checksum_returns_false_when_missing_source_frame(self):
        """Test that verify_checksum returns False when source_frame is missing."""
        # GIVEN: A master frame without source_frame_from_master
        data = {
            "frame_type": FrameType.CMD,
            "device_uid": "DEV001",
            "command_id": 1,
            "command_slug": "test",
            "from_master": True,
            "checksum": "A5",
            "source_frame_from_master": None,
        }

        # WHEN/THEN: Creating frame should fail validation
        with pytest.raises(ValueError):
            Frame(**data)

    def test_verify_checksum_returns_false_when_missing_checksum(self):
        """Test that verify_checksum returns False when checksum is missing."""
        # GIVEN: A master frame without checksum
        data = {
            "frame_type": FrameType.CMD,
            "device_uid": "DEV002",
            "command_id": 1,
            "command_slug": "test",
            "from_master": True,
            "checksum": None,
            "source_frame_from_master": "test_data",
        }

        # WHEN/THEN: Creating frame should fail validation
        with pytest.raises(ValueError):
            Frame(**data)

    def test_verify_checksum_returns_true_for_valid_checksum(self):
        """Test that verify_checksum returns True for valid checksum."""
        # GIVEN: A frame with valid checksum
        source_data = "CMD DEV123 1 test arg"
        calculated_checksum = Frame.build_checksum(source_data.encode())
        checksum_hex = format(calculated_checksum, "02X")

        data = {
            "frame_type": FrameType.CMD,
            "device_uid": "DEV123",
            "command_id": 1,
            "command_slug": "test",
            "from_master": True,
            "checksum": checksum_hex,
            "source_frame_from_master": source_data,
        }
        frame = Frame(**data)

        # WHEN: We verify the checksum
        result = frame.verify_checksum()

        # THEN: It should return True
        assert result is True

    def test_verify_checksum_returns_false_for_invalid_checksum(self):
        """Test that verify_checksum returns False for invalid checksum."""
        # GIVEN: A frame with incorrect checksum
        source_data = "CMD DEV123 1 test arg"
        wrong_checksum = "FF"  # Intentionally wrong

        data = {
            "frame_type": FrameType.CMD,
            "device_uid": "DEV123",
            "command_id": 1,
            "command_slug": "test",
            "from_master": True,
            "checksum": wrong_checksum,
            "source_frame_from_master": source_data,
        }
        frame = Frame(**data)

        # WHEN: We verify the checksum
        result = frame.verify_checksum()

        # THEN: It should return False
        assert result is False

    def test_verify_checksum_handles_lowercase_hex_checksum(self):
        """Test that verify_checksum handles lowercase hexadecimal checksums."""
        # GIVEN: A frame with lowercase hex checksum
        source_data = "PING DEV999 0 ping"
        calculated_checksum = Frame.build_checksum(source_data.encode())
        checksum_hex = format(calculated_checksum, "02x")  # lowercase

        data = {
            "frame_type": FrameType.ACK,
            "device_uid": "DEV999",
            "command_id": 0,
            "command_slug": "ping",
            "from_master": True,
            "checksum": checksum_hex,
            "source_frame_from_master": source_data,
        }
        frame = Frame(**data)

        # WHEN: We verify the checksum
        result = frame.verify_checksum()

        # THEN: It should return True
        assert result is True


class TestFrameSlots:
    """Tests for Frame __slots__ memory optimization."""

    def test_frame_uses_slots(self, basic_command_frame_data):
        """Test that Frame uses __slots__ for memory optimization."""
        # GIVEN: A Frame instance
        frame = Frame(**basic_command_frame_data)

        # WHEN: We check if __dict__ exists
        has_dict = hasattr(frame, "__dict__")

        # THEN: It should not have __dict__ (uses __slots__ instead)
        assert not has_dict

    def test_cannot_add_arbitrary_attributes(self, basic_command_frame_data):
        """Test that we cannot add arbitrary attributes to Frame."""
        # GIVEN: A Frame instance
        frame = Frame(**basic_command_frame_data)

        # WHEN/THEN: Trying to add a new attribute should raise AttributeError
        with pytest.raises(AttributeError):
            frame.new_attribute = "value"  # type: ignore


class TestIsPingOrder:
    """Tests for the is_ping_order method."""

    def test_is_ping_order_returns_true_for_ping_from_master(self, ping_order_frame_data):
        """Test that is_ping_order returns True for PING frame from master with command_id 0."""
        # GIVEN: A PING frame from master with command_id 0
        frame = Frame(**ping_order_frame_data)

        # WHEN: We call is_ping_order
        result = frame.is_ping_order()

        # THEN: It should return True
        assert result is True

    def test_is_ping_order_returns_false_for_non_master_frame(self, ping_frame_data):
        """Test that is_ping_order returns False for frames not from master."""
        # GIVEN: A ping response frame (not from master)
        frame = Frame(**ping_frame_data)

        # WHEN: We call is_ping_order
        result = frame.is_ping_order()

        # THEN: It should return False
        assert result is False

    def test_is_ping_order_returns_false_for_wrong_frame_type(self, master_frame_data):
        """Test that is_ping_order returns False for non-PING frame types."""
        # GIVEN: A CMD frame from master
        frame = Frame(**master_frame_data)

        # WHEN: We call is_ping_order
        result = frame.is_ping_order()

        # THEN: It should return False
        assert result is False

    def test_is_ping_order_returns_false_for_wrong_command_id(self):
        """Test that is_ping_order returns False when command_id is not 0."""
        # GIVEN: A PING frame from master but with command_id != 0
        source_data = "PING DEV333 5"
        calculated_checksum = Frame.build_checksum(source_data.encode())
        checksum_hex = format(calculated_checksum, "02X")
        data = {
            "frame_type": FrameType.PING,
            "device_uid": "DEV333",
            "command_id": 5,
            "command_slug": "ping",
            "from_master": True,
            "checksum": checksum_hex,
            "source_frame_from_master": source_data,
        }
        frame = Frame(**data)

        # WHEN: We call is_ping_order
        result = frame.is_ping_order()

        # THEN: It should return False
        assert result is False

    def test_is_ping_order_returns_false_for_ack_frame(self):
        """Test that is_ping_order returns False for ACK frames."""
        # GIVEN: An ACK frame from master with command_id 0
        source_data = "ACK DEV444 0"
        calculated_checksum = Frame.build_checksum(source_data.encode())
        checksum_hex = format(calculated_checksum, "02X")
        data = {
            "frame_type": FrameType.ACK,
            "device_uid": "DEV444",
            "command_id": 0,
            "command_slug": "ack",
            "from_master": True,
            "checksum": checksum_hex,
            "source_frame_from_master": source_data,
        }
        frame = Frame(**data)

        # WHEN: We call is_ping_order
        result = frame.is_ping_order()

        # THEN: It should return False
        assert result is False


class TestIsInitOrder:
    """Tests for the is_init_order method."""

    def test_is_init_order_returns_true_for_lg_init_from_master(self, lg_init_frame_data):
        """Test that is_init_order returns True for LG_INIT frame from master."""
        # GIVEN: A LG_INIT frame from master (from fixture)
        frame = Frame(**lg_init_frame_data)

        # WHEN: We call is_init_order
        result = frame.is_init_order()

        # THEN: It should return True
        assert result is True

    def test_is_init_order_returns_false_for_non_master_frame(self, basic_command_frame_data):
        """Test that is_init_order returns False for non-master frames."""
        # GIVEN: A frame not from master (from fixture)
        frame = Frame(**basic_command_frame_data)

        # WHEN: We call is_init_order
        result = frame.is_init_order()

        # THEN: It should return False
        assert result is False

    def test_is_init_order_returns_false_for_wrong_frame_type(self, master_frame_data):
        """Test that is_init_order returns False for wrong frame type."""
        # GIVEN: A CMD frame from master (from fixture)
        frame = Frame(**master_frame_data)

        # WHEN: We call is_init_order
        result = frame.is_init_order()

        # THEN: It should return False
        assert result is False

    def test_is_init_order_returns_false_for_wrong_command_id(self):
        """Test that is_init_order returns False for wrong command_id."""
        # GIVEN: A LG_INIT frame from master with wrong command_id
        source_data = "LG_INIT DEV555 0 Order language en"
        calculated_checksum = Frame.build_checksum(source_data.encode())
        checksum_hex = format(calculated_checksum, "02X")
        data = {
            "frame_type": FrameType.LG_INIT,
            "device_uid": "DEV555",
            "command_id": 0,
            "from_master": True,
            "model": ModelType.ORDER,
            "model_attrs_values": ("language", "en"),
            "checksum": checksum_hex,
            "source_frame_from_master": source_data,
        }
        frame = Frame(**data)

        # WHEN: We call is_init_order
        result = frame.is_init_order()

        # THEN: It should return False
        assert result is False

    def test_is_init_order_returns_false_for_ping_frame(self, ping_order_frame_data):
        """Test that is_init_order returns False for PING frames."""
        # GIVEN: A PING frame from master (from fixture)
        frame = Frame(**ping_order_frame_data)

        # WHEN: We call is_init_order
        result = frame.is_init_order()

        # THEN: It should return False
        assert result is False


class TestIsCommandOrder:
    """Tests for the is_command_order method."""

    def test_is_command_order_returns_true_for_cmd_from_master_with_valid_id(self, master_frame_data):
        """Test that is_command_order returns True for CMD frame from master with command_id > 0."""
        # GIVEN: A CMD frame from master with command_id > 0
        frame = Frame(**master_frame_data)

        # WHEN: We call is_command_order
        result = frame.is_command_order()

        # THEN: It should return True
        assert result is True

    def test_is_command_order_returns_false_for_non_master_frame(self, basic_command_frame_data):
        """Test that is_command_order returns False for frames not from master."""
        # GIVEN: A CMD frame not from master
        frame = Frame(**basic_command_frame_data)

        # WHEN: We call is_command_order
        result = frame.is_command_order()

        # THEN: It should return False
        assert result is False

    def test_is_command_order_returns_false_for_wrong_frame_type(self, ping_order_frame_data):
        """Test that is_command_order returns False for non-CMD frame types."""
        # GIVEN: A PING frame from master
        frame = Frame(**ping_order_frame_data)

        # WHEN: We call is_command_order
        result = frame.is_command_order()

        # THEN: It should return False
        assert result is False

    def test_is_command_order_returns_false_for_command_id_zero(self):
        """Test that is_command_order returns False when command_id is 0."""
        # GIVEN: A CMD frame from master with command_id == 0
        source_data = "CMD DEV555 0 test"
        calculated_checksum = Frame.build_checksum(source_data.encode())
        checksum_hex = format(calculated_checksum, "02X")
        data = {
            "frame_type": FrameType.CMD,
            "device_uid": "DEV555",
            "command_id": 0,
            "command_slug": "test",
            "from_master": True,
            "checksum": checksum_hex,
            "source_frame_from_master": source_data,
        }
        frame = Frame(**data)

        # WHEN: We call is_command_order
        result = frame.is_command_order()

        # THEN: It should return False
        assert result is False

    def test_is_command_order_returns_false_for_ack_frame(self):
        """Test that is_command_order returns False for ACK frames."""
        # GIVEN: An ACK frame from master with command_id > 0
        source_data = "ACK DEV666 1"
        calculated_checksum = Frame.build_checksum(source_data.encode())
        checksum_hex = format(calculated_checksum, "02X")
        data = {
            "frame_type": FrameType.ACK,
            "device_uid": "DEV666",
            "command_id": 1,
            "command_slug": "ack",
            "from_master": True,
            "checksum": checksum_hex,
            "source_frame_from_master": source_data,
        }
        frame = Frame(**data)

        # WHEN: We call is_command_order
        result = frame.is_command_order()

        # THEN: It should return False
        assert result is False

    def test_is_command_order_returns_true_for_various_command_ids(self):
        """Test that is_command_order returns True for various command_id values > 0."""
        # GIVEN: CMD frames from master with different command_id values
        test_command_ids = [1, 5, 10, 100, 999]

        for cmd_id in test_command_ids:
            source_data = f"CMD DEV777 {cmd_id} test"
            calculated_checksum = Frame.build_checksum(source_data.encode())
            checksum_hex = format(calculated_checksum, "02X")
            data = {
                "frame_type": FrameType.CMD,
                "device_uid": "DEV777",
                "command_id": cmd_id,
                "command_slug": "test",
                "from_master": True,
                "checksum": checksum_hex,
                "source_frame_from_master": source_data,
            }
            frame = Frame(**data)

            # WHEN: We call is_command_order
            result = frame.is_command_order()

            # THEN: It should return True
            assert result is True, f"Failed for command_id={cmd_id}"
