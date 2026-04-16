# This test, test a lg_init frame complete workflow, from receiving a lg_init frame to sending the response.
# It is a high level test, that covers the handler and the parser.
# It is not a unit test, but an integration test.
import pytest

from src.core import DEVICE_UID
from src.core import command_store
from src.core import event_emitter
from src.core.models import Argument
from src.core.models import ModelType
from src.core.models import Order
from src.protocols.settings import ETX
from src.protocols.settings import STX
from src.protocols.usb.callback import cb_register
from src.protocols.usb.callback import on_order_process
from src.protocols.usb.callback import on_order_received
from src.protocols.usb.callback import on_response_ready
from src.protocols.usb.dataqueue import data_received as inbox
from src.protocols.usb.dataqueue import data_to_response as outbox
from src.protocols.usb.frame import CommandState
from src.protocols.usb.frame import Frame
from src.protocols.usb.frame import FrameType
from src.protocols.usb.handler import FrameHandler
from src.protocols.usb.parsers import FrameParser

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def build_lg_init_frame_str(device_uid: str, model: str, fields: str) -> str:
    """Build a valid raw LG_INIT frame string with correct checksum, as sent by master.

    Args:
        device_uid: The target device UID.
        model: The model name (e.g. "argument", "order").
        fields: Semicolon-separated field values (e.g. "1;pin_num;int;true;false").

    Returns:
        A complete frame string ending with newline, ready for parsing.
    """
    frame_without_cs = f"{STX} LG_INIT {device_uid} -1 {model} {fields} {ETX}"
    checksum = Frame.build_checksum(frame_without_cs.encode())
    return f"{frame_without_cs} {checksum:02X}\n"


# ---------------------------------------------------------------------------
# Test data
# ---------------------------------------------------------------------------

ARGUMENT_MODEL_NAME = "argument"
ARGUMENT_FIELDS = "1;pin_num;int;true;false"

ORDER_MODEL_NAME = "order"
ORDER_FIELDS = "1;get_temp;get;{arguments:1}"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def handler():
    """Fixture providing a FrameHandler instance."""
    return FrameHandler()


@pytest.fixture(autouse=True)
def setup_event_emitter():
    """Register all USB callbacks on the event emitter before each test and clean up after."""
    for cb in cb_register:
        event_emitter.on(cb.name, cb.func)
    yield
    for cb in cb_register:
        try:
            event_emitter.off(cb.name)
        except Exception:
            pass


@pytest.fixture(autouse=True)
def drain_queues():
    """Drain inbox and outbox queues before each test to ensure isolation."""
    while not inbox.empty():
        inbox.get_nowait()
    while not outbox.empty():
        outbox.get_nowait()
    yield


@pytest.fixture(autouse=True)
def clean_command_store():
    """Clear the command store before and after each test to ensure isolation."""
    command_store._args.clear()
    command_store._orders.clear()
    yield
    command_store._args.clear()
    command_store._orders.clear()


# -- Argument fixtures --


@pytest.fixture
def argument_raw_frame():
    """Fixture providing a valid raw LG_INIT frame string for the Argument model."""
    return build_lg_init_frame_str(DEVICE_UID, ARGUMENT_MODEL_NAME, ARGUMENT_FIELDS)


@pytest.fixture
def argument_raw_bytes(argument_raw_frame):
    """Fixture providing the Argument LG_INIT frame as raw bytes (simulating stdin read)."""
    return argument_raw_frame.encode("utf-8")


@pytest.fixture
def parsed_argument_frame(argument_raw_frame):
    """Fixture providing a Frame object parsed from the raw Argument LG_INIT frame."""
    return FrameParser.parse_from_master(argument_raw_frame)


# -- Order fixtures (require Argument to exist in command store) --


@pytest.fixture
def order_raw_frame():
    """Fixture providing a valid raw LG_INIT frame string for the Order model."""
    return build_lg_init_frame_str(DEVICE_UID, ORDER_MODEL_NAME, ORDER_FIELDS)


@pytest.fixture
def order_raw_bytes(order_raw_frame):
    """Fixture providing the Order LG_INIT frame as raw bytes (simulating stdin read)."""
    return order_raw_frame.encode("utf-8")


@pytest.fixture
def parsed_order_frame(order_raw_frame):
    """Fixture providing a Frame object parsed from the raw Order LG_INIT frame."""
    return FrameParser.parse_from_master(order_raw_frame)


@pytest.fixture
def preloaded_argument(handler, parsed_argument_frame):
    """Fixture that processes the Argument frame first, populating the command store.

    This is required before processing Order frames because Order references Argument IDs.
    """
    handler.handle_master_command(parsed_argument_frame)


# ---------------------------------------------------------------------------
# Tests – Parsing stage (Argument model)
# ---------------------------------------------------------------------------


