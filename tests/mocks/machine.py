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
        self._value = 0

    def value(self, val=None):
        """Get or set the pin value. If val is provided, set the value; otherwise return it."""
        if val is None:
            return self._value
        self._value = val


class PWM:
    """Mock of machine.PWM for testing purposes."""

    def __init__(self, dest: int, freq: int = 1000, duty_u16_value: int = 512, duty_ns: int = 0):
        self.dest = dest
        self.freq = freq
        self._duty_u16 = duty_u16_value
        self.duty_ns = duty_ns

    def duty_u16(self, val=None) -> int | None:
        """Get or set the duty cycle as a 16-bit value. Returns current value if no argument."""
        if val is None:
            return self._duty_u16
        self._duty_u16 = val


class ADC:
    """Mock of machine.ADC for testing purposes."""

    def __init__(self, pin: int, read_u16_value: int = 0):
        self.pin = pin
        self._read_u16_value = read_u16_value

    def read_u16(self) -> int:
        """Return the configured 16-bit ADC reading."""
        return self._read_u16_value
