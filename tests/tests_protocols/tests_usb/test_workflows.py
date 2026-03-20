import asyncio

import pytest

from src.protocols.errors import CommandError
from src.protocols.usb.workflow import runner
from src.protocols.usb.workflow import task_process_order
from src.protocols.usb.workflow import task_received_order
from src.protocols.usb.workflow import task_response_to_master

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def readline_stub(lines):
    """Build an async readline that yields *lines* then raises CancelledError."""
    it = iter(lines)

    async def _readline():
        try:
            return next(it)
        except StopIteration:
            raise asyncio.CancelledError()

    return _readline


def queue_get_stub(items):
    """Build an async get that yields *items* then raises CancelledError."""
    it = iter(items)

    async def _get():
        try:
            return next(it)
        except StopIteration:
            raise asyncio.CancelledError()

    return _get


# ---------------------------------------------------------------------------
# Tests – task_received_order
# ---------------------------------------------------------------------------


class TestTaskReceivedOrder:
    """Tests verifying the task_received_order async task."""

    async def test_emits_order_received_with_raw_bytes(self, mocker):
        """Verify that incoming raw data triggers the order:received event."""
        # GIVEN: A StreamReader returning one line then cancelling the loop
        mock_reader = mocker.MagicMock()
        mock_reader.readline = readline_stub([b"< CMD uid 1 get_temp > FF\n"])
        mocker.patch("asyncio.StreamReader", return_value=mock_reader)
        mock_emitter = mocker.patch("src.protocols.usb.workflow.event_emitter")
        mock_emitter.emit = mocker.AsyncMock()

        # WHEN: Running the task until it is cancelled
        with pytest.raises(asyncio.CancelledError):
            await task_received_order()

        # THEN: order:received was emitted once with the raw bytes
        mock_emitter.emit.assert_called_once_with("order:received", b"< CMD uid 1 get_temp > FF\n")

    async def test_does_not_emit_on_empty_read(self, mocker):
        """Verify that an empty readline result does not trigger any event."""
        # GIVEN: A StreamReader returning empty bytes then cancelling
        mock_reader = mocker.MagicMock()
        mock_reader.readline = readline_stub([b""])
        mocker.patch("asyncio.StreamReader", return_value=mock_reader)
        mock_emitter = mocker.patch("src.protocols.usb.workflow.event_emitter")
        mock_emitter.emit = mocker.AsyncMock()

        # WHEN: Running the task
        with pytest.raises(asyncio.CancelledError):
            await task_received_order()

        # THEN: No event was emitted
        mock_emitter.emit.assert_not_called()

    async def test_emits_for_each_incoming_line(self, mocker):
        """Verify that each line triggers a separate order:received event."""
        # GIVEN: A StreamReader returning two lines then cancelling
        mock_reader = mocker.MagicMock()
        mock_reader.readline = readline_stub([b"line_1\n", b"line_2\n"])
        mocker.patch("asyncio.StreamReader", return_value=mock_reader)
        mock_emitter = mocker.patch("src.protocols.usb.workflow.event_emitter")
        mock_emitter.emit = mocker.AsyncMock()

        # WHEN: Running the task
        with pytest.raises(asyncio.CancelledError):
            await task_received_order()

        # THEN: Two events were emitted in order
        assert mock_emitter.emit.call_count == 2
        calls = mock_emitter.emit.call_args_list
        assert calls[0].args == ("order:received", b"line_1\n")
        assert calls[1].args == ("order:received", b"line_2\n")

    async def test_creates_stream_reader_with_stdin(self, mocker):
        """Verify that asyncio.StreamReader is instantiated with sys.stdin."""
        # GIVEN: Mocked StreamReader constructor and stdin
        mock_reader = mocker.MagicMock()
        mock_reader.readline = readline_stub([])
        mock_sr_cls = mocker.patch("asyncio.StreamReader", return_value=mock_reader)
        mock_stdin = mocker.patch("src.protocols.usb.workflow.sys.stdin")
        mocker.patch("src.protocols.usb.workflow.event_emitter")

        # WHEN: Running the task
        with pytest.raises(asyncio.CancelledError):
            await task_received_order()

        # THEN: StreamReader was created with sys.stdin
        mock_sr_cls.assert_called_once_with(mock_stdin)