class TestLgInitArgumentParsing:
    """Tests for parsing a raw LG_INIT Argument frame string into a Frame object."""

    def test_parsed_frame_type_is_lg_init(self, parsed_argument_frame):
        """Test that the parsed frame has LG_INIT type."""
        # GIVEN a raw LG_INIT frame string for Argument model (fixture)

        # WHEN it is parsed into a Frame object (fixture)

        # THEN frame_type is LG_INIT
        assert parsed_argument_frame.frame_type == FrameType.LG_INIT

    def test_parsed_frame_is_from_master(self, parsed_argument_frame):
        """Test that the parsed frame is marked as coming from master."""
        # GIVEN a parsed LG_INIT Argument frame (fixture)

        # WHEN we check from_master
        # THEN it is True
        assert parsed_argument_frame.from_master is True

    def test_parsed_command_id_is_minus_one(self, parsed_argument_frame):
        """Test that a LG_INIT frame has command_id -1."""
        # GIVEN a parsed LG_INIT Argument frame (fixture)

        # WHEN we check command_id
        # THEN it is -1
        assert parsed_argument_frame.command_id == -1

    def test_parsed_device_uid_matches(self, parsed_argument_frame):
        """Test that the device UID in the parsed frame matches the current device."""
        # GIVEN a parsed LG_INIT Argument frame targeting the current device (fixture)

        # WHEN we check device_uid
        # THEN it matches DEVICE_UID
        assert parsed_argument_frame.device_uid == DEVICE_UID

    def test_parsed_model_is_argument(self, parsed_argument_frame):
        """Test that the model type is correctly parsed as Argument."""
        # GIVEN a parsed LG_INIT Argument frame (fixture)

        # WHEN we check the model
        # THEN it is ModelType.ARGUMENT
        assert parsed_argument_frame.model == ModelType.ARGUMENT

    def test_parsed_model_attrs_values(self, parsed_argument_frame):
        """Test that model attribute values are correctly split from semicolons."""
        # GIVEN a parsed LG_INIT Argument frame with fields "1;pin_num;int;true;false"

        # WHEN we check model_attrs_values
        # THEN the tuple contains each field as a separate string
        assert parsed_argument_frame.model_attrs_values == ("1", "pin_num", "int", "true", "false")

    def test_is_init_order_returns_true(self, parsed_argument_frame):
        """Test that is_init_order() returns True for a LG_INIT frame."""
        # GIVEN a parsed LG_INIT Argument frame (fixture)

        # WHEN we call is_init_order()
        # THEN it returns True
        assert parsed_argument_frame.is_init_order() is True

    def test_is_not_ping_order(self, parsed_argument_frame):
        """Test that is_ping_order() returns False for a LG_INIT frame."""
        # GIVEN a parsed LG_INIT Argument frame (fixture)

        # WHEN we call is_ping_order()
        # THEN it returns False
        assert parsed_argument_frame.is_ping_order() is False

    def test_is_not_command_order(self, parsed_argument_frame):
        """Test that is_command_order() returns False for a LG_INIT frame."""
        # GIVEN a parsed LG_INIT Argument frame (fixture)

        # WHEN we call is_command_order()
        # THEN it returns False
        assert parsed_argument_frame.is_command_order() is False

    def test_checksum_verification_passes(self, parsed_argument_frame):
        """Test that the checksum of the parsed Argument frame is valid."""
        # GIVEN a parsed LG_INIT Argument frame built with a correct checksum (fixture)

        # WHEN we verify the checksum
        # THEN verification passes
        assert parsed_argument_frame.verify_checksum() is True


# ---------------------------------------------------------------------------
# Tests – Parsing stage (Order model)
# ---------------------------------------------------------------------------


class TestLgInitOrderParsing:
    """Tests for parsing a raw LG_INIT Order frame string into a Frame object."""

    def test_parsed_frame_type_is_lg_init(self, parsed_order_frame):
        """Test that the parsed frame has LG_INIT type."""
        # GIVEN a raw LG_INIT frame string for Order model (fixture)

        # WHEN it is parsed into a Frame object (fixture)

        # THEN frame_type is LG_INIT
        assert parsed_order_frame.frame_type == FrameType.LG_INIT

    def test_parsed_frame_is_from_master(self, parsed_order_frame):
        """Test that the parsed frame is marked as coming from master."""
        # GIVEN a parsed LG_INIT Order frame (fixture)

        # WHEN we check from_master
        # THEN it is True
        assert parsed_order_frame.from_master is True

    def test_parsed_command_id_is_minus_one(self, parsed_order_frame):
        """Test that a LG_INIT frame has command_id -1."""
        # GIVEN a parsed LG_INIT Order frame (fixture)

        # WHEN we check command_id
        # THEN it is -1
        assert parsed_order_frame.command_id == -1

    def test_parsed_model_is_order(self, parsed_order_frame):
        """Test that the model type is correctly parsed as Order."""
        # GIVEN a parsed LG_INIT Order frame (fixture)

        # WHEN we check the model
        # THEN it is ModelType.ORDER
        assert parsed_order_frame.model == ModelType.ORDER

    def test_parsed_model_attrs_values(self, parsed_order_frame):
        """Test that model attribute values are correctly split from semicolons."""
        # GIVEN a parsed LG_INIT Order frame with fields "1;get_temp;get;{arguments:1}"

        # WHEN we check model_attrs_values
        # THEN the tuple contains each field as a separate string
        assert parsed_order_frame.model_attrs_values == ("1", "get_temp", "get", "{arguments:1}")

    def test_is_init_order_returns_true(self, parsed_order_frame):
        """Test that is_init_order() returns True for a LG_INIT frame."""
        # GIVEN a parsed LG_INIT Order frame (fixture)

        # WHEN we call is_init_order()
        # THEN it returns True
        assert parsed_order_frame.is_init_order() is True

    def test_checksum_verification_passes(self, parsed_order_frame):
        """Test that the checksum of the parsed Order frame is valid."""
        # GIVEN a parsed LG_INIT Order frame built with a correct checksum (fixture)

        # WHEN we verify the checksum
        # THEN verification passes
        assert parsed_order_frame.verify_checksum() is True


