import pytest

from src.core.dataclass import FrozenDataclass
from src.protocols.errors import CommandError
from src.protocols.settings import ETX
from src.protocols.settings import STX
from src.protocols.usb.callback import FrozRegisterCB
from src.protocols.usb.callback import cb_register
from src.protocols.usb.callback import on_error_occurred
from src.protocols.usb.callback import on_order_process
from src.protocols.usb.callback import on_order_received
from src.protocols.usb.callback import on_response_ready
from src.protocols.usb.frame import CommandState
from src.protocols.usb.frame import Frame
from src.protocols.usb.frame import FrameType

# ---------------------------------------------------------------------------
# Tests – FrozRegisterCB
# ---------------------------------------------------------------------------


class TestFrozRegisterCB:
    """Tests verifying the FrozRegisterCB frozen dataclass."""

    def test_is_frozen_dataclass_subclass(self):
        """Verify that FrozRegisterCB is a subclass of FrozenDataclass."""
        # GIVEN: The FrozRegisterCB class definition
        # WHEN: Checking its base classes
        # THEN: It inherits from FrozenDataclass
        assert issubclass(FrozRegisterCB, FrozenDataclass)

    def test_stores_name_and_func_correctly(self):
        """Verify that name and func are stored and accessible after instantiation."""
        # GIVEN: A callback function and an event name
        cb = lambda: None  # noqa: E731

        # WHEN: Creating a FrozRegisterCB instance
        entry = FrozRegisterCB(name="my_event", func=cb)

        # THEN: Both fields hold the provided values
        assert entry.name == "my_event"
        assert entry.func is cb

    def test_name_field_is_immutable(self):
        """Verify that the name field cannot be modified after instantiation."""
        # GIVEN: A FrozRegisterCB instance
        entry = FrozRegisterCB(name="my_event", func=lambda: None)

        # WHEN: Attempting to overwrite name
        # THEN: AttributeError is raised
        with pytest.raises(AttributeError):
            entry.name = "other_event"

    def test_func_field_is_immutable(self):
        """Verify that the func field cannot be modified after instantiation."""
        # GIVEN: A FrozRegisterCB instance
        entry = FrozRegisterCB(name="my_event", func=lambda: None)

        # WHEN: Attempting to overwrite func
        # THEN: AttributeError is raised
        with pytest.raises(AttributeError):
            entry.func = lambda: None


# ---------------------------------------------------------------------------
# Tests – on_order_received
# ---------------------------------------------------------------------------


class TestOnOrderReceived:
    """Tests verifying the on_order_received callback."""

    async def test_decodes_bytes_and_puts_in_data_received(self, mocker):
        """Verify that raw bytes are decoded to UTF-8 and put into data_received."""
        # GIVEN: Mocked data_received queue and raw bytes
        mock_queue = mocker.patch("src.protocols.usb.callback.data_received")
        mock_queue.put = mocker.AsyncMock()

        # WHEN: Calling on_order_received with bytes data
        await on_order_received(b"hello world")

        # THEN: data_received.put is called once with the decoded UTF-8 string
        mock_queue.put.assert_called_once_with("hello world")

    async def test_decodes_multibyte_utf8_correctly(self, mocker):
        """Verify that multi-byte UTF-8 sequences are decoded correctly."""
        # GIVEN: UTF-8 bytes containing non-ASCII characters
        mock_queue = mocker.patch("src.protocols.usb.callback.data_received")
        mock_queue.put = mocker.AsyncMock()
        raw_data = "café".encode("utf-8")

        # WHEN: Calling on_order_received
        await on_order_received(raw_data)

        # THEN: The decoded string is forwarded unaltered
        mock_queue.put.assert_called_once_with("café")

    async def test_calls_put_exactly_once(self, mocker):
        """Verify that data_received.put is called exactly once per invocation."""
        # GIVEN: Mocked data_received queue
        mock_queue = mocker.patch("src.protocols.usb.callback.data_received")
        mock_queue.put = mocker.AsyncMock()

        # WHEN: Calling on_order_received once
        await on_order_received(b"frame_data")

        # THEN: put is called exactly once
        assert mock_queue.put.call_count == 1

    async def test_returns_none(self, mocker):
        """Verify that on_order_received returns None."""
        # GIVEN: Mocked data_received queue
        mock_queue = mocker.patch("src.protocols.usb.callback.data_received")
        mock_queue.put = mocker.AsyncMock()

        # WHEN: Calling on_order_received
        result = await on_order_received(b"data")

        # THEN: The return value is None
        assert result is None


