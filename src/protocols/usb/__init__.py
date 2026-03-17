# This file is a entrypoint to USB protocol !
import asyncio

from src.core import event_emitter

from .callback import cb_register
from .workflow import runner


def setup():
    for cb in cb_register:
        event_emitter.on(cb.name, cb.func)


def process():
    asyncio.run(runner())
