import asyncio
import sys

from src.core import event_emitter

from .dataqueue import data_received as inbox
from .dataqueue import data_to_response as outbox
from .frame import CommandError
from .frame import Frame
from .parser import FrameParser


async def task_received_order():
    """
    Continuously listens for incoming data on sys.stdin via an async StreamReader.

    This task reads one line at a time from stdin (USB serial input).
    Each received line (raw bytes) is forwarded to the event pipeline
    by emitting the "order:received" event, which triggers the
    on_order_received callback responsible for decoding and queuing the data.

    Note:
        In MicroPython, asyncio.StreamReader wraps sys.stdin directly.
        sleep(0) yields control to the event loop without delay,
        allowing other tasks to run between each read cycle.
    """
    sreader = asyncio.StreamReader(sys.stdin)
    while True:
        raw_data = await sreader.readline()
        if raw_data:
            await event_emitter.emit("order:received", raw_data)
        # Yield to event loop so other tasks can execute
        await asyncio.sleep(0)


async def task_process_order():
    """
    Continuously consumes orders from the inbox queue and processes them.

    This task waits for decoded order strings placed in the inbox by the
    on_order_received callback. For each order it:
    1. Parses the raw string into a Frame object via FrameParser.
    2. Emits the "order:process" event which triggers the handler
       (checksum verification, command dispatch, response generation).

    If parsing or processing raises an exception, the error is forwarded
    via the "error:occurred" event to generate an error response frame.

    Note:
        inbox.get() blocks naturally when the queue is empty,
        so no explicit join() is needed.
    """
    while True:
        order: str = await inbox.get()

        try:
            frame_order_obj: Frame = FrameParser.parse_from_master(order)
            await event_emitter.emit("order:process", frame_order_obj)
        except Exception as e:
            err_type = CommandError.UNKNOW_ERR
            # Strip trailing newline before forwarding to error handler
            if order.endswith("\n"):
                order = order.removesuffix("\n")
            await event_emitter.emit("error:occurred", str(e), err_type, order)

        # Yield to event loop between each processed order
        await asyncio.sleep(0.05)


async def task_response_to_master():
    """
    Continuously consumes response frames from the outbox queue
    and sends them back to the master service via sys.stdout.

    This task waits for serialized frame strings placed in the outbox
    by the on_response_ready callback, then writes them to stdout
    (USB serial output) for the backend service to receive.

    Note:
        outbox.get() blocks naturally when the queue is empty.
    """
    while True:
        frame_response: str = await outbox.get()
        sys.stdout.write(frame_response)
        # Yield to event loop between each sent response
        await asyncio.sleep(0.05)


async def runner():
    """
    Entry point for the USB communication workflow.

    Launches the three concurrent tasks that form the processing pipeline:
    1. task_received_order   — reads raw data from stdin (USB input)
    2. task_process_order    — parses and dispatches commands
    3. task_response_to_master — writes responses to stdout (USB output)

    These tasks run indefinitely and communicate through the inbox/outbox
    queues and the EventEmitter event system.
    """
    asyncio.create_task(task_received_order())
    asyncio.create_task(task_process_order())
    asyncio.create_task(task_response_to_master())
