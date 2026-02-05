import sys

# Mock micropython modules BEFORE pytest collection
# This must be done at module level, not in a fixture
from tests.mocks import machine
from tests.mocks import sys as sys_mock
from tests.mocks import ubinascii

sys.modules["machine"] = machine
sys.modules["ubinascii"] = ubinascii
sys.modules["sys"] = sys_mock