# ---------------------------------------------------------------------------
# Tests – Handler stage (Argument model)
# ---------------------------------------------------------------------------


class TestLgInitArgumentHandler:
    """Tests for the handler processing a LG_INIT Argument frame and building the response."""

    def test_handler_returns_response_string(self, handler, parsed_argument_frame):
        """Test that the handler returns a non-empty response string."""
        # GIVEN a FrameHandler and a parsed LG_INIT Argument frame (fixtures)

        # WHEN the handler processes the frame
        response = handler.handle_master_command(parsed_argument_frame)

        # THEN a non-empty string is returned
        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    def test_response_contains_ack_frame_type(self, handler, parsed_argument_frame):
        """Test that the response frame type is ACK."""
        # GIVEN a handler processing a LG_INIT Argument frame
        response = handler.handle_master_command(parsed_argument_frame)

        # WHEN we inspect the response
        # THEN it contains ACK
        assert f"{STX} ACK" in response

    def test_response_contains_device_uid(self, handler, parsed_argument_frame):
        """Test that the response includes the device UID."""
        # GIVEN a handler processing a LG_INIT Argument frame
        response = handler.handle_master_command(parsed_argument_frame)

        # WHEN we inspect the response
        # THEN it contains the device UID
        assert DEVICE_UID in response

    def test_response_contains_command_id_minus_one(self, handler, parsed_argument_frame):
        """Test that the response preserves the LG_INIT command_id (-1)."""
        # GIVEN a handler processing a LG_INIT Argument frame
        response = handler.handle_master_command(parsed_argument_frame)

        # WHEN we inspect the response parts
        parts = response.strip().split(" ")

        # THEN command_id is -1
        assert parts[3] == "-1"

    def test_response_contains_ok_state(self, handler, parsed_argument_frame):
        """Test that the response frame has OK command state."""
        # GIVEN a handler processing a LG_INIT Argument frame
        response = handler.handle_master_command(parsed_argument_frame)

        # WHEN we inspect the response
        # THEN it contains OK state
        assert f" {CommandState.OK} " in response

    def test_response_ends_with_newline(self, handler, parsed_argument_frame):
        """Test that the response is newline-terminated for serial transmission."""
        # GIVEN a handler processing a LG_INIT Argument frame
        response = handler.handle_master_command(parsed_argument_frame)

        # WHEN we check the ending
        # THEN it ends with newline
        assert response.endswith("\n")

    def test_response_has_valid_checksum(self, handler, parsed_argument_frame):
        """Test that the checksum in the response frame is valid."""
        # GIVEN a handler processing a LG_INIT Argument frame
        response = handler.handle_master_command(parsed_argument_frame)

        # WHEN we extract response parts and verify the checksum
        response_stripped = response.removesuffix("\n")
        frame_part, cs_hex = response_stripped.rsplit(" ", 1)
        expected_cs = Frame.build_checksum(frame_part.encode())

        # THEN the checksum matches
        assert int(cs_hex, 16) == expected_cs

    def test_argument_added_to_command_store(self, handler, parsed_argument_frame):
        """Test that the Argument object is stored in command_store after handling."""
        # GIVEN a handler and a LG_INIT Argument frame

        # WHEN the handler processes the frame
        handler.handle_master_command(parsed_argument_frame)

        # THEN the argument is retrievable from the command store
        arg = command_store.get_arg(1)
        assert isinstance(arg, Argument)

    def test_stored_argument_has_correct_pk(self, handler, parsed_argument_frame):
        """Test that the stored Argument has the expected pk."""
        # GIVEN a handler processing a LG_INIT Argument frame with pk=1
        handler.handle_master_command(parsed_argument_frame)

        # WHEN we retrieve the argument
        arg = command_store.get_arg(1)

        # THEN pk is 1
        assert arg.pk == 1

    def test_stored_argument_has_correct_slug(self, handler, parsed_argument_frame):
        """Test that the stored Argument has the expected slug."""
        # GIVEN a handler processing a LG_INIT Argument frame with slug='pin_num'
        handler.handle_master_command(parsed_argument_frame)

        # WHEN we retrieve the argument
        arg = command_store.get_arg(1)

        # THEN slug is 'pin_num'
        assert arg.slug == "pin_num"

    def test_stored_argument_has_correct_value_type(self, handler, parsed_argument_frame):
        """Test that the stored Argument has the expected value_type."""
        # GIVEN a handler processing a LG_INIT Argument frame with value_type='int'
        handler.handle_master_command(parsed_argument_frame)

        # WHEN we retrieve the argument
        arg = command_store.get_arg(1)

        # THEN value_type is 'int'
        assert arg.value_type == "int"

    def test_stored_argument_has_correct_required_flag(self, handler, parsed_argument_frame):
        """Test that the stored Argument has the expected required flag."""
        # GIVEN a handler processing a LG_INIT Argument frame with required='true'
        handler.handle_master_command(parsed_argument_frame)

        # WHEN we retrieve the argument
        arg = command_store.get_arg(1)

        # THEN required is True (cast from string 'true')
        assert arg.required is True

    def test_stored_argument_has_correct_is_option_flag(self, handler, parsed_argument_frame):
        """Test that the stored Argument has the expected is_option flag."""
        # GIVEN a handler processing a LG_INIT Argument frame with is_option='false'
        handler.handle_master_command(parsed_argument_frame)

        # WHEN we retrieve the argument
        arg = command_store.get_arg(1)

        # THEN is_option is False (cast from string 'false')
        assert arg.is_option is False


