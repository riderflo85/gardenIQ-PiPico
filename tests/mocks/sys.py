# Mock of sys module for MicroPython testing environment.

version = "3.4.0; MicroPython v1.25.0 on 2025-04-15"


class _MockStream:
    """Minimal mock stream mimicking MicroPython stdin/stdout interface."""

    def read(self, n=-1):
        return b""

    def readline(self):
        return b""

    def write(self, data):
        pass


stdin = _MockStream()
stdout = _MockStream()