# ---------------------------------------------------------------------------
# Tests – on_order_process
# ---------------------------------------------------------------------------


class TestOnOrderProcess:
    """Tests verifying the on_order_process callback."""

    async def test_emits_response_ready_when_handler_returns_frame(self, mocker):
        """Verify that response:ready is emitted when frame_handler returns a result."""
        # GIVEN: frame_handler returning a valid frame string and mocked event_emitter
        mock_handler = mocker.patch("src.protocols.usb.callback.frame_handler")
        mock_handler.handle_master_command.return_value = "< ACK uid 0 OK > FF\n"
        mock_emitter = mocker.patch("src.protocols.usb.callback.event_emitter")
        mock_emitter.emit = mocker.AsyncMock()
        order = mocker.MagicMock(spec=Frame)

        # WHEN: Calling on_order_process
        await on_order_process(order)

        # THEN: event_emitter.emit is called with response:ready and the frame string
        mock_emitter.emit.assert_called_once_with("response:ready", "< ACK uid 0 OK > FF\n")

    async def test_emits_error_occurred_when_handler_returns_none(self, mocker):
        """Verify that error:occurred is emitted when frame_handler returns None."""
        # GIVEN: frame_handler returning None and mocked event_emitter
        mock_handler = mocker.patch("src.protocols.usb.callback.frame_handler")
        mock_handler.handle_master_command.return_value = None
        mock_emitter = mocker.patch("src.protocols.usb.callback.event_emitter")
        mock_emitter.emit = mocker.AsyncMock()
        order = mocker.MagicMock(spec=Frame)

        # WHEN: Calling on_order_process
        await on_order_process(order)

        # THEN: event_emitter.emit is called with error:occurred and the expected arguments
        mock_emitter.emit.assert_called_once_with(
            "error:occurred",
            "Cannot handle and process the command. No response generated.",
            CommandError.UNKNOW_ERR,
            order,
        )

    async def test_does_not_emit_response_ready_when_handler_returns_none(self, mocker):
        """Verify that response:ready is NOT emitted when frame_handler returns None."""
        # GIVEN: frame_handler returning None
        mock_handler = mocker.patch("src.protocols.usb.callback.frame_handler")
        mock_handler.handle_master_command.return_value = None
        mock_emitter = mocker.patch("src.protocols.usb.callback.event_emitter")
        mock_emitter.emit = mocker.AsyncMock()
        order = mocker.MagicMock(spec=Frame)

        # WHEN: Calling on_order_process
        await on_order_process(order)

        # THEN: response:ready is never emitted
        emitted_events = [call.args[0] for call in mock_emitter.emit.call_args_list]
        assert "response:ready" not in emitted_events

    async def test_calls_handle_master_command_with_order(self, mocker):
        """Verify that frame_handler.handle_master_command is called with the provided order."""
        # GIVEN: Mocked frame_handler and event_emitter
        mock_handler = mocker.patch("src.protocols.usb.callback.frame_handler")
        mock_handler.handle_master_command.return_value = "some_frame"
        mock_emitter = mocker.patch("src.protocols.usb.callback.event_emitter")
        mock_emitter.emit = mocker.AsyncMock()
        order = mocker.MagicMock(spec=Frame)

        # WHEN: Calling on_order_process
        await on_order_process(order)

        # THEN: handle_master_command is called exactly once with the order object
        mock_handler.handle_master_command.assert_called_once_with(order)

    async def test_returns_none(self, mocker):
        """Verify that on_order_process returns None in all cases."""
        # GIVEN: frame_handler returning a frame string
        mock_handler = mocker.patch("src.protocols.usb.callback.frame_handler")
        mock_handler.handle_master_command.return_value = "< ACK uid 0 OK > FF\n"
        mock_emitter = mocker.patch("src.protocols.usb.callback.event_emitter")
        mock_emitter.emit = mocker.AsyncMock()

        # WHEN: Calling on_order_process
        result = await on_order_process(mocker.MagicMock(spec=Frame))

        # THEN: The return value is None
        assert result is None


# ---------------------------------------------------------------------------
# Tests – on_error_occurred
# ---------------------------------------------------------------------------