# ---------------------------------------------------------------------------
# Tests – task_process_order
# ---------------------------------------------------------------------------


class TestTaskProcessOrder:
    """Tests verifying the task_process_order async task."""

    async def test_parses_order_and_emits_order_process(self, mocker):
        """Verify that a valid order is parsed and order:process is emitted."""
        # GIVEN: Inbox returning one order then cancelling
        mock_inbox = mocker.patch("src.protocols.usb.workflow.inbox")
        mock_inbox.get = queue_get_stub(["< CMD uid 1 get_temp > FF\n"])
        mock_frame = mocker.MagicMock()
        mock_parser = mocker.patch("src.protocols.usb.workflow.FrameParser")
        mock_parser.parse_from_master.return_value = mock_frame
        mock_emitter = mocker.patch("src.protocols.usb.workflow.event_emitter")
        mock_emitter.emit = mocker.AsyncMock()

        # WHEN: Running the task
        with pytest.raises(asyncio.CancelledError):
            await task_process_order()

        # THEN: The order was parsed and order:process emitted with the frame
        mock_parser.parse_from_master.assert_called_once_with("< CMD uid 1 get_temp > FF\n")
        mock_emitter.emit.assert_called_once_with("order:process", mock_frame)

    async def test_emits_error_occurred_when_parsing_fails(self, mocker):
        """Verify that error:occurred is emitted when FrameParser raises an exception."""
        # GIVEN: Inbox returning one order and FrameParser raising
        mock_inbox = mocker.patch("src.protocols.usb.workflow.inbox")
        mock_inbox.get = queue_get_stub(["< INVALID > FF\n"])
        mock_parser = mocker.patch("src.protocols.usb.workflow.FrameParser")
        mock_parser.parse_from_master.side_effect = ValueError("Invalid frame")
        mock_emitter = mocker.patch("src.protocols.usb.workflow.event_emitter")
        mock_emitter.emit = mocker.AsyncMock()

        # WHEN: Running the task
        with pytest.raises(asyncio.CancelledError):
            await task_process_order()

        # THEN: error:occurred was emitted with the error details (newline stripped)
        mock_emitter.emit.assert_called_once_with(
            "error:occurred",
            "Invalid frame",
            CommandError.UNKNOW_ERR,
            "< INVALID > FF",
        )

    async def test_error_path_strips_trailing_newline_from_order(self, mocker):
        """Verify that a trailing newline is stripped from the order before error emission."""
        # GIVEN: An order with trailing newline that triggers a parse error
        mock_inbox = mocker.patch("src.protocols.usb.workflow.inbox")
        mock_inbox.get = queue_get_stub(["bad order\n"])
        mock_parser = mocker.patch("src.protocols.usb.workflow.FrameParser")
        mock_parser.parse_from_master.side_effect = Exception("Parse error")
        mock_emitter = mocker.patch("src.protocols.usb.workflow.event_emitter")
        mock_emitter.emit = mocker.AsyncMock()

        # WHEN: Running the task
        with pytest.raises(asyncio.CancelledError):
            await task_process_order()

        # THEN: The order passed to the error event has no trailing newline
        order_arg = mock_emitter.emit.call_args.args[3]
        assert not order_arg.endswith("\n")
        assert order_arg == "bad order"

    async def test_error_path_preserves_order_without_trailing_newline(self, mocker):
        """Verify that an order without a trailing newline is forwarded unchanged."""
        # GIVEN: An order without trailing newline that triggers a parse error
        mock_inbox = mocker.patch("src.protocols.usb.workflow.inbox")
        mock_inbox.get = queue_get_stub(["no newline"])
        mock_parser = mocker.patch("src.protocols.usb.workflow.FrameParser")
        mock_parser.parse_from_master.side_effect = Exception("Error")
        mock_emitter = mocker.patch("src.protocols.usb.workflow.event_emitter")
        mock_emitter.emit = mocker.AsyncMock()

        # WHEN: Running the task
        with pytest.raises(asyncio.CancelledError):
            await task_process_order()

        # THEN: The order is forwarded as-is
        order_arg = mock_emitter.emit.call_args.args[3]
        assert order_arg == "no newline"

    async def test_error_type_is_always_unknow_err(self, mocker):
        """Verify that error:occurred always uses UNKNOW_ERR as error type."""
        # GIVEN: An order that fails parsing
        mock_inbox = mocker.patch("src.protocols.usb.workflow.inbox")
        mock_inbox.get = queue_get_stub(["bad"])
        mock_parser = mocker.patch("src.protocols.usb.workflow.FrameParser")
        mock_parser.parse_from_master.side_effect = Exception("Boom")
        mock_emitter = mocker.patch("src.protocols.usb.workflow.event_emitter")
        mock_emitter.emit = mocker.AsyncMock()

        # WHEN: Running the task
        with pytest.raises(asyncio.CancelledError):
            await task_process_order()

        # THEN: The error type is UNKNOW_ERR
        err_type_arg = mock_emitter.emit.call_args.args[2]
        assert err_type_arg == CommandError.UNKNOW_ERR

    async def test_processes_multiple_orders_sequentially(self, mocker):
        """Verify that multiple orders are consumed and processed in FIFO order."""
        # GIVEN: Inbox returning two orders then cancelling
        mock_inbox = mocker.patch("src.protocols.usb.workflow.inbox")
        mock_inbox.get = queue_get_stub(["order_1\n", "order_2\n"])
        mock_frame_1 = mocker.MagicMock(name="frame_1")
        mock_frame_2 = mocker.MagicMock(name="frame_2")
        mock_parser = mocker.patch("src.protocols.usb.workflow.FrameParser")
        mock_parser.parse_from_master.side_effect = [mock_frame_1, mock_frame_2]
        mock_emitter = mocker.patch("src.protocols.usb.workflow.event_emitter")
        mock_emitter.emit = mocker.AsyncMock()

        # WHEN: Running the task
        with pytest.raises(asyncio.CancelledError):
            await task_process_order()

        # THEN: Two events were emitted with the respective parsed frames
        assert mock_emitter.emit.call_count == 2
        calls = mock_emitter.emit.call_args_list
        assert calls[0].args == ("order:process", mock_frame_1)
        assert calls[1].args == ("order:process", mock_frame_2)


