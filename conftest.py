import asyncio
import sys

# ---------------------------------------------------------------------------
# MicroPython asyncio.StreamReader compatibility
# ---------------------------------------------------------------------------
# In MicroPython, asyncio.StreamReader(stream) takes a stream as its first
# positional argument. CPython's StreamReader does not support this.
# We wrap it so that code written for MicroPython can be tested under CPython.
_OrigStreamReader = asyncio.StreamReader


class _StreamReaderCompat(_OrigStreamReader):
    """StreamReader wrapper that accepts a MicroPython-style stream argument."""

    def __init__(self, stream=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._stream = stream


asyncio.StreamReader = _StreamReaderCompat

# ---------------------------------------------------------------------------
# Mock micropython modules BEFORE pytest collection
# ---------------------------------------------------------------------------
# This must be done at module level, not in a fixture
from tests.mocks import machine  # noqa: E402
from tests.mocks import ubinascii  # noqa: E402

from tests.mocks import sys as sys_mock  # isort: skip # noqa: E402

sys.modules["machine"] = machine
sys.modules["ubinascii"] = ubinascii
sys.modules["sys"] = sys_mock
