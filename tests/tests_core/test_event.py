import pytest

from src.core.event import EventEmitter
from src.core.event import UnknownEventError

# ---------------------------------------------------------------------------
# Tests – initialisation
# ---------------------------------------------------------------------------


class TestEventEmitterInit:
    """Tests verifying the initial state of a newly created EventEmitter."""

    def test_listeners_dict_is_created_on_init(self):
        """Verify that _listeners is initialised as an empty dict."""
        # GIVEN: Nothing
        # WHEN: Creating a new EventEmitter instance
        emitter = EventEmitter()

        # THEN: _listeners is an empty dictionary
        assert isinstance(emitter._listeners, dict)

    def test_listeners_dict_is_empty_on_init(self):
        """Verify that no listener is registered right after instantiation."""
        # GIVEN: Nothing
        # WHEN: Creating a new EventEmitter instance
        emitter = EventEmitter()

        # THEN: _listeners has no entries
        assert len(emitter._listeners) == 0


# ---------------------------------------------------------------------------
# Tests – on()
# ---------------------------------------------------------------------------


class TestEventEmitterOn:
    """Tests verifying the on() method registers callbacks correctly."""

    def test_on_registers_callback_for_event(self):
        """Verify that a callback is stored under the given event name."""
        # GIVEN: A fresh EventEmitter and a dummy callback
        emitter = EventEmitter()
        callback = lambda: None  # noqa: E731

        # WHEN: Registering the callback for an event
        emitter.on("my_event", callback)

        # THEN: The callback is accessible via _listeners
        assert emitter._listeners.get("my_event") is callback

    def test_on_returns_none(self):
        """Verify that on() returns None."""
        # GIVEN: A fresh EventEmitter and a dummy callback
        emitter = EventEmitter()

        # WHEN: Registering a callback
        result = emitter.on("my_event", lambda: None)

        # THEN: The return value is None
        assert result is None

    def test_on_overwrites_previous_callback_for_same_event(self):
        """Verify that registering a new callback replaces the previous one."""
        # GIVEN: An EventEmitter with an already-registered callback
        emitter = EventEmitter()
        first_callback = lambda: "first"  # noqa: E731
        second_callback = lambda: "second"  # noqa: E731
        emitter.on("my_event", first_callback)

        # WHEN: Registering a different callback for the same event
        emitter.on("my_event", second_callback)

        # THEN: Only the second callback is kept
        assert emitter._listeners["my_event"] is second_callback

    def test_on_registers_multiple_distinct_events(self):
        """Verify that several events can be registered independently."""
        # GIVEN: A fresh EventEmitter
        emitter = EventEmitter()
        cb_a = lambda: "a"  # noqa: E731
        cb_b = lambda: "b"  # noqa: E731

        # WHEN: Registering two separate events
        emitter.on("event_a", cb_a)
        emitter.on("event_b", cb_b)

        # THEN: Both events are stored with their respective callbacks
        assert emitter._listeners["event_a"] is cb_a
        assert emitter._listeners["event_b"] is cb_b
        assert len(emitter._listeners) == 2


# ---------------------------------------------------------------------------
# Tests – off()
# ---------------------------------------------------------------------------


class TestEventEmitterOff:
    """Tests verifying the off() method removes listeners correctly."""

    def test_off_removes_registered_listener(self):
        """Verify that off() removes the callback for the given event."""
        # GIVEN: An EventEmitter with a registered listener
        emitter = EventEmitter()
        emitter.on("my_event", lambda: None)

        # WHEN: Removing the listener
        emitter.off("my_event")

        # THEN: The event is no longer in _listeners
        assert "my_event" not in emitter._listeners

    def test_off_returns_none(self):
        """Verify that off() returns None on success."""
        # GIVEN: An EventEmitter with a registered listener
        emitter = EventEmitter()
        emitter.on("my_event", lambda: None)

        # WHEN: Removing the listener
        result = emitter.off("my_event")

        # THEN: The return value is None
        assert result is None

    def test_off_raises_unknown_event_error_for_unregistered_event(self):
        """Verify that off() raises UnknownEventError when the event is not registered."""
        # GIVEN: A fresh EventEmitter with no listeners
        emitter = EventEmitter()

        # WHEN: Attempting to remove a non-existent listener
        # THEN: UnknownEventError is raised
        with pytest.raises(UnknownEventError):
            emitter.off("ghost_event")

    def test_off_error_message_contains_event_name(self):
        """Verify that the UnknownEventError message includes the event name."""
        # GIVEN: A fresh EventEmitter with no listeners
        emitter = EventEmitter()

        # WHEN: Removing a non-existent listener
        # THEN: The error message references the event name
        with pytest.raises(UnknownEventError, match="ghost_event"):
            emitter.off("ghost_event")

    def test_off_only_removes_targeted_event(self):
        """Verify that off() does not affect other registered events."""
        # GIVEN: An EventEmitter with two registered listeners
        emitter = EventEmitter()
        emitter.on("event_a", lambda: None)
        emitter.on("event_b", lambda: None)

        # WHEN: Removing only event_a
        emitter.off("event_a")

        # THEN: event_b is still registered
        assert "event_a" not in emitter._listeners
        assert "event_b" in emitter._listeners


