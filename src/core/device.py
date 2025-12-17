from machine import unique_id
from ubinascii import hexlify


def get_device_uid() -> str:
    # unique_id return bytes like b'\xe6cX\x98c\\7/'
    uid = unique_id()
    # hexlify(uid).decode() return string like "e6635898635c372f"
    return hexlify(uid).decode()