# ---------------------------------------------------------------------------
# Tests – Handler stage (Order model)
# ---------------------------------------------------------------------------


class TestLgInitOrderHandler:
    """Tests for the handler processing a LG_INIT Order frame and building the response.

    All tests in this class use the preloaded_argument fixture to ensure
    the referenced Argument (pk=1) exists in the command store before
    the Order frame is processed.
    """

    def test_handler_returns_response_string(self, handler, parsed_order_frame, preloaded_argument):
        """Test that the handler returns a non-empty response string."""
        # GIVEN a FrameHandler, a pre-existing Argument in the store, and a parsed LG_INIT Order frame

        # WHEN the handler processes the frame
        response = handler.handle_master_command(parsed_order_frame)

        # THEN a non-empty string is returned
        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    def test_response_contains_ack_frame_type(self, handler, parsed_order_frame, preloaded_argument):
        """Test that the response frame type is ACK."""
        # GIVEN a handler processing a LG_INIT Order frame
        response = handler.handle_master_command(parsed_order_frame)

        # WHEN we inspect the response
        # THEN it contains ACK
        assert f"{STX} ACK" in response

    def test_response_contains_device_uid(self, handler, parsed_order_frame, preloaded_argument):
        """Test that the response includes the device UID."""
        # GIVEN a handler processing a LG_INIT Order frame
        response = handler.handle_master_command(parsed_order_frame)

        # WHEN we inspect the response
        # THEN it contains the device UID
        assert DEVICE_UID in response

    def test_response_contains_command_id_minus_one(self, handler, parsed_order_frame, preloaded_argument):
        """Test that the response preserves the LG_INIT command_id (-1)."""
        # GIVEN a handler processing a LG_INIT Order frame
        response = handler.handle_master_command(parsed_order_frame)

        # WHEN we inspect the response parts
        parts = response.strip().split(" ")

        # THEN command_id is -1
        assert parts[3] == "-1"

    def test_response_contains_ok_state(self, handler, parsed_order_frame, preloaded_argument):
        """Test that the response frame has OK command state."""
        # GIVEN a handler processing a LG_INIT Order frame
        response = handler.handle_master_command(parsed_order_frame)

        # WHEN we inspect the response
        # THEN it contains OK state
        assert f" {CommandState.OK} " in response

    def test_response_ends_with_newline(self, handler, parsed_order_frame, preloaded_argument):
        """Test that the response is newline-terminated for serial transmission."""
        # GIVEN a handler processing a LG_INIT Order frame
        response = handler.handle_master_command(parsed_order_frame)

        # WHEN we check the ending
        # THEN it ends with newline
        assert response.endswith("\n")

    def test_response_has_valid_checksum(self, handler, parsed_order_frame, preloaded_argument):
        """Test that the checksum in the response frame is valid."""
        # GIVEN a handler processing a LG_INIT Order frame
        response = handler.handle_master_command(parsed_order_frame)

        # WHEN we extract response parts and verify the checksum
        response_stripped = response.removesuffix("\n")
        frame_part, cs_hex = response_stripped.rsplit(" ", 1)
        expected_cs = Frame.build_checksum(frame_part.encode())

        # THEN the checksum matches
        assert int(cs_hex, 16) == expected_cs

    def test_order_added_to_command_store(self, handler, parsed_order_frame, preloaded_argument):
        """Test that the Order object is stored in command_store after handling."""
        # GIVEN a handler and a LG_INIT Order frame

        # WHEN the handler processes the frame
        handler.handle_master_command(parsed_order_frame)

        # THEN the order is retrievable from the command store
        order = command_store.get_order(1)
        assert isinstance(order, Order)

    def test_stored_order_has_correct_pk(self, handler, parsed_order_frame, preloaded_argument):
        """Test that the stored Order has the expected pk."""
        # GIVEN a handler processing a LG_INIT Order frame with pk=1
        handler.handle_master_command(parsed_order_frame)

        # WHEN we retrieve the order
        order = command_store.get_order(1)

        # THEN pk is 1
        assert order.pk == 1

    def test_stored_order_has_correct_slug(self, handler, parsed_order_frame, preloaded_argument):
        """Test that the stored Order has the expected slug."""
        # GIVEN a handler processing a LG_INIT Order frame with slug='get_temp'
        handler.handle_master_command(parsed_order_frame)

        # WHEN we retrieve the order
        order = command_store.get_order(1)

        # THEN slug is 'get_temp'
        assert order.slug == "get_temp"

    def test_stored_order_has_correct_action_type(self, handler, parsed_order_frame, preloaded_argument):
        """Test that the stored Order has the expected action_type."""
        # GIVEN a handler processing a LG_INIT Order frame with action_type='get'
        handler.handle_master_command(parsed_order_frame)

        # WHEN we retrieve the order
        order = command_store.get_order(1)

        # THEN action_type is 'get'
        assert order.action_type == "get"

    def test_stored_order_has_correct_arguments_relation(self, handler, parsed_order_frame, preloaded_argument):
        """Test that the stored Order has the expected arguments tuple referencing Argument pk=1."""
        # GIVEN a handler processing a LG_INIT Order frame with arguments referencing pk=1
        handler.handle_master_command(parsed_order_frame)

        # WHEN we retrieve the order
        order = command_store.get_order(1)

        # THEN arguments is a tuple containing the referenced argument pk
        assert order.arguments == (1,)

    def test_stored_order_arguments_match_existing_argument(self, handler, parsed_order_frame, preloaded_argument):
        """Test that the Order's argument IDs can be resolved from the command store."""
        # GIVEN a handler that has processed both Argument and Order frames
        handler.handle_master_command(parsed_order_frame)

        # WHEN we retrieve the order and its referenced argument
        order = command_store.get_order(1)
        referenced_arg = command_store.get_arg(order.arguments[0])

        # THEN the referenced argument exists and is valid
        assert isinstance(referenced_arg, Argument)
        assert referenced_arg.pk == 1
        assert referenced_arg.slug == "pin_num"