# ---------------------------------------------------------------------------
# Tests – emit()
# ---------------------------------------------------------------------------


class TestEventEmitterEmit:
    """Tests verifying the emit() method calls callbacks correctly."""

    async def test_emit_calls_registered_callback(self):
        """Verify that emit() invokes the callback associated with the event."""
        # GIVEN: An EventEmitter with a callback that records calls
        emitter = EventEmitter()
        call_log = []

        async def callback():
            call_log.append(True)

        emitter.on("my_event", callback)

        # WHEN: Emitting the event
        await emitter.emit("my_event")

        # THEN: The callback was called exactly once
        assert call_log == [True]

    async def test_emit_passes_positional_args_to_callback(self):
        """Verify that positional arguments are forwarded to the callback."""
        # GIVEN: An EventEmitter with a callback that captures its arguments
        emitter = EventEmitter()
        received = []

        async def callback(*args):
            received.extend(args)

        emitter.on("data_event", callback)

        # WHEN: Emitting with positional arguments
        await emitter.emit("data_event", 1, 2, 3)

        # THEN: The callback received all positional arguments
        assert received == [1, 2, 3]

    async def test_emit_passes_keyword_args_to_callback(self):
        """Verify that keyword arguments are forwarded to the callback."""
        # GIVEN: An EventEmitter with a callback that captures keyword arguments
        emitter = EventEmitter()
        received = {}

        async def callback(**kwargs):
            received.update(kwargs)

        emitter.on("data_event", callback)

        # WHEN: Emitting with keyword arguments
        await emitter.emit("data_event", status="ok", code=200)

        # THEN: The callback received all keyword arguments
        assert received == {"status": "ok", "code": 200}

    async def test_emit_passes_both_args_and_kwargs(self):
        """Verify that emit() forwards both positional and keyword arguments."""
        # GIVEN: An EventEmitter with a callback capturing all arguments
        emitter = EventEmitter()
        received_args = []
        received_kwargs = {}

        async def callback(*args, **kwargs):
            received_args.extend(args)
            received_kwargs.update(kwargs)

        emitter.on("full_event", callback)

        # WHEN: Emitting with mixed arguments
        await emitter.emit("full_event", "payload", key="value")

        # THEN: All arguments are forwarded correctly
        assert received_args == ["payload"]
        assert received_kwargs == {"key": "value"}

    async def test_emit_returns_none(self):
        """Verify that emit() returns None after calling the callback."""
        # GIVEN: An EventEmitter with a simple async callback
        emitter = EventEmitter()

        async def callback():
            pass

        emitter.on("my_event", callback)

        # WHEN: Emitting the event
        result = await emitter.emit("my_event")

        # THEN: The return value is None
        assert result is None

    async def test_emit_raises_unknown_event_error_for_unregistered_event(self):
        """Verify that emit() raises UnknownEventError when the event has no listener."""
        # GIVEN: A fresh EventEmitter with no listeners
        emitter = EventEmitter()

        # WHEN: Emitting an event that was never registered
        # THEN: UnknownEventError is raised
        with pytest.raises(UnknownEventError):
            await emitter.emit("ghost_event")

    async def test_emit_error_message_contains_event_name(self):
        """Verify that the UnknownEventError message includes the event name."""
        # GIVEN: A fresh EventEmitter with no listeners
        emitter = EventEmitter()

        # WHEN: Emitting an unregistered event
        # THEN: The error message references the event name
        with pytest.raises(UnknownEventError, match="ghost_event"):
            await emitter.emit("ghost_event")

    async def test_emit_calls_only_the_targeted_callback(self):
        """Verify that emitting one event does not trigger callbacks for other events."""
        # GIVEN: An EventEmitter with two distinct events
        emitter = EventEmitter()
        log_a = []
        log_b = []

        async def callback_a():
            log_a.append("a")

        async def callback_b():
            log_b.append("b")

        emitter.on("event_a", callback_a)
        emitter.on("event_b", callback_b)

        # WHEN: Emitting only event_a
        await emitter.emit("event_a")

        # THEN: Only callback_a was called
        assert log_a == ["a"]
        assert log_b == []
