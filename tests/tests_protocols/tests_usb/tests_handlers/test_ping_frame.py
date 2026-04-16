# This test, test a ping frame complete workflow, from receiving a ping frame to sending the response.
# It is a high level test, that covers the handler and the parser.
# It is not a unit test, but an integration test.
import pytest

from src.__version__ import __version__
from src.__version__ import micropython_version
from src.core import DEVICE_UID
from src.core import event_emitter
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


def build_ping_frame_str(device_uid: str) -> str:
    """Build a valid raw PING frame string with correct checksum, as sent by master."""
    frame_without_cs = f"{STX} PING {device_uid} 0 {ETX}"
    checksum = Frame.build_checksum(frame_without_cs.encode())
    return f"{frame_without_cs} {checksum:02X}\n"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def ping_raw_frame():
    """Fixture providing a valid raw PING frame string targeting the current device."""
    return build_ping_frame_str(DEVICE_UID)


@pytest.fixture
def ping_raw_bytes(ping_raw_frame):
    """Fixture providing the PING frame as raw bytes (simulating stdin read)."""
    return ping_raw_frame.encode("utf-8")


@pytest.fixture
def parsed_ping_frame(ping_raw_frame):
    """Fixture providing a Frame object parsed from the raw PING string."""
    return FrameParser.parse_from_master(ping_raw_frame)


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
    # Cleanup: remove all registered listeners to avoid side effects
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


# ---------------------------------------------------------------------------
# Tests – Parsing stage
# ---------------------------------------------------------------------------


class TestPingFrameParsing:
    """Tests for parsing a raw PING frame string into a Frame object."""

    def test_parsed_frame_type_is_ping(self, parsed_ping_frame):
        """Test that the parsed frame has PING type."""
        # GIVEN a raw PING frame string (fixture)

        # WHEN it is parsed into a Frame object (fixture)

        # THEN frame_type is PING
        assert parsed_ping_frame.frame_type == FrameType.PING

    def test_parsed_frame_is_from_master(self, parsed_ping_frame):
        """Test that the parsed frame is marked as coming from master."""
        # GIVEN a parsed PING frame (fixture)

        # WHEN we check from_master
        # THEN it is True
        assert parsed_ping_frame.from_master is True

    def test_parsed_command_id_is_zero(self, parsed_ping_frame):
        """Test that a PING frame has command_id 0."""
        # GIVEN a parsed PING frame (fixture)

        # WHEN we check command_id
        # THEN it is 0
        assert parsed_ping_frame.command_id == 0

    def test_parsed_device_uid_matches(self, parsed_ping_frame):
        """Test that the device UID in the parsed frame matches the current device."""
        # GIVEN a parsed PING frame targeting the current device (fixture)

        # WHEN we check device_uid
        # THEN it matches DEVICE_UID
        assert parsed_ping_frame.device_uid == DEVICE_UID

    def test_is_ping_order_returns_true(self, parsed_ping_frame):
        """Test that is_ping_order() returns True for a PING frame."""
        # GIVEN a parsed PING frame (fixture)

        # WHEN we call is_ping_order()
        # THEN it returns True
        assert parsed_ping_frame.is_ping_order() is True

    def test_checksum_verification_passes(self, parsed_ping_frame):
        """Test that the checksum of the parsed frame is valid."""
        # GIVEN a parsed PING frame built with a correct checksum (fixture)

        # WHEN we verify the checksum
        # THEN verification passes
        assert parsed_ping_frame.verify_checksum() is True


# ---------------------------------------------------------------------------
# Tests – Handler stage
# ---------------------------------------------------------------------------


