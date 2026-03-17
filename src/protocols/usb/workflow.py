import asyncio
import sys

from src.core import event_emitter

from .dataqueue import data_received as inbox
from .dataqueue import data_to_response as outbox
from .frame import CommandError
from .frame import Frame
from .parser import FrameParser


async def task_received_order():
    sreader = asyncio.StreamReader(sys.stdin)
    while True:
        raw_data = await sreader.readline()
        if raw_data:
            await event_emitter.emit("order:received", raw_data)
        await asyncio.sleep(0)


async def task_process_order():
    while True:
        await inbox.join()
        order: str = await inbox.get()

        try:
            frame_order_obj: Frame = FrameParser.parse_from_master(order)
            await event_emitter.emit("order:process", frame_order_obj)
        except Exception as e:
            err_type = CommandError.UNKNOW_ERR
            if order.endswith("\n"):
                order = order.removesuffix("\n")
            await event_emitter.emit("error:occured", str(e), err_type, order)

        inbox.task_done()
        await asyncio.sleep(0.5)


async def task_response_to_master():
    while True:
        await outbox.join()
        frame_response: str = await outbox.get()
        sys.stdout.write(frame_response)
        await asyncio.sleep(0.5)


async def runner():
    asyncio.create_task(task_received_order())
    asyncio.create_task(task_process_order())
    asyncio.create_task(task_response_to_master())