# ---------------------------------------------------------------------------
# Tests – Handler error cases
# ---------------------------------------------------------------------------


class TestLgInitHandlerErrors:
    """Tests for handler error cases during LG_INIT frame processing."""

    def test_wrong_device_uid_raises_exception(self, handler):
        """Test that a LG_INIT frame with a non-matching device UID raises an exception."""
        # GIVEN a LG_INIT frame targeting a different device
        raw_frame = build_lg_init_frame_str("wrong_device_uid", ARGUMENT_MODEL_NAME, ARGUMENT_FIELDS)
        frame = FrameParser.parse_from_master(raw_frame)

        # WHEN / THEN the handler raises an exception
        with pytest.raises(Exception, match="does not match"):
            handler.handle_master_command(frame)

    def test_invalid_checksum_raises_value_error(self, handler):
        """Test that a LG_INIT frame with a tampered checksum raises ValueError."""
        # GIVEN a LG_INIT frame with a deliberately wrong checksum
        frame_without_cs = f"{STX} LG_INIT {DEVICE_UID} -1 argument 1;pin_num;int;true;false {ETX}"
        bad_frame_str = f"{frame_without_cs} FF\n"
        frame = FrameParser.parse_from_master(bad_frame_str)

        # WHEN / THEN the handler raises a ValueError about checksum
        with pytest.raises(ValueError, match="Checksum verification failed"):
            handler.handle_master_command(frame)

    def test_unknown_device_uid_accepted(self, handler):
        """Test that a LG_INIT frame with UKW_DEV_UID is accepted."""
        # GIVEN a LG_INIT frame using the unknown device UID wildcard
        raw_frame = build_lg_init_frame_str("UKW_DEV_UID", ARGUMENT_MODEL_NAME, ARGUMENT_FIELDS)
        frame = FrameParser.parse_from_master(raw_frame)

        # WHEN the handler processes the frame
        response = handler.handle_master_command(frame)

        # THEN a valid response is returned
        assert response is not None
        assert f"{STX} ACK" in response

    def test_unsupported_model_raises_value_error(self, handler):
        """Test that a LG_INIT frame with an unsupported model raises ValueError."""
        # GIVEN a LG_INIT frame with an invalid model name
        # We build the frame manually to bypass from_string validation
        frame_without_cs = f"{STX} LG_INIT {DEVICE_UID} -1 argument 1;pin_num;int;true;false {ETX}"
        checksum = Frame.build_checksum(frame_without_cs.encode())
        raw_frame = f"{frame_without_cs} {checksum:02X}\n"
        frame = FrameParser.parse_from_master(raw_frame)

        # Manually override the model to an invalid value
        frame.model = "InvalidModel"

        # WHEN / THEN the handler raises a ValueError
        with pytest.raises(ValueError, match="not supported"):
            handler.handle_master_command(frame)

    def test_argument_not_stored_when_checksum_fails(self, handler):
        """Test that a failed checksum prevents Argument from being stored."""
        # GIVEN a LG_INIT Argument frame with a bad checksum
        frame_without_cs = f"{STX} LG_INIT {DEVICE_UID} -1 argument 1;pin_num;int;true;false {ETX}"
        bad_frame_str = f"{frame_without_cs} FF\n"
        frame = FrameParser.parse_from_master(bad_frame_str)

        # WHEN the handler rejects the frame
        with pytest.raises(ValueError):
            handler.handle_master_command(frame)

        # THEN the argument is NOT in the command store
        with pytest.raises(KeyError):
            command_store.get_arg(1)