class TestOnErrorOccurred:
    """Tests verifying the on_error_occurred callback."""

    async def test_formats_error_message_replaces_spaces_with_underscores(self, mocker):
        """Verify that spaces in the error message are replaced with underscores."""
        # GIVEN: An error message containing spaces and a Frame trigger_order
        mock_parser = mocker.patch("src.protocols.usb.callback.FrameParser")
        mock_parser.parse_from_frame_klass.return_value = "frame_str\n"
        mock_emitter = mocker.patch("src.protocols.usb.callback.event_emitter")
        mock_emitter.emit = mocker.AsyncMock()
        trigger_order = mocker.MagicMock(spec=Frame)
        trigger_order.device_uid = "uid123"
        trigger_order.command_id = 42

        # WHEN: Calling on_error_occurred with a spaced error message
        await on_error_occurred("sensor read error", "ERR_TYPE", trigger_order)

        # THEN: The created frame has underscores instead of spaces in err_msg
        created_frame = mock_parser.parse_from_frame_klass.call_args[0][0]
        assert "sensor_read_error" in created_frame.err_msg
        assert "sensor read error" not in created_frame.err_msg

    async def test_formats_error_message_prepends_error_type(self, mocker):
        """Verify that the error type is prepended to the formatted error message."""
        # GIVEN: A specific error type and message
        mock_parser = mocker.patch("src.protocols.usb.callback.FrameParser")
        mock_parser.parse_from_frame_klass.return_value = "frame_str\n"
        mock_emitter = mocker.patch("src.protocols.usb.callback.event_emitter")
        mock_emitter.emit = mocker.AsyncMock()
        trigger_order = mocker.MagicMock(spec=Frame)
        trigger_order.device_uid = "uid"
        trigger_order.command_id = 1

        # WHEN: Calling on_error_occurred
        await on_error_occurred("failed", "UNKNOW_ERR", trigger_order)

        # THEN: The err_msg is formatted as "error_type::formatted_message"
        created_frame = mock_parser.parse_from_frame_klass.call_args[0][0]
        assert created_frame.err_msg == "UNKNOW_ERR::failed"

    async def test_with_frame_trigger_creates_ack_error_frame(self, mocker):
        """Verify that when trigger_order is a Frame, an ACK/ERROR frame is created."""
        # GIVEN: A mocked Frame as trigger_order
        mock_parser = mocker.patch("src.protocols.usb.callback.FrameParser")
        mock_parser.parse_from_frame_klass.return_value = "frame_str\n"
        mock_emitter = mocker.patch("src.protocols.usb.callback.event_emitter")
        mock_emitter.emit = mocker.AsyncMock()
        trigger_order = mocker.MagicMock(spec=Frame)
        trigger_order.device_uid = "uid"
        trigger_order.command_id = 10

        # WHEN: Calling on_error_occurred with a Frame trigger
        await on_error_occurred("error", "ERR", trigger_order)

        # THEN: The created frame is an ACK frame in ERROR command state
        created_frame = mock_parser.parse_from_frame_klass.call_args[0][0]
        assert created_frame.frame_type == FrameType.ACK
        assert created_frame.command_state == CommandState.ERROR

    async def test_with_frame_trigger_reuses_frame_device_uid_and_command_id(self, mocker):
        """Verify that when trigger_order is a Frame, its device_uid and command_id are reused."""
        # GIVEN: A mocked Frame trigger with specific device_uid and command_id
        mock_parser = mocker.patch("src.protocols.usb.callback.FrameParser")
        mock_parser.parse_from_frame_klass.return_value = "frame_str\n"
        mock_emitter = mocker.patch("src.protocols.usb.callback.event_emitter")
        mock_emitter.emit = mocker.AsyncMock()
        trigger_order = mocker.MagicMock(spec=Frame)
        trigger_order.device_uid = "dev_abc"
        trigger_order.command_id = 99

        # WHEN: Calling on_error_occurred
        await on_error_occurred("an error", "ERR_TYPE", trigger_order)

        # THEN: The error frame carries the trigger frame's device_uid and command_id
        created_frame = mock_parser.parse_from_frame_klass.call_args[0][0]
        assert created_frame.device_uid == "dev_abc"
        assert created_frame.command_id == 99

    async def test_with_string_trigger_uses_device_uid_and_minus_502(self, mocker):
        """Verify that the string branch uses DEVICE_UID and command_id=-502."""
        # GIVEN: A plain string as trigger_order and DEVICE_UID patched to a known value
        mock_parser = mocker.patch("src.protocols.usb.callback.FrameParser")
        mock_parser.parse_from_frame_klass.return_value = "frame_str\n"
        mock_emitter = mocker.patch("src.protocols.usb.callback.event_emitter")
        mock_emitter.emit = mocker.AsyncMock()
        mocker.patch("src.protocols.usb.callback.DEVICE_UID", "test_uid")

        # WHEN: Calling on_error_occurred with a simple string
        await on_error_occurred("err", "ERR_TYPE", "some order")

        # THEN: The created frame uses the patched DEVICE_UID and command_id=-502
        created_frame = mock_parser.parse_from_frame_klass.call_args[0][0]
        assert created_frame.device_uid == "test_uid"
        assert created_frame.command_id == -502

    async def test_with_string_trigger_strips_trailing_newline(self, mocker):
        """Verify that a trailing newline is stripped from the string trigger_order."""
        # GIVEN: A string trigger ending with \n and no STX/ETX
        mock_parser = mocker.patch("src.protocols.usb.callback.FrameParser")
        mock_parser.parse_from_frame_klass.return_value = "frame_str\n"
        mock_emitter = mocker.patch("src.protocols.usb.callback.event_emitter")
        mock_emitter.emit = mocker.AsyncMock()

        # WHEN: Calling on_error_occurred with a newline-terminated string
        await on_error_occurred("err", "ERR_TYPE", "plain order\n")

        # THEN: The string branch is used (command_id=-502)
        created_frame = mock_parser.parse_from_frame_klass.call_args[0][0]
        assert created_frame.command_id == -502

    async def test_with_full_frame_string_trigger_formats_order_reference(self, mocker):
        """Verify that STX, ETX, and checksum are stripped and spaces replaced by dashes."""
        # GIVEN: A full raw USB frame string as trigger_order
        mock_parser = mocker.patch("src.protocols.usb.callback.FrameParser")
        mock_parser.parse_from_frame_klass.return_value = "frame_str\n"
        mock_emitter = mocker.patch("src.protocols.usb.callback.event_emitter")
        mock_emitter.emit = mocker.AsyncMock()
        raw_frame = f"{STX} CMD uid 42 get_temp {ETX} AG\n"

        # WHEN: Calling on_error_occurred with the full frame string
        await on_error_occurred("err", "ERR_TYPE", raw_frame)

        # THEN: The err_msg contains a dash-formatted order reference
        created_frame = mock_parser.parse_from_frame_klass.call_args[0][0]
        assert "CMD-uid-42-get_temp" in created_frame.err_msg

    async def test_emits_response_ready_with_parsed_frame_string(self, mocker):
        """Verify that response:ready is emitted with the string returned by FrameParser."""
        # GIVEN: FrameParser returning a known frame string
        mock_parser = mocker.patch("src.protocols.usb.callback.FrameParser")
        mock_parser.parse_from_frame_klass.return_value = "< ACK uid 10 ERR > FF\n"
        mock_emitter = mocker.patch("src.protocols.usb.callback.event_emitter")
        mock_emitter.emit = mocker.AsyncMock()
        trigger_order = mocker.MagicMock(spec=Frame)
        trigger_order.device_uid = "uid"
        trigger_order.command_id = 10

        # WHEN: Calling on_error_occurred
        await on_error_occurred("error", "ERR", trigger_order)

        # THEN: response:ready is emitted with the exact parsed frame string
        mock_emitter.emit.assert_called_once_with("response:ready", "< ACK uid 10 ERR > FF\n")

    async def test_returns_none(self, mocker):
        """Verify that on_error_occurred always returns None."""
        # GIVEN: Mocked FrameParser and event_emitter
        mock_parser = mocker.patch("src.protocols.usb.callback.FrameParser")
        mock_parser.parse_from_frame_klass.return_value = "frame\n"
        mock_emitter = mocker.patch("src.protocols.usb.callback.event_emitter")
        mock_emitter.emit = mocker.AsyncMock()
        trigger_order = mocker.MagicMock(spec=Frame)
        trigger_order.device_uid = "uid"
        trigger_order.command_id = 1

        # WHEN: Calling on_error_occurred
        result = await on_error_occurred("error", "ERR", trigger_order)

        # THEN: The return value is None
        assert result is None