# ---------------------------------------------------------------------------
# Tests – task_response_to_master
# ---------------------------------------------------------------------------


class TestTaskResponseToMaster:
    """Tests verifying the task_response_to_master async task."""

    async def test_writes_response_to_stdout(self, mocker):
        """Verify that a response frame is written to sys.stdout."""
        # GIVEN: Outbox returning one response then cancelling
        mock_outbox = mocker.patch("src.protocols.usb.workflow.outbox")
        mock_outbox.get = queue_get_stub(["< ACK uid 1 OK > FF\n"])
        mock_stdout = mocker.patch("src.protocols.usb.workflow.sys.stdout")

        # WHEN: Running the task
        with pytest.raises(asyncio.CancelledError):
            await task_response_to_master()

        # THEN: sys.stdout.write was called with the response string
        mock_stdout.write.assert_called_once_with("< ACK uid 1 OK > FF\n")

    async def test_writes_multiple_responses_sequentially(self, mocker):
        """Verify that multiple responses are written to stdout in order."""
        # GIVEN: Outbox returning two responses then cancelling
        mock_outbox = mocker.patch("src.protocols.usb.workflow.outbox")
        mock_outbox.get = queue_get_stub(["resp_1\n", "resp_2\n"])
        mock_stdout = mocker.patch("src.protocols.usb.workflow.sys.stdout")

        # WHEN: Running the task
        with pytest.raises(asyncio.CancelledError):
            await task_response_to_master()

        # THEN: stdout.write was called twice in order
        assert mock_stdout.write.call_count == 2
        calls = mock_stdout.write.call_args_list
        assert calls[0].args == ("resp_1\n",)
        assert calls[1].args == ("resp_2\n",)

    async def test_forwards_response_data_unchanged(self, mocker):
        """Verify that the response string is forwarded to stdout without modification."""
        # GIVEN: A response with error details
        raw = "< ACK dev_uid 42 ERR UNKNOW_ERR::err_msg > 3F\n"
        mock_outbox = mocker.patch("src.protocols.usb.workflow.outbox")
        mock_outbox.get = queue_get_stub([raw])
        mock_stdout = mocker.patch("src.protocols.usb.workflow.sys.stdout")

        # WHEN: Running the task
        with pytest.raises(asyncio.CancelledError):
            await task_response_to_master()

        # THEN: The exact string was written to stdout
        mock_stdout.write.assert_called_once_with(raw)