# ---------------------------------------------------------------------------
# Tests – Full pipeline (end-to-end with event system and queues)
# ---------------------------------------------------------------------------


class TestLgInitFullPipeline:
    """End-to-end integration tests: raw bytes in -> event pipeline -> response in outbox."""

    @pytest.mark.asyncio
    async def test_argument_raw_bytes_to_inbox(self, argument_raw_bytes):
        """Test that on_order_received decodes raw bytes and queues them in inbox."""
        # GIVEN raw LG_INIT Argument bytes as received from stdin

        # WHEN on_order_received is called
        await on_order_received(argument_raw_bytes)

        # THEN the decoded string is available in the inbox queue
        assert not inbox.empty()
        queued_value = inbox.get_nowait()
        assert queued_value == argument_raw_bytes.decode("utf-8")

    @pytest.mark.asyncio
    async def test_argument_order_process_produces_response(self, parsed_argument_frame):
        """Test that on_order_process puts a response in the outbox queue for Argument."""
        # GIVEN a parsed LG_INIT Argument Frame object (fixture)

        # WHEN on_order_process is called
        await on_order_process(parsed_argument_frame)

        # THEN a response is ready in the outbox queue
        assert not outbox.empty()

    @pytest.mark.asyncio
    async def test_order_order_process_produces_response(self, handler, parsed_argument_frame, parsed_order_frame):
        """Test that on_order_process puts a response in the outbox queue for Order."""
        # GIVEN a pre-existing Argument in the store
        handler.handle_master_command(parsed_argument_frame)
        # Drain the outbox from the Argument response
        while not outbox.empty():
            outbox.get_nowait()

        # WHEN on_order_process is called for Order
        await on_order_process(parsed_order_frame)

        # THEN a response is ready in the outbox queue
        assert not outbox.empty()

    @pytest.mark.asyncio
    async def test_response_ready_puts_in_outbox(self):
        """Test that on_response_ready correctly queues the response string."""
        # GIVEN a response frame string
        fake_response = f"{STX} ACK test -1 OK {ETX} AB\n"

        # WHEN on_response_ready is called
        await on_response_ready(fake_response)

        # THEN the response is in the outbox
        assert not outbox.empty()
        assert outbox.get_nowait() == fake_response

    @pytest.mark.asyncio
    async def test_full_argument_pipeline_from_raw_bytes(self, argument_raw_bytes):
        """Test the complete Argument flow: raw bytes -> decode -> parse -> handle -> response queued."""
        # GIVEN raw LG_INIT Argument bytes

        # WHEN we simulate the full pipeline step by step
        # Step 1: Receive raw bytes -> decode and queue
        await on_order_received(argument_raw_bytes)

        # Step 2: Consume from inbox, parse, and process
        order_str = inbox.get_nowait()
        frame = FrameParser.parse_from_master(order_str)
        await on_order_process(frame)

        # THEN a valid response has been queued in the outbox
        assert not outbox.empty()
        response = outbox.get_nowait()
        assert isinstance(response, str)
        assert response.endswith("\n")

    @pytest.mark.asyncio
    async def test_full_argument_pipeline_response_content(self, argument_raw_bytes):
        """Test that the full Argument pipeline produces a correctly formatted ACK response."""
        # GIVEN raw LG_INIT Argument bytes going through the complete pipeline

        # WHEN processed end-to-end
        await on_order_received(argument_raw_bytes)
        order_str = inbox.get_nowait()
        frame = FrameParser.parse_from_master(order_str)
        await on_order_process(frame)
        response = outbox.get_nowait()

        # THEN the response contains all expected ACK response components
        assert f"{STX} ACK" in response
        assert DEVICE_UID in response
        assert CommandState.OK in response

    @pytest.mark.asyncio
    async def test_full_argument_pipeline_response_checksum_valid(self, argument_raw_bytes):
        """Test that the response generated by the full Argument pipeline has a valid checksum."""
        # GIVEN raw LG_INIT Argument bytes going through the complete pipeline

        # WHEN processed end-to-end
        await on_order_received(argument_raw_bytes)
        order_str = inbox.get_nowait()
        frame = FrameParser.parse_from_master(order_str)
        await on_order_process(frame)
        response = outbox.get_nowait()

        # THEN the checksum in the response is valid
        response_stripped = response.removesuffix("\n")
        frame_part, cs_hex = response_stripped.rsplit(" ", 1)
        expected_cs = Frame.build_checksum(frame_part.encode())
        assert int(cs_hex, 16) == expected_cs

    @pytest.mark.asyncio
    async def test_full_argument_pipeline_via_event_emitter(self, argument_raw_bytes):
        """Test the complete Argument flow driven entirely by event emissions."""
        # GIVEN raw LG_INIT Argument bytes and a fully wired event emitter (autouse fixture)

        # WHEN we emit 'order:received' (the entry point of the pipeline)
        await event_emitter.emit("order:received", argument_raw_bytes)

        # Step 2: manually drive inbox -> parse -> emit 'order:process'
        order_str = inbox.get_nowait()
        frame = FrameParser.parse_from_master(order_str)
        await event_emitter.emit("order:process", frame)

        # THEN the outbox contains the response
        assert not outbox.empty()
        response = outbox.get_nowait()
        assert f"{STX} ACK" in response

    @pytest.mark.asyncio
    async def test_full_order_pipeline_from_raw_bytes(self, handler, parsed_argument_frame, order_raw_bytes):
        """Test the complete Order flow: raw bytes -> decode -> parse -> handle -> response queued."""
        # GIVEN a pre-existing Argument in the store and raw LG_INIT Order bytes
        handler.handle_master_command(parsed_argument_frame)
        while not outbox.empty():
            outbox.get_nowait()

        # WHEN we simulate the full pipeline step by step
        await on_order_received(order_raw_bytes)
        order_str = inbox.get_nowait()
        frame = FrameParser.parse_from_master(order_str)
        await on_order_process(frame)

        # THEN a valid response has been queued in the outbox
        assert not outbox.empty()
        response = outbox.get_nowait()
        assert isinstance(response, str)
        assert response.endswith("\n")
        assert f"{STX} ACK" in response

    @pytest.mark.asyncio
    async def test_full_order_pipeline_via_event_emitter(self, handler, parsed_argument_frame, order_raw_bytes):
        """Test the complete Order flow driven entirely by event emissions."""
        # GIVEN a pre-existing Argument in the store
        handler.handle_master_command(parsed_argument_frame)
        while not outbox.empty():
            outbox.get_nowait()

        # WHEN we emit 'order:received' for Order bytes
        await event_emitter.emit("order:received", order_raw_bytes)
        order_str = inbox.get_nowait()
        frame = FrameParser.parse_from_master(order_str)
        await event_emitter.emit("order:process", frame)

        # THEN the outbox contains a valid ACK response
        assert not outbox.empty()
        response = outbox.get_nowait()
        assert f"{STX} ACK" in response
        assert DEVICE_UID in response


