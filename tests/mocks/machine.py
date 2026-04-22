def unique_id() -> bytes:
    """Mock of micropython machine.unique_id - returns a fixed UID for testing."""
    return b"\xe6cX\x98c\\7/"


class Pin:
    """Mock of machine.Pin for testing purposes."""

    OUT = 0
    IN = 1
    PULL_UP = 2
    PULL_DOWN = 3

    def __init__(self, id: int, mode: int, pull=None):
        self.id = id
        self.mode = mode
        self.pull = pull


class PWM:
    """Mock of machine.PWM for testing purposes."""

    def __init__(self, dest: int, freq: int = 1000, duty_u16: int = 512, duty_ns: int = 0):
        self.dest = dest
        self.freq = freq
        self.duty_u16 = duty_u16
        self.duty_ns = duty_ns


class ADC:
    """Mock of machine.ADC for testing purposes."""

    def __init__(self, pin: int):
        self.pin = pin