class TestPingFrameHandler:
    """Tests for the handler processing a PING frame and building the response."""

    def test_handler_returns_response_string(self, handler, parsed_ping_frame):
        """Test that the handler returns a non-empty response string."""
        # GIVEN a FrameHandler and a parsed PING frame (fixtures)

        # WHEN the handler processes the frame
        response = handler.handle_master_command(parsed_ping_frame)

        # THEN a non-empty string is returned
        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    def test_response_contains_ack_frame_type(self, handler, parsed_ping_frame):
        """Test that the response frame type is ACK."""
        # GIVEN a handler processing a PING frame
        response = handler.handle_master_command(parsed_ping_frame)

        # WHEN we inspect the response
        # THEN it contains ACK
        assert f"{STX} ACK" in response

    def test_response_contains_device_uid(self, handler, parsed_ping_frame):
        """Test that the response includes the device UID."""
        # GIVEN a handler processing a PING frame
        response = handler.handle_master_command(parsed_ping_frame)

        # WHEN we inspect the response
        # THEN it contains the device UID
        assert DEVICE_UID in response

    def test_response_contains_gardeniq_version(self, handler, parsed_ping_frame):
        """Test that the response includes the GardenIQ firmware version."""
        # GIVEN a handler processing a PING frame
        response = handler.handle_master_command(parsed_ping_frame)

        # WHEN we inspect the response
        # THEN it contains GDFW=<version>
        assert f"GDFW={__version__}" in response

    def test_response_contains_micropython_version(self, handler, parsed_ping_frame):
        """Test that the response includes the MicroPython firmware version."""
        # GIVEN a handler processing a PING frame
        response = handler.handle_master_command(parsed_ping_frame)

        # WHEN we inspect the response
        # THEN it contains MPFW=<version>
        assert f"MPFW={micropython_version}" in response

    def test_response_contains_ok_state(self, handler, parsed_ping_frame):
        """Test that the response frame has OK command state."""
        # GIVEN a handler processing a PING frame
        response = handler.handle_master_command(parsed_ping_frame)

        # WHEN we inspect the response
        # THEN it contains OK state
        assert f" {CommandState.OK} " in response

    def test_response_ends_with_newline(self, handler, parsed_ping_frame):
        """Test that the response is newline-terminated for serial transmission."""
        # GIVEN a handler processing a PING frame
        response = handler.handle_master_command(parsed_ping_frame)

        # WHEN we check the ending
        # THEN it ends with newline
        assert response.endswith("\n")

    def test_response_has_valid_checksum(self, handler, parsed_ping_frame):
        """Test that the checksum in the response frame is valid."""
        # GIVEN a handler processing a PING frame
        response = handler.handle_master_command(parsed_ping_frame)

        # WHEN we extract response parts and verify the checksum
        response_stripped = response.removesuffix("\n")
        frame_part, cs_hex = response_stripped.rsplit(" ", 1)
        expected_cs = Frame.build_checksum(frame_part.encode())

        # THEN the checksum matches
        assert int(cs_hex, 16) == expected_cs


# ---------------------------------------------------------------------------
# Tests – Handler error cases
# ---------------------------------------------------------------------------


class TestPingFrameHandlerErrors:
    """Tests for handler error cases during PING frame processing."""

    def test_wrong_device_uid_raises_exception(self, handler):
        """Test that a PING frame with a non-matching device UID raises an exception."""
        # GIVEN a PING frame targeting a different device
        raw_frame = build_ping_frame_str("wrong_device_uid")
        frame = FrameParser.parse_from_master(raw_frame)

        # WHEN / THEN the handler raises an exception
        with pytest.raises(Exception, match="does not match"):
            handler.handle_master_command(frame)

    def test_invalid_checksum_raises_value_error(self, handler):
        """Test that a PING frame with a tampered checksum raises ValueError."""
        # GIVEN a PING frame with a deliberately wrong checksum
        frame_without_cs = f"{STX} PING {DEVICE_UID} 0 {ETX}"
        bad_frame_str = f"{frame_without_cs} FF\n"
        frame = FrameParser.parse_from_master(bad_frame_str)

        # WHEN / THEN the handler raises a ValueError about checksum
        with pytest.raises(ValueError, match="Checksum verification failed"):
            handler.handle_master_command(frame)

    def test_unknown_device_uid_accepted(self, handler):
        """Test that a PING frame with UKW_DEV_UID is accepted."""
        # GIVEN a PING frame using the unknown device UID wildcard
        raw_frame = build_ping_frame_str("UKW_DEV_UID")
        frame = FrameParser.parse_from_master(raw_frame)

        # WHEN the handler processes the frame
        response = handler.handle_master_command(frame)

        # THEN a valid response is returned
        assert response is not None
        assert f"{STX} ACK" in response


