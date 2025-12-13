import pytest

from src.protocols.errors import CommandError
from src.protocols.errors import FrameParsingError
from src.protocols.usb.frame import CommandState
from src.protocols.usb.frame import Frame
from src.protocols.usb.frame import FrameType
from src.protocols.usb.parser import FrameParser


class TestFrameParserParseFromMaster:
    """Tests for FrameParser.parse_from_master method."""

    # Fixtures
    @pytest.fixture
    def valid_ping_frame(self):
        """Valid ping command frame from master (command_id = 0)."""
        return "< PING device123 0 ping > 3C\n"

    @pytest.fixture
    def valid_command_frame_no_args(self):
        """Valid command frame without arguments."""
        return "< CMD device456 1 water_now > 42\n"

    @pytest.fixture
    def valid_command_frame_with_args(self):
        """Valid command frame with multiple arguments."""
        return "< CMD device789 2 set_schedule 08:00,18:00,daily > 5A\n"

    @pytest.fixture
    def valid_command_frame_single_arg(self):
        """Valid command frame with a single argument."""
        return "< CMD device999 3 set_duration 30 > 7F\n"

    # Tests for valid frames
    def test_parse_valid_ping_frame(self, valid_ping_frame):
        # GIVEN a valid ping frame string from master
        frame_str = valid_ping_frame

        # WHEN parsing the frame
        result = FrameParser.parse_from_master(frame_str)

        # THEN the frame is correctly parsed
        assert isinstance(result, Frame)
        assert result.frame_type == FrameType.PING
        assert result.device_uid == "device123"
        assert result.command_id == 0
        assert result.command_slug == "ping"
        assert result.args_values == []
        assert result.from_master is True
        assert result.checksum == "3C"
        assert result.source_frame_from_master == "< PING device123 0 ping > 3C"

    def test_parse_valid_command_no_args(self, valid_command_frame_no_args):
        # GIVEN a valid command frame without arguments
        frame_str = valid_command_frame_no_args

        # WHEN parsing the frame
        result = FrameParser.parse_from_master(frame_str)

        # THEN the frame is correctly parsed
        assert isinstance(result, Frame)
        assert result.frame_type == FrameType.CMD
        assert result.device_uid == "device456"
        assert result.command_id == 1
        assert result.command_slug == "water_now"
        assert result.args_values == []
        assert result.from_master is True
        assert result.checksum == "42"

    def test_parse_valid_command_with_multiple_args(self, valid_command_frame_with_args):
        # GIVEN a valid command frame with multiple arguments
        frame_str = valid_command_frame_with_args

        # WHEN parsing the frame
        result = FrameParser.parse_from_master(frame_str)

        # THEN the frame is correctly parsed with all arguments
        assert isinstance(result, Frame)
        assert result.frame_type == FrameType.CMD
        assert result.device_uid == "device789"
        assert result.command_id == 2
        assert result.command_slug == "set_schedule"
        assert result.args_values == ["08:00", "18:00", "daily"]
        assert result.from_master is True
        assert result.checksum == "5A"

    def test_parse_valid_command_with_single_arg(self, valid_command_frame_single_arg):
        # GIVEN a valid command frame with a single argument
        frame_str = valid_command_frame_single_arg

        # WHEN parsing the frame
        result = FrameParser.parse_from_master(frame_str)

        # THEN the frame is correctly parsed
        assert result.command_id == 3
        assert result.command_slug == "set_duration"
        assert result.args_values == ["30"]

    # Tests for invalid frames - missing newline
    def test_parse_frame_without_newline_raises_error(self):
        # GIVEN a frame string without a newline character
        frame_str = "< CMD device123 0 ping > 3C"

        # WHEN parsing the frame
        # THEN a FrameParsingError is raised
        with pytest.raises(FrameParsingError) as exc_info:
            FrameParser.parse_from_master(frame_str)

        assert "does not end with a newline character" in str(exc_info.value)

    # Tests for invalid frames - too short
    def test_parse_frame_too_short_raises_error(self):
        # GIVEN a frame string that is too short (less than 7 parts)
        frame_str = "< CMD device123 0 > 3C\n"

        # WHEN parsing the frame
        # THEN a FrameParsingError is raised
        with pytest.raises(FrameParsingError) as exc_info:
            FrameParser.parse_from_master(frame_str)

        assert "too short" in str(exc_info.value)
        assert "may be infected" in str(exc_info.value)

    def test_parse_frame_minimal_parts_raises_error(self):
        # GIVEN a frame string with only 3 parts
        frame_str = "< CMD device123\n"

        # WHEN parsing the frame
        # THEN a FrameParsingError is raised
        with pytest.raises(FrameParsingError) as exc_info:
            FrameParser.parse_from_master(frame_str)

        assert "too short" in str(exc_info.value)

    # Tests for invalid STX/ETX markers
    def test_parse_frame_invalid_stx_raises_error(self):
        # GIVEN a frame string with an invalid STX marker
        frame_str = "[ CMD device123 0 ping > 3C\n"

        # WHEN parsing the frame
        # THEN a FrameParsingError is raised
        with pytest.raises(FrameParsingError) as exc_info:
            FrameParser.parse_from_master(frame_str)

        assert "Invalid STX" in str(exc_info.value)
        assert "[" in str(exc_info.value)

    def test_parse_frame_invalid_etx_raises_error(self):
        # GIVEN a frame string with an invalid ETX marker
        frame_str = "< CMD device123 0 ping ] 3C\n"

        # WHEN parsing the frame
        # THEN a FrameParsingError is raised
        with pytest.raises(FrameParsingError) as exc_info:
            FrameParser.parse_from_master(frame_str)

        assert "Invalid ETX" in str(exc_info.value)
        assert "]" in str(exc_info.value)

    # Tests for invalid frame type
    def test_parse_frame_invalid_frame_type_raises_error(self):
        # GIVEN a frame string with an invalid frame type
        frame_str = "< INVALID device123 0 ping > 3C\n"

        # WHEN parsing the frame
        # THEN a FrameParsingError is raised
        with pytest.raises(FrameParsingError) as exc_info:
            FrameParser.parse_from_master(frame_str)

        assert "Invalid frame type" in str(exc_info.value)
        assert "INVALID" in str(exc_info.value)

    # Tests for different frame types
    def test_parse_ack_frame_type(self):
        # GIVEN an ACK frame type
        frame_str = "< ACK device123 0 ping > 3C\n"

        # WHEN parsing the frame
        result = FrameParser.parse_from_master(frame_str)

        # THEN the frame type is ACK
        assert result.frame_type == FrameType.ACK

    # Edge cases
    def test_parse_frame_with_empty_device_uid(self):
        # GIVEN a frame with an empty device UID (but still valid structure)
        frame_str = "< CMD  0 ping > 3C\n"

        # WHEN parsing the frame
        result = FrameParser.parse_from_master(frame_str)

        # THEN the device_uid is empty string
        assert result.device_uid == ""

    def test_parse_frame_with_special_characters_in_slug(self):
        # GIVEN a frame with special characters in command slug
        frame_str = "< CMD device123 5 water_zone_2 value1,value2 > AB\n"

        # WHEN parsing the frame
        result = FrameParser.parse_from_master(frame_str)

        # THEN the slug is correctly parsed
        assert result.command_slug == "water_zone_2"
        assert result.args_values == ["value1", "value2"]