# ---------------------------------------------------------------------------
# Tests – on_response_ready
# ---------------------------------------------------------------------------


class TestOnResponseReady:
    """Tests verifying the on_response_ready callback."""

    async def test_puts_frame_data_in_data_to_response(self, mocker):
        """Verify that the frame response data is put into data_to_response."""
        # GIVEN: Mocked data_to_response queue and a frame string
        mock_queue = mocker.patch("src.protocols.usb.callback.data_to_response")
        mock_queue.put = mocker.AsyncMock()

        # WHEN: Calling on_response_ready
        await on_response_ready("< ACK uid 0 OK > FF\n")

        # THEN: data_to_response.put is called once with the exact frame string
        mock_queue.put.assert_called_once_with("< ACK uid 0 OK > FF\n")

    async def test_does_not_modify_frame_data(self, mocker):
        """Verify that the frame data is forwarded to the queue unmodified."""
        # GIVEN: A frame string with special characters
        mock_queue = mocker.patch("src.protocols.usb.callback.data_to_response")
        mock_queue.put = mocker.AsyncMock()
        frame_data = "< ACK dev_uid 42 OK some_data > 3F\n"

        # WHEN: Calling on_response_ready
        await on_response_ready(frame_data)

        # THEN: The exact string is passed to the queue unchanged
        mock_queue.put.assert_called_once_with(frame_data)

    async def test_calls_put_exactly_once(self, mocker):
        """Verify that data_to_response.put is called exactly once per invocation."""
        # GIVEN: Mocked data_to_response queue
        mock_queue = mocker.patch("src.protocols.usb.callback.data_to_response")
        mock_queue.put = mocker.AsyncMock()

        # WHEN: Calling on_response_ready once
        await on_response_ready("frame data")

        # THEN: put is called exactly once
        assert mock_queue.put.call_count == 1

    async def test_returns_none(self, mocker):
        """Verify that on_response_ready returns None."""
        # GIVEN: Mocked data_to_response queue
        mock_queue = mocker.patch("src.protocols.usb.callback.data_to_response")
        mock_queue.put = mocker.AsyncMock()

        # WHEN: Calling on_response_ready
        result = await on_response_ready("frame data")

        # THEN: The return value is None
        assert result is None


