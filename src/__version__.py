import sys

MAJOR = 1
MINOR = 0
PATCH = 0

__version__ = f"{MAJOR}.{MINOR}.{PATCH}"


def get_micropython_version() -> str:
    # sys.version -> 3.4.0; MicroPython v1.25.0 on 2025-04-15
    # string_version -> v1.25.0
    string_version = sys.version.split(';')[1].strip().split(" ")[1]
    # Slice version without "v"
    return string_version[1:]


micropython_version = get_micropython_version()