class TestFrameParserParseFromFrameKlass:
    """Tests for FrameParser.parse_from_frame_klass method."""

    # Fixtures
    @pytest.fixture
    def ping_response_frame_ok(self):
        """Frame object for a successful ping response."""
        return Frame(
            frame_type=FrameType.ACK,
            device_uid="device123",
            command_id=0,
            from_master=False,
            command_state=CommandState.OK,
            gd_fw_version="1.2.3",
            mp_fw_version="1.11.0",
        )

    @pytest.fixture
    def ping_response_frame_error(self):
        """Frame object for a ping response with error."""
        return Frame(
            frame_type=FrameType.ACK,
            device_uid="device456",
            command_id=0,
            from_master=False,
            command_state=CommandState.ERROR,
            err_msg=CommandError.CHECKSUM_ERR,
            gd_fw_version="1.2.3",
            mp_fw_version="1.11.0",
        )

    @pytest.fixture
    def command_response_ok_with_data(self):
        """Frame object for a successful command response with data."""
        return Frame(
            frame_type=FrameType.ACK,
            device_uid="device789",
            command_id=5,
            from_master=False,
            command_state=CommandState.OK,
            ok_data="sensor_value:42.5",
        )

    @pytest.fixture
    def command_response_ok_no_data(self):
        """Frame object for a successful command response without data."""
        return Frame(
            frame_type=FrameType.ACK,
            device_uid="device999",
            command_id=3,
            from_master=False,
            command_state=CommandState.OK,
            ok_data="",
        )

    @pytest.fixture
    def command_response_error(self):
        """Frame object for a command response with error."""
        return Frame(
            frame_type=FrameType.ACK,
            device_uid="device111",
            command_id=7,
            from_master=False,
            command_state=CommandState.ERROR,
            err_msg=CommandError.INVALID_PARAM,
        )

    @pytest.fixture
    def master_frame(self):
        """Frame object that comes from master (should raise error)."""
        return Frame(
            frame_type=FrameType.CMD,
            device_uid="device222",
            command_id=1,
            from_master=True,
            command_slug="test",
            checksum="3C",
            source_frame_from_master="< CMD device222 1 test > 3C",
        )

    # Tests for ping responses
    def test_serialize_ping_response_ok(self, ping_response_frame_ok):
        # GIVEN a successful ping response frame
        frame = ping_response_frame_ok

        # WHEN serializing the frame
        result = FrameParser.parse_from_frame_klass(frame)

        # THEN the frame string is correctly formatted
        assert result.startswith("< ACK device123 0 OK GDFW=1.2.3 MPFW=1.11.0 > ")
        assert result.endswith("\n")
        # Verify checksum is 2 uppercase hex characters
        checksum_part = result.split(" ")[-1].strip()
        assert len(checksum_part) == 2
        assert all(c in "0123456789ABCDEF" for c in checksum_part)

    def test_serialize_ping_response_error(self, ping_response_frame_error):
        # GIVEN a ping response frame with error
        frame = ping_response_frame_error

        # WHEN serializing the frame
        result = FrameParser.parse_from_frame_klass(frame)

        # THEN the frame string contains error message
        assert "< ACK device456 0 ERR CHECKSUM_ERR >" in result
        assert result.endswith("\n")

    # Tests for command responses with command_id > 0
    def test_serialize_command_response_ok_with_data(self, command_response_ok_with_data):
        # GIVEN a successful command response with data
        frame = command_response_ok_with_data

        # WHEN serializing the frame
        result = FrameParser.parse_from_frame_klass(frame)

        # THEN the frame string contains the ok_data
        assert "< ACK device789 5 OK sensor_value:42.5 >" in result
        assert result.endswith("\n")

    def test_serialize_command_response_ok_no_data(self, command_response_ok_no_data):
        # GIVEN a successful command response without data
        frame = command_response_ok_no_data

        # WHEN serializing the frame
        result = FrameParser.parse_from_frame_klass(frame)

        # THEN the frame string has empty data field
        assert "< ACK device999 3 OK  >" in result
        assert result.endswith("\n")

    def test_serialize_command_response_error(self, command_response_error):
        # GIVEN a command response with error
        frame = command_response_error

        # WHEN serializing the frame
        result = FrameParser.parse_from_frame_klass(frame)

        # THEN the frame string contains error message
        assert "< ACK device111 7 ERR INVALID_PARAM >" in result
        assert result.endswith("\n")

    # Tests for frame type variations
    def test_serialize_cmd_frame_type(self):
        # GIVEN a CMD frame type (not ACK)
        frame = Frame(
            frame_type=FrameType.CMD,
            device_uid="device333",
            command_id=10,
            from_master=False,
            command_state=CommandState.OK,
            ok_data="response_data",
        )

        # WHEN serializing the frame
        result = FrameParser.parse_from_frame_klass(frame)

        # THEN the frame type is CMD in the output
        assert result.startswith("< CMD ")

    # Tests for error conditions
    def test_serialize_master_frame_raises_error(self, master_frame):
        # GIVEN a frame that originates from master
        frame = master_frame

        # WHEN attempting to serialize it
        # THEN a FrameParsingError is raised
        with pytest.raises(FrameParsingError) as exc_info:
            FrameParser.parse_from_frame_klass(frame)

        assert "Cannot build frame from master frame" in str(exc_info.value)

    # Tests for checksum calculation
    def test_serialize_checksum_format(self, command_response_ok_with_data):
        # GIVEN any valid frame
        frame = command_response_ok_with_data

        # WHEN serializing the frame
        result = FrameParser.parse_from_frame_klass(frame)

        # THEN the checksum is correctly formatted
        parts = result.strip().split(" ")
        checksum = parts[-1]

        # Checksum should be 2 uppercase hex characters
        assert len(checksum) == 2
        assert all(c in "0123456789ABCDEF" for c in checksum)

    def test_serialize_checksum_is_calculated(self, ping_response_frame_ok):
        # GIVEN a frame
        frame = ping_response_frame_ok

        # WHEN serializing the frame
        result = FrameParser.parse_from_frame_klass(frame)

        # THEN the checksum matches the calculated value
        parts = result.strip().split(" ")
        checksum_in_result = parts[-1]

        # Rebuild the frame without checksum and newline
        frame_without_checksum = " ".join(parts[:-1])
        expected_checksum = Frame.build_checksum(frame_without_checksum.encode())
        expected_checksum_hex = f"{expected_checksum:02X}"

        assert checksum_in_result == expected_checksum_hex

    # Edge cases
    def test_serialize_with_empty_ok_data(self):
        # GIVEN a frame with None ok_data but OK state
        frame = Frame(
            frame_type=FrameType.ACK,
            device_uid="device444",
            command_id=15,
            from_master=False,
            command_state=CommandState.OK,
            ok_data=None,
        )

        # WHEN serializing the frame
        result = FrameParser.parse_from_frame_klass(frame)

        # THEN None is converted to string "None"
        assert "< ACK device444 15 OK None >" in result

    def test_serialize_with_complex_data_string(self):
        # GIVEN a frame with complex data containing special characters
        frame = Frame(
            frame_type=FrameType.ACK,
            device_uid="device555",
            command_id=20,
            from_master=False,
            command_state=CommandState.OK,
            ok_data="temp:23.5,humidity:65.2,pressure:1013.25",
        )

        # WHEN serializing the frame
        result = FrameParser.parse_from_frame_klass(frame)

        # THEN the complex data is preserved
        assert "temp:23.5,humidity:65.2,pressure:1013.25" in result