# ---------------------------------------------------------------------------
# Tests – cb_register
# ---------------------------------------------------------------------------


class TestCbRegister:
    """Tests verifying the cb_register tuple structure."""

    def test_cb_register_is_a_tuple(self):
        """Verify that cb_register is a tuple."""
        # GIVEN: The module-level cb_register
        # WHEN: Checking its type
        # THEN: It is a tuple
        assert isinstance(cb_register, tuple)

    def test_cb_register_contains_four_entries(self):
        """Verify that cb_register holds exactly four callback entries."""
        # GIVEN: The cb_register tuple
        # WHEN: Counting its entries
        # THEN: There are exactly four entries
        assert len(cb_register) == 4

    def test_all_entries_are_froz_register_cb_instances(self):
        """Verify that every entry in cb_register is a FrozRegisterCB instance."""
        # GIVEN: The cb_register tuple
        # WHEN: Checking the type of each entry
        # THEN: All entries are FrozRegisterCB instances
        for entry in cb_register:
            assert isinstance(entry, FrozRegisterCB)

    def test_cb_register_contains_expected_event_names(self):
        """Verify that the four expected protocol event names are present."""
        # GIVEN: The cb_register tuple
        # WHEN: Extracting all event names
        names = [entry.name for entry in cb_register]

        # THEN: All expected event names are registered
        assert "order:received" in names
        assert "order:process" in names
        assert "response:ready" in names
        assert "error:occurred" in names

    def test_each_entry_references_the_correct_function(self):
        """Verify that each entry maps its event name to the correct callback function."""
        # GIVEN: A lookup dict built from cb_register
        registry = {entry.name: entry.func for entry in cb_register}

        # WHEN: Checking each function reference
        # THEN: Each name maps to its corresponding callback
        assert registry["order:received"] is on_order_received
        assert registry["order:process"] is on_order_process
        assert registry["response:ready"] is on_response_ready
        assert registry["error:occurred"] is on_error_occurred

    def test_cb_register_entries_are_immutable(self):
        """Verify that cb_register cannot be mutated (tuples are immutable)."""
        # GIVEN: The cb_register tuple
        # WHEN: Attempting to replace an entry
        # THEN: TypeError is raised
        with pytest.raises(TypeError):
            cb_register[0] = None  # type: ignore[index]
