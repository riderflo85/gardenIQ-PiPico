# Warning, typing lib does not exist in MicroPython !
# Remove this with a compile framework script !
from typing import Callable


class UnknownEventError(ValueError):
    """Raised when an unknown event is emitted."""

    pass


class EventEmitter:
    """
    EventEmitter class for managing event-driven architecture.
    This class implements a simple event listener pattern that allows registering,
    removing, and emitting events with associated callback functions.

    Attributes:
        _listeners (dict): Internal dictionary mapping event names to their registered
            callback functions. Format: {"event_name": callback_function}

    Example:
        >>> emitter = EventEmitter()
        >>> async def on_event_fired(data):
        ...     print(f"Event fired with data: {data}")
        >>> emitter.on("my_event", on_event_fired)
        >>> await emitter.emit("my_event", data={"status": "success"})
    """

    def __init__(self) -> None:
        self._listeners = {}  # {"event_name": callback function,}

    def on(self, event_name: str, callback: Callable) -> None:
        """
        Register a callback function to listen for a specific event.

        Args:
            event_name (str): The name of the event to listen for.
            callback (Callable): The callback function to execute when the event is triggered.

        Returns:
            None

        Note:
            Registering a new callback for an existing event_name will overwrite the previous callback.
        """
        self._listeners[event_name] = callback

    def off(self, event_name: str) -> None:
        """
        Remove all listeners for the specified event.

        Args:
            event_name (str): The name of the event to remove listeners from.

        Returns:
            None

        Raises:
            UnknownEventError: If no listener is registered for the event_name.
        """
        if self._listeners.get(event_name, None):
            self._listeners.pop(event_name)
        else:
            raise UnknownEventError(f"No listener registered for event: {event_name}")

    async def emit(self, event_name: str, *args, **kwargs) -> None:
        """
        Emit an event by calling the associated listener callback.

        Args:
            event_name (str): The name of the event to emit.
            *args: Positional arguments to pass to the listener callback.
            **kwargs: Keyword arguments to pass to the listener callback.

        Returns:
            None

        Raises:
            UnknownEventError: If no listener is registered for the event_name.
        """
        if callback := self._listeners.get(event_name, None):
            await callback(*args, **kwargs)
        else:
            raise UnknownEventError(f"No listener registered for event: {event_name}")