class TestFrameParserRoundTrip:
    """Tests for round-trip parsing: parse_from_master -> modify -> parse_from_frame_klass."""

    def test_roundtrip_command_parsing_and_response(self):
        # GIVEN a command frame string from master
        master_frame_str = "< CMD device123 5 get_sensor val1,val2 > 3C\n"

        # WHEN parsing the incoming frame
        parsed_frame = FrameParser.parse_from_master(master_frame_str)

        # AND creating a response frame based on parsed data
        response_frame = Frame(
            frame_type=FrameType.ACK,
            device_uid=parsed_frame.device_uid,
            command_id=parsed_frame.command_id,
            from_master=False,
            command_state=CommandState.OK,
            ok_data="sensor_reading:42.0",
        )

        # AND serializing the response
        response_str = FrameParser.parse_from_frame_klass(response_frame)

        # THEN the response string is correctly formatted
        assert response_str.startswith("< ACK device123 5 OK sensor_reading:42.0 >")
        assert response_str.endswith("\n")

    def test_roundtrip_ping_parsing_and_response(self):
        # GIVEN a ping frame from master
        ping_str = "< PING device999 0 ping > AB\n"

        # WHEN parsing the ping
        parsed_ping = FrameParser.parse_from_master(ping_str)

        # AND creating a ping response
        ping_response = Frame(
            frame_type=FrameType.ACK,
            device_uid=parsed_ping.device_uid,
            command_id=0,
            from_master=False,
            command_state=CommandState.OK,
            gd_fw_version="2.1.0",
            mp_fw_version="1.20.0",
        )

        # AND serializing the response
        response_str = FrameParser.parse_from_frame_klass(ping_response)

        # THEN the response contains firmware versions
        assert "GDFW=2.1.0" in response_str
        assert "MPFW=1.20.0" in response_str
        assert "< ACK device999 0 OK" in response_str
