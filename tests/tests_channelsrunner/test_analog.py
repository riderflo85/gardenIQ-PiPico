import pytest

from src.channelsrunner.analog import run_get
from tests.mocks.machine import ADC


@pytest.fixture
def adc():
    """A mock ADC instance returning 0 by default."""
    return ADC(pin=26)


class TestRunGet:
    """Tests for the analog run_get function."""

    def test_returns_zero_when_adc_reads_zero(self, adc):
        # GIVEN an ADC configured to return 0
        adc._read_u16_value = 0

        # WHEN run_get is called
        result = run_get(adc)

        # THEN it returns 0
        assert result == 0

    def test_returns_max_value_when_adc_reads_max(self, adc):
        # GIVEN an ADC configured to return the maximum 16-bit value (65535)
        adc._read_u16_value = 65535

        # WHEN run_get is called
        result = run_get(adc)

        # THEN it returns 65535
        assert result == 65535

    def test_returns_mid_value_when_adc_reads_mid(self, adc):
        # GIVEN an ADC configured to return a mid-range value
        adc._read_u16_value = 32768

        # WHEN run_get is called
        result = run_get(adc)

        # THEN it returns 32768
        assert result == 32768

    def test_return_type_is_int(self, adc):
        # GIVEN an ADC configured to return a value
        adc._read_u16_value = 1024

        # WHEN run_get is called
        result = run_get(adc)

        # THEN the result is an integer
        assert isinstance(result, int)
