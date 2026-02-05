import binascii


def hexlify(data: bytes) -> bytes:
    """Mock of micropython ubinascii.hexlify - wraps standard binascii."""
    return binascii.hexlify(data)


def unhexlify(data: str | bytes) -> bytes:
    """Mock of micropython ubinascii.unhexlify - wraps standard binascii."""
    return binascii.unhexlify(data)
