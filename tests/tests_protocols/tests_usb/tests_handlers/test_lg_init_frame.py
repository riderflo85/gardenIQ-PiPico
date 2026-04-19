# This test, test a lg_init frame complete workflow, from receiving a lg_init frame to sending the response.
# It is a high level test, that covers the handler and the parser.
# It is not a unit test, but an integration test.
import pytest

from src.core import DEVICE_UID
from src.core import command_store
from src.core import event_emitter
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
        model: The model name (e.g. "order").
        fields: Semicolon-separated field values (e.g. "1;get_temp;get").

    Returns:
        A complete frame string ending with newline, ready for parsing.
    """
    frame_without_cs = f"{STX} LG_INIT {device_uid} -1 {model} {fields} {ETX}"
    checksum = Frame.build_checksum(frame_without_cs.encode())
    return f"{frame_without_cs} {checksum:02X}\n"


# ---------------------------------------------------------------------------
# Test data
# ---------------------------------------------------------------------------

ORDER_MODEL_NAME = "order"
ORDER_FIELDS = "1;get_temp;get;5;-1;False;"


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
    command_store._orders.clear()
    yield
    command_store._orders.clear()


# -- Order fixtures --


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
        # GIVEN a parsed LG_INIT Order frame with fields "1;get_temp;get;5;-1;False;"

        # WHEN we check model_attrs_values
        # THEN the tuple contains each field as a separate string
        assert parsed_order_frame.model_attrs_values == ("1", "get_temp", "get", "5", "-1", "False", "")

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
# Tests – Handler stage (Order model)
# ---------------------------------------------------------------------------


class TestLgInitOrderHandler:
    """Tests for the handler processing a LG_INIT Order frame and building the response."""

    def test_handler_returns_response_string(self, handler, parsed_order_frame):
        """Test that the handler returns a non-empty response string."""
        # GIVEN a FrameHandler and a parsed LG_INIT Order frame (fixtures)

        # WHEN the handler processes the frame
        response = handler.handle_master_command(parsed_order_frame)

        # THEN a non-empty string is returned
        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    def test_response_contains_ack_frame_type(self, handler, parsed_order_frame):
        """Test that the response frame type is ACK."""
        # GIVEN a handler processing a LG_INIT Order frame
        response = handler.handle_master_command(parsed_order_frame)

        # WHEN we inspect the response
        # THEN it contains ACK
        assert f"{STX} ACK" in response

    def test_response_contains_device_uid(self, handler, parsed_order_frame):
        """Test that the response includes the device UID."""
        # GIVEN a handler processing a LG_INIT Order frame
        response = handler.handle_master_command(parsed_order_frame)

        # WHEN we inspect the response
        # THEN it contains the device UID
        assert DEVICE_UID in response

    def test_response_contains_command_id_minus_one(self, handler, parsed_order_frame):
        """Test that the response preserves the LG_INIT command_id (-1)."""
        # GIVEN a handler processing a LG_INIT Order frame
        response = handler.handle_master_command(parsed_order_frame)

        # WHEN we inspect the response parts
        parts = response.strip().split(" ")

        # THEN command_id is -1
        assert parts[3] == "-1"

    def test_response_contains_ok_state(self, handler, parsed_order_frame):
        """Test that the response frame has OK command state."""
        # GIVEN a handler processing a LG_INIT Order frame
        response = handler.handle_master_command(parsed_order_frame)

        # WHEN we inspect the response
        # THEN it contains OK state
        assert f" {CommandState.OK} " in response

    def test_response_ends_with_newline(self, handler, parsed_order_frame):
        """Test that the response is newline-terminated for serial transmission."""
        # GIVEN a handler processing a LG_INIT Order frame
        response = handler.handle_master_command(parsed_order_frame)

        # WHEN we check the ending
        # THEN it ends with newline
        assert response.endswith("\n")

    def test_response_has_valid_checksum(self, handler, parsed_order_frame):
        """Test that the checksum in the response frame is valid."""
        # GIVEN a handler processing a LG_INIT Order frame
        response = handler.handle_master_command(parsed_order_frame)

        # WHEN we extract response parts and verify the checksum
        response_stripped = response.removesuffix("\n")
        frame_part, cs_hex = response_stripped.rsplit(" ", 1)
        expected_cs = Frame.build_checksum(frame_part.encode())

        # THEN the checksum matches
        assert int(cs_hex, 16) == expected_cs

    def test_order_added_to_command_store(self, handler, parsed_order_frame):
        """Test that the Order object is stored in command_store after handling."""
        # GIVEN a handler and a LG_INIT Order frame

        # WHEN the handler processes the frame
        handler.handle_master_command(parsed_order_frame)

        # THEN the order is retrievable from the command store
        order = command_store.get_order(1)
        assert isinstance(order, Order)

    def test_stored_order_has_correct_pk(self, handler, parsed_order_frame):
        """Test that the stored Order has the expected pk."""
        # GIVEN a handler processing a LG_INIT Order frame with pk=1
        handler.handle_master_command(parsed_order_frame)

        # WHEN we retrieve the order
        order = command_store.get_order(1)

        # THEN pk is 1
        assert order.pk == 1

    def test_stored_order_has_correct_slug(self, handler, parsed_order_frame):
        """Test that the stored Order has the expected slug."""
        # GIVEN a handler processing a LG_INIT Order frame with slug='get_temp'
        handler.handle_master_command(parsed_order_frame)

        # WHEN we retrieve the order
        order = command_store.get_order(1)

        # THEN slug is 'get_temp'
        assert order.slug == "get_temp"

    def test_stored_order_has_correct_action_type(self, handler, parsed_order_frame):
        """Test that the stored Order has the expected action_type."""
        # GIVEN a handler processing a LG_INIT Order frame with action_type='get'
        handler.handle_master_command(parsed_order_frame)

        # WHEN we retrieve the order
        order = command_store.get_order(1)

        # THEN action_type is 'get'
        assert order.action_type == "get"

    def test_stored_order_has_correct_sensor(self, handler, parsed_order_frame):
        """Test that the stored Order has the expected sensor pin."""
        # GIVEN a handler processing a LG_INIT Order frame with sensor=5
        handler.handle_master_command(parsed_order_frame)

        # WHEN we retrieve the order
        order = command_store.get_order(1)

        # THEN sensor is 5
        assert order.sensor == 5

    def test_stored_order_has_correct_controller(self, handler, parsed_order_frame):
        """Test that the stored Order has the expected controller pin."""
        # GIVEN a handler processing a LG_INIT Order frame with controller=-1
        handler.handle_master_command(parsed_order_frame)

        # WHEN we retrieve the order
        order = command_store.get_order(1)

        # THEN controller is -1
        assert order.controller == -1

    def test_stored_order_has_correct_is_toggle_ctrl_value(self, handler, parsed_order_frame):
        """Test that the stored Order has the expected is_toggle_ctrl_value."""
        # GIVEN a handler processing a LG_INIT Order frame with is_toggle_ctrl_value=False
        handler.handle_master_command(parsed_order_frame)

        # WHEN we retrieve the order
        order = command_store.get_order(1)

        # THEN is_toggle_ctrl_value is False
        assert order.is_toggle_ctrl_value is False

    def test_stored_order_has_correct_ctrl_value(self, handler, parsed_order_frame):
        """Test that the stored Order has the expected ctrl_value."""
        # GIVEN a handler processing a LG_INIT Order frame with ctrl_value=''
        handler.handle_master_command(parsed_order_frame)

        # WHEN we retrieve the order
        order = command_store.get_order(1)

        # THEN ctrl_value is ''
        assert order.ctrl_value == ""


# ---------------------------------------------------------------------------
# Tests – Handler error cases
# ---------------------------------------------------------------------------


class TestLgInitHandlerErrors:
    """Tests for handler error cases during LG_INIT frame processing."""

    def test_wrong_device_uid_raises_exception(self, handler):
        """Test that a LG_INIT frame with a non-matching device UID raises an exception."""
        # GIVEN a LG_INIT frame targeting a different device
        raw_frame = build_lg_init_frame_str("wrong_device_uid", ORDER_MODEL_NAME, ORDER_FIELDS)
        frame = FrameParser.parse_from_master(raw_frame)

        # WHEN / THEN the handler raises an exception
        with pytest.raises(Exception, match="does not match"):
            handler.handle_master_command(frame)

    def test_invalid_checksum_raises_value_error(self, handler):
        """Test that a LG_INIT frame with a tampered checksum raises ValueError."""
        # GIVEN a LG_INIT frame with a deliberately wrong checksum
        frame_without_cs = f"{STX} LG_INIT {DEVICE_UID} -1 order 1;get_temp;get;5;-1;False; {ETX}"
        bad_frame_str = f"{frame_without_cs} FF\n"
        frame = FrameParser.parse_from_master(bad_frame_str)

        # WHEN / THEN the handler raises a ValueError about checksum
        with pytest.raises(ValueError, match="Checksum verification failed"):
            handler.handle_master_command(frame)

    def test_unknown_device_uid_accepted(self, handler):
        """Test that a LG_INIT frame with UKW_DEV_UID is accepted."""
        # GIVEN a LG_INIT frame using the unknown device UID wildcard
        raw_frame = build_lg_init_frame_str("UKW_DEV_UID", ORDER_MODEL_NAME, ORDER_FIELDS)
        frame = FrameParser.parse_from_master(raw_frame)

        # WHEN the handler processes the frame
        response = handler.handle_master_command(frame)

        # THEN a valid response is returned
        assert response is not None
        assert f"{STX} ACK" in response

    def test_unsupported_model_raises_value_error(self, handler):
        """Test that a LG_INIT frame with an unsupported model raises ValueError."""
        # GIVEN a LG_INIT frame with a valid model name
        # We build the frame manually to bypass from_string validation
        frame_without_cs = f"{STX} LG_INIT {DEVICE_UID} -1 order 1;get_temp;get;5;-1;False; {ETX}"
        checksum = Frame.build_checksum(frame_without_cs.encode())
        raw_frame = f"{frame_without_cs} {checksum:02X}\n"
        frame = FrameParser.parse_from_master(raw_frame)

        # Manually override the model to an invalid value
        frame.model = "InvalidModel"

        # WHEN / THEN the handler raises a ValueError
        with pytest.raises(ValueError, match="not supported"):
            handler.handle_master_command(frame)

    def test_order_not_stored_when_checksum_fails(self, handler):
        """Test that a failed checksum prevents Order from being stored."""
        # GIVEN a LG_INIT Order frame with a bad checksum
        frame_without_cs = f"{STX} LG_INIT {DEVICE_UID} -1 order 1;get_temp;get;5;-1;False; {ETX}"
        bad_frame_str = f"{frame_without_cs} FF\n"
        frame = FrameParser.parse_from_master(bad_frame_str)

        # WHEN the handler rejects the frame
        with pytest.raises(ValueError):
            handler.handle_master_command(frame)

        # THEN the order is NOT in the command store
        with pytest.raises(KeyError):
            command_store.get_order(1)


# ---------------------------------------------------------------------------
# Tests – Full pipeline (end-to-end with event system and queues)
# ---------------------------------------------------------------------------


class TestLgInitFullPipeline:
    """End-to-end integration tests: raw bytes in -> event pipeline -> response in outbox."""

    @pytest.mark.asyncio
    async def test_order_raw_bytes_to_inbox(self, order_raw_bytes):
        """Test that on_order_received decodes raw bytes and queues them in inbox."""
        # GIVEN raw LG_INIT Order bytes as received from stdin

        # WHEN on_order_received is called
        await on_order_received(order_raw_bytes)

        # THEN the decoded string is available in the inbox queue
        assert not inbox.empty()
        queued_value = inbox.get_nowait()
        assert queued_value == order_raw_bytes.decode("utf-8")

    @pytest.mark.asyncio
    async def test_order_process_produces_response(self, parsed_order_frame):
        """Test that on_order_process puts a response in the outbox queue for Order."""
        # GIVEN a parsed LG_INIT Order Frame object (fixture)

        # WHEN on_order_process is called
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
    async def test_full_order_pipeline_from_raw_bytes(self, order_raw_bytes):
        """Test the complete Order flow: raw bytes -> decode -> parse -> handle -> response queued."""
        # GIVEN raw LG_INIT Order bytes

        # WHEN we simulate the full pipeline step by step
        # Step 1: Receive raw bytes -> decode and queue
        await on_order_received(order_raw_bytes)

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
    async def test_full_order_pipeline_response_content(self, order_raw_bytes):
        """Test that the full Order pipeline produces a correctly formatted ACK response."""
        # GIVEN raw LG_INIT Order bytes going through the complete pipeline

        # WHEN processed end-to-end
        await on_order_received(order_raw_bytes)
        order_str = inbox.get_nowait()
        frame = FrameParser.parse_from_master(order_str)
        await on_order_process(frame)
        response = outbox.get_nowait()

        # THEN the response contains all expected ACK response components
        assert f"{STX} ACK" in response
        assert DEVICE_UID in response
        assert CommandState.OK in response

    @pytest.mark.asyncio
    async def test_full_order_pipeline_response_checksum_valid(self, order_raw_bytes):
        """Test that the response generated by the full Order pipeline has a valid checksum."""
        # GIVEN raw LG_INIT Order bytes going through the complete pipeline

        # WHEN processed end-to-end
        await on_order_received(order_raw_bytes)
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
    async def test_full_order_pipeline_via_event_emitter(self, order_raw_bytes):
        """Test the complete Order flow driven entirely by event emissions."""
        # GIVEN raw LG_INIT Order bytes and a fully wired event emitter (autouse fixture)

        # WHEN we emit 'order:received' (the entry point of the pipeline)
        await event_emitter.emit("order:received", order_raw_bytes)

        # Step 2: manually drive inbox -> parse -> emit 'order:process'
        order_str = inbox.get_nowait()
        frame = FrameParser.parse_from_master(order_str)
        await event_emitter.emit("order:process", frame)

        # THEN the outbox contains a valid ACK response
        assert not outbox.empty()
        response = outbox.get_nowait()
        assert f"{STX} ACK" in response
        assert DEVICE_UID in response