# ---------------------------------------------------------------------------
# Tests – runner
# ---------------------------------------------------------------------------


class TestRunner:
    """Tests verifying the runner entry point."""

    async def test_creates_exactly_three_tasks(self, mocker):
        """Verify that runner creates exactly three asyncio tasks."""
        # GIVEN: Mocked create_task and task functions
        mock_create_task = mocker.patch("src.protocols.usb.workflow.asyncio.create_task")
        mocker.patch("src.protocols.usb.workflow.task_received_order")
        mocker.patch("src.protocols.usb.workflow.task_process_order")
        mocker.patch("src.protocols.usb.workflow.task_response_to_master")

        # WHEN: Running the runner
        await runner()

        # THEN: Exactly three tasks were created
        assert mock_create_task.call_count == 3

    async def test_creates_task_for_each_workflow_function(self, mocker):
        """Verify that runner creates tasks for all three workflow functions."""
        # GIVEN: Mocked task functions as MagicMock (not AsyncMock) so that
        # calling them returns return_value directly instead of a coroutine.
        mock_create_task = mocker.patch("src.protocols.usb.workflow.asyncio.create_task")
        mock_recv = mocker.MagicMock()
        mock_proc = mocker.MagicMock()
        mock_resp = mocker.MagicMock()
        mocker.patch("src.protocols.usb.workflow.task_received_order", mock_recv)
        mocker.patch("src.protocols.usb.workflow.task_process_order", mock_proc)
        mocker.patch("src.protocols.usb.workflow.task_response_to_master", mock_resp)

        # WHEN: Running the runner
        await runner()

        # THEN: Each task function was called once
        mock_recv.assert_called_once()
        mock_proc.assert_called_once()
        mock_resp.assert_called_once()

        # THEN: create_task received the return value of each function call
        created_coros = [call.args[0] for call in mock_create_task.call_args_list]
        assert mock_recv.return_value in created_coros
        assert mock_proc.return_value in created_coros
        assert mock_resp.return_value in created_coros


# ---------------------------------------------------------------------------
# Tests – full command pipeline (integration)
# ---------------------------------------------------------------------------