# ---------------------------------------------------------------------------
# Tests – Full pipeline (end-to-end with event system and queues)
# ---------------------------------------------------------------------------


class TestPingFrameFullPipeline:
    """End-to-end integration tests: raw bytes in → event pipeline → response in outbox."""

    @pytest.mark.asyncio
    async def test_raw_bytes_to_inbox(self, ping_raw_bytes):
        """Test that on_order_received decodes raw bytes and queues them in inbox."""
        # GIVEN raw PING bytes as received from stdin

        # WHEN on_order_received is called
        await on_order_received(ping_raw_bytes)

        # THEN the decoded string is available in the inbox queue
        assert not inbox.empty()
        queued_value = inbox.get_nowait()
        assert queued_value == ping_raw_bytes.decode("utf-8")

    @pytest.mark.asyncio
    async def test_order_process_produces_response(self, parsed_ping_frame):
        """Test that on_order_process puts a response in the outbox queue."""
        # GIVEN a parsed PING Frame object (fixture)

        # WHEN on_order_process is called
        await on_order_process(parsed_ping_frame)

        # THEN a response is ready in the outbox queue
        assert not outbox.empty()

    @pytest.mark.asyncio
    async def test_response_ready_puts_in_outbox(self):
        """Test that on_response_ready correctly queues the response string."""
        # GIVEN a response frame string
        fake_response = f"{STX} ACK test 0 OK {ETX} AB\n"

        # WHEN on_response_ready is called
        await on_response_ready(fake_response)

        # THEN the response is in the outbox
        assert not outbox.empty()
        assert outbox.get_nowait() == fake_response

    @pytest.mark.asyncio
    async def test_full_pipeline_from_raw_bytes(self, ping_raw_bytes, ping_raw_frame):
        """Test the complete flow: raw bytes → decode → parse → handle → response queued."""
        # GIVEN raw PING bytes

        # WHEN we simulate the full pipeline step by step
        # Step 1: Receive raw bytes → decode and queue
        await on_order_received(ping_raw_bytes)

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
    async def test_full_pipeline_response_content(self, ping_raw_bytes):
        """Test that the full pipeline produces a correctly formatted PING response."""
        # GIVEN raw PING bytes going through the complete pipeline

        # WHEN processed end-to-end
        await on_order_received(ping_raw_bytes)
        order_str = inbox.get_nowait()
        frame = FrameParser.parse_from_master(order_str)
        await on_order_process(frame)
        response = outbox.get_nowait()

        # THEN the response contains all expected PING response components
        assert f"{STX} ACK" in response
        assert DEVICE_UID in response
        assert "0" in response
        assert CommandState.OK in response
        assert f"GDFW={__version__}" in response
        assert f"MPFW={micropython_version}" in response

    @pytest.mark.asyncio
    async def test_full_pipeline_response_checksum_valid(self, ping_raw_bytes):
        """Test that the response generated by the full pipeline has a valid checksum."""
        # GIVEN raw PING bytes going through the complete pipeline

        # WHEN processed end-to-end
        await on_order_received(ping_raw_bytes)
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
    async def test_full_pipeline_via_event_emitter(self, ping_raw_bytes):
        """Test the complete flow driven entirely by event emissions."""
        # GIVEN raw PING bytes and a fully wired event emitter (autouse fixture)

        # WHEN we emit 'order:received' (the entry point of the pipeline)
        await event_emitter.emit("order:received", ping_raw_bytes)

        # Step 2: manually drive inbox → parse → emit 'order:process'
        order_str = inbox.get_nowait()
        frame = FrameParser.parse_from_master(order_str)
        await event_emitter.emit("order:process", frame)

        # THEN the outbox contains the response
        assert not outbox.empty()
        response = outbox.get_nowait()
        assert f"GDFW={__version__}" in response
        assert f"MPFW={micropython_version}" in response
