from .commands import CommandStore
from .pins import InitializedPinStore

# Create a singleton of CommandStore to be used across the application
commands_store = CommandStore()

# Create a singleton of InitializedPinStore to be used across the application
init_pins_store = InitializedPinStore()