class TestCommandPipeline:
    """Integration tests verifying the end-to-end command processing flow."""

    async def test_valid_order_flows_from_inbox_to_outbox(self, mocker):
        """Verify that a valid order in inbox produces a response in outbox."""
        # GIVEN: Fresh queues replacing inbox and outbox
        from src.core.queue import Queue

        test_inbox = Queue(maxsize=10)
        test_outbox = Queue(maxsize=10)
        mocker.patch("src.protocols.usb.workflow.inbox", test_inbox)
        mocker.patch("src.protocols.usb.workflow.outbox", test_outbox)

        # FrameParser returning a mock frame
        mock_frame = mocker.MagicMock()
        mock_parser = mocker.patch("src.protocols.usb.workflow.FrameParser")
        mock_parser.parse_from_master.return_value = mock_frame

        # event_emitter that simulates the callback chain:
        #   order:process → put response in outbox
        response_str = "< ACK uid 1 OK > FF\n"
        mock_emitter = mocker.patch("src.protocols.usb.workflow.event_emitter")

        async def fake_emit(event_name, *args, **kwargs):
            if event_name == "order:process":
                await test_outbox.put(response_str)

        mock_emitter.emit = fake_emit

        # Put a valid order in the inbox
        test_inbox.put_nowait("< CMD uid 1 get_temp > FF\n")

        # WHEN: Running task_process_order briefly
        task = asyncio.create_task(task_process_order())
        await asyncio.sleep(0.15)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        # THEN: The response was placed in the outbox
        assert test_outbox.qsize() == 1
        assert test_outbox.get_nowait() == response_str

    async def test_parsing_error_triggers_error_event_not_outbox(self, mocker):
        """Verify that a parse error results in error:occurred with no response in outbox."""
        # GIVEN: Fresh queues
        from src.core.queue import Queue

        test_inbox = Queue(maxsize=10)
        test_outbox = Queue(maxsize=10)
        mocker.patch("src.protocols.usb.workflow.inbox", test_inbox)
        mocker.patch("src.protocols.usb.workflow.outbox", test_outbox)

        # FrameParser raises on invalid data
        mock_parser = mocker.patch("src.protocols.usb.workflow.FrameParser")
        mock_parser.parse_from_master.side_effect = ValueError("Invalid frame")

        # Track events emitted
        emitted_events = []
        mock_emitter = mocker.patch("src.protocols.usb.workflow.event_emitter")

        async def fake_emit(event_name, *args, **kwargs):
            emitted_events.append(event_name)

        mock_emitter.emit = fake_emit

        # Put an invalid order in the inbox
        test_inbox.put_nowait("garbage\n")

        # WHEN: Running task_process_order briefly
        task = asyncio.create_task(task_process_order())
        await asyncio.sleep(0.15)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        # THEN: error:occurred was emitted and outbox remains empty
        assert "error:occurred" in emitted_events
        assert "order:process" not in emitted_events
        assert test_outbox.empty() is True

    async def test_response_in_outbox_is_sent_to_stdout(self, mocker):
        """Verify that a response queued in outbox is written to stdout."""
        # GIVEN: Fresh outbox with a ready response
        from src.core.queue import Queue

        test_outbox = Queue(maxsize=10)
        mocker.patch("src.protocols.usb.workflow.outbox", test_outbox)
        mock_stdout = mocker.patch("src.protocols.usb.workflow.sys.stdout")

        response_str = "< ACK uid 1 OK data > AB\n"
        test_outbox.put_nowait(response_str)

        # WHEN: Running task_response_to_master briefly
        task = asyncio.create_task(task_response_to_master())
        await asyncio.sleep(0.15)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        # THEN: The response was written to stdout exactly once
        mock_stdout.write.assert_called_once_with(response_str)

    async def test_multiple_orders_produce_matching_responses_in_order(self, mocker):
        """Verify that several orders produce responses in outbox in the same order."""
        # GIVEN: Fresh queues with two orders and a matching emitter simulation
        from src.core.queue import Queue

        test_inbox = Queue(maxsize=10)
        test_outbox = Queue(maxsize=10)
        mocker.patch("src.protocols.usb.workflow.inbox", test_inbox)
        mocker.patch("src.protocols.usb.workflow.outbox", test_outbox)

        frames = [mocker.MagicMock(name="frame_1"), mocker.MagicMock(name="frame_2")]
        mock_parser = mocker.patch("src.protocols.usb.workflow.FrameParser")
        mock_parser.parse_from_master.side_effect = frames

        responses = ["response_1\n", "response_2\n"]
        resp_iter = iter(responses)
        mock_emitter = mocker.patch("src.protocols.usb.workflow.event_emitter")

        async def fake_emit(event_name, *args, **kwargs):
            if event_name == "order:process":
                await test_outbox.put(next(resp_iter))

        mock_emitter.emit = fake_emit

        test_inbox.put_nowait("order_1\n")
        test_inbox.put_nowait("order_2\n")

        # WHEN: Running task_process_order long enough for both orders
        task = asyncio.create_task(task_process_order())
        await asyncio.sleep(0.25)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        # THEN: Both responses are in the outbox in order
        assert test_outbox.qsize() == 2
        assert test_outbox.get_nowait() == "response_1\n"
        assert test_outbox.get_nowait() == "response_2\n"
