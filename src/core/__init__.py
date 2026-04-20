from .dataclass import FrozenDataclass
from .device import get_device_uid
from .event import EventEmitter

DEVICE_UID = get_device_uid()

# Create a singleton of EventEmitter to be used across the application for event handling.
event_emitter = EventEmitter()