# ---------------------------------------------------------------------------
# Tests – Sequential Argument then Order pipeline (command store population)
# ---------------------------------------------------------------------------


class TestLgInitSequentialPipeline:
    """Integration tests verifying the correct sequential processing of Argument then Order.

    These tests simulate the real-world scenario where the backend sends
    Argument frames first, then Order frames that reference those Arguments.
    After both frames are processed, the command store must contain both entries.
    """

    @pytest.mark.asyncio
    async def test_sequential_pipeline_populates_argument_in_store(self):
        """Test that processing Argument frame first populates it in the command store."""
        # GIVEN raw LG_INIT Argument bytes
        arg_raw = build_lg_init_frame_str(DEVICE_UID, ARGUMENT_MODEL_NAME, ARGUMENT_FIELDS)

        # WHEN processed through the pipeline
        await on_order_received(arg_raw.encode("utf-8"))
        order_str = inbox.get_nowait()
        frame = FrameParser.parse_from_master(order_str)
        await on_order_process(frame)

        # THEN the Argument is in the command store
        arg = command_store.get_arg(1)
        assert arg.pk == 1
        assert arg.slug == "pin_num"

    @pytest.mark.asyncio
    async def test_sequential_pipeline_populates_order_in_store(self):
        """Test that processing Argument then Order populates both in the command store."""
        # GIVEN raw LG_INIT Argument bytes processed first
        arg_raw = build_lg_init_frame_str(DEVICE_UID, ARGUMENT_MODEL_NAME, ARGUMENT_FIELDS)
        await on_order_received(arg_raw.encode("utf-8"))
        arg_str = inbox.get_nowait()
        arg_frame = FrameParser.parse_from_master(arg_str)
        await on_order_process(arg_frame)
        # Drain outbox
        outbox.get_nowait()

        # WHEN raw LG_INIT Order bytes are processed
        order_raw = build_lg_init_frame_str(DEVICE_UID, ORDER_MODEL_NAME, ORDER_FIELDS)
        await on_order_received(order_raw.encode("utf-8"))
        order_str = inbox.get_nowait()
        order_frame = FrameParser.parse_from_master(order_str)
        await on_order_process(order_frame)

        # THEN the Order is in the command store
        order = command_store.get_order(1)
        assert order.pk == 1
        assert order.slug == "get_temp"
        assert order.action_type == "get"
        assert order.arguments == (1,)

    @pytest.mark.asyncio
    async def test_sequential_pipeline_both_stored_and_linked(self):
        """Test that after processing both frames, the Order references a valid Argument."""
        # GIVEN the full sequential pipeline: Argument then Order
        arg_raw = build_lg_init_frame_str(DEVICE_UID, ARGUMENT_MODEL_NAME, ARGUMENT_FIELDS)
        await on_order_received(arg_raw.encode("utf-8"))
        arg_str = inbox.get_nowait()
        arg_frame = FrameParser.parse_from_master(arg_str)
        await on_order_process(arg_frame)
        outbox.get_nowait()

        order_raw = build_lg_init_frame_str(DEVICE_UID, ORDER_MODEL_NAME, ORDER_FIELDS)
        await on_order_received(order_raw.encode("utf-8"))
        order_str = inbox.get_nowait()
        order_frame = FrameParser.parse_from_master(order_str)
        await on_order_process(order_frame)
        outbox.get_nowait()

        # WHEN we resolve the Order's argument references
        order = command_store.get_order(1)
        referenced_arg = command_store.get_arg(order.arguments[0])

        # THEN the Argument exists and matches the expected values
        assert isinstance(referenced_arg, Argument)
        assert referenced_arg.pk == 1
        assert referenced_arg.slug == "pin_num"
        assert referenced_arg.value_type == "int"
        assert referenced_arg.required is True
        assert referenced_arg.is_option is False

    @pytest.mark.asyncio
    async def test_sequential_pipeline_produces_two_ack_responses(self):
        """Test that both Argument and Order processing produce valid ACK responses."""
        # GIVEN the full sequential pipeline
        arg_raw = build_lg_init_frame_str(DEVICE_UID, ARGUMENT_MODEL_NAME, ARGUMENT_FIELDS)
        await on_order_received(arg_raw.encode("utf-8"))
        arg_str = inbox.get_nowait()
        arg_frame = FrameParser.parse_from_master(arg_str)
        await on_order_process(arg_frame)

        # WHEN we collect the first response
        arg_response = outbox.get_nowait()

        # AND process the Order frame
        order_raw = build_lg_init_frame_str(DEVICE_UID, ORDER_MODEL_NAME, ORDER_FIELDS)
        await on_order_received(order_raw.encode("utf-8"))
        order_str = inbox.get_nowait()
        order_frame = FrameParser.parse_from_master(order_str)
        await on_order_process(order_frame)
        order_response = outbox.get_nowait()

        # THEN both responses are valid ACK frames
        for response in (arg_response, order_response):
            assert f"{STX} ACK" in response
            assert DEVICE_UID in response
            assert CommandState.OK in response
            assert response.endswith("\n")

            # Verify checksums
            response_stripped = response.removesuffix("\n")
            frame_part, cs_hex = response_stripped.rsplit(" ", 1)
            expected_cs = Frame.build_checksum(frame_part.encode())
            assert int(cs_hex, 16) == expected_cs

    @pytest.mark.asyncio
    async def test_sequential_pipeline_via_event_emitter(self):
        """Test the complete sequential flow driven entirely by event emissions."""
        # GIVEN raw LG_INIT bytes for Argument then Order

        # WHEN Argument is processed via event emitter
        arg_raw = build_lg_init_frame_str(DEVICE_UID, ARGUMENT_MODEL_NAME, ARGUMENT_FIELDS)
        await event_emitter.emit("order:received", arg_raw.encode("utf-8"))
        arg_str = inbox.get_nowait()
        arg_frame = FrameParser.parse_from_master(arg_str)
        await event_emitter.emit("order:process", arg_frame)
        outbox.get_nowait()

        # AND Order is processed via event emitter
        order_raw = build_lg_init_frame_str(DEVICE_UID, ORDER_MODEL_NAME, ORDER_FIELDS)
        await event_emitter.emit("order:received", order_raw.encode("utf-8"))
        order_str = inbox.get_nowait()
        order_frame = FrameParser.parse_from_master(order_str)
        await event_emitter.emit("order:process", order_frame)

        # THEN the outbox contains the Order response
        assert not outbox.empty()
        response = outbox.get_nowait()
        assert f"{STX} ACK" in response

        # AND the command store contains both Argument and Order
        arg = command_store.get_arg(1)
        order = command_store.get_order(1)
        assert arg.slug == "pin_num"
        assert order.slug == "get_temp"
        assert order.arguments == (1,)
