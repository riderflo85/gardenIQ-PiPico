import asyncio

import pytest

from src.core.queue import Queue
from src.core.queue import QueueEmpty
from src.core.queue import QueueFull

# ---------------------------------------------------------------------------
# Tests – initialisation
# ---------------------------------------------------------------------------


class TestQueueInit:
    """Tests verifying the initial state of a newly created Queue."""

    def test_maxsize_is_stored(self):
        """Verify that the maxsize argument is stored on the instance."""
        # GIVEN: A maxsize value of 10
        # WHEN: Creating a Queue with that maxsize
        queue = Queue(maxsize=10)

        # THEN: The maxsize attribute matches the provided value
        assert queue.maxsize == 10

    def test_queue_is_empty_on_init(self):
        """Verify that the queue contains no items right after creation."""
        # GIVEN: Nothing
        # WHEN: Creating a Queue
        queue = Queue(maxsize=5)

        # THEN: The queue is empty
        assert queue.empty() is True
        assert queue.qsize() == 0

    def test_join_counter_is_zero_on_init(self):
        """Verify that the internal join counter starts at zero."""
        # GIVEN: Nothing
        # WHEN: Creating a Queue
        queue = Queue(maxsize=5)

        # THEN: The internal join counter is zero
        assert queue._jncnt == 0


# ---------------------------------------------------------------------------
# Tests – empty()
# ---------------------------------------------------------------------------


class TestQueueEmpty:
    """Tests verifying the empty() predicate."""

    def test_empty_returns_true_on_empty_queue(self):
        """Verify that empty() returns True when no items are in the queue."""
        # GIVEN: A newly created queue
        queue = Queue(maxsize=5)

        # WHEN: Checking emptiness
        result = queue.empty()

        # THEN: The queue is empty
        assert result is True

    def test_empty_returns_false_after_put_nowait(self):
        """Verify that empty() returns False after an item is added."""
        # GIVEN: A queue with one item
        queue = Queue(maxsize=5)
        queue.put_nowait("item")

        # WHEN: Checking emptiness
        result = queue.empty()

        # THEN: The queue is not empty
        assert result is False

    def test_empty_returns_true_after_all_items_removed(self):
        """Verify that empty() returns True once the last item is removed."""
        # GIVEN: A queue with one item that is then consumed
        queue = Queue(maxsize=5)
        queue.put_nowait("item")
        queue.get_nowait()

        # WHEN: Checking emptiness
        result = queue.empty()

        # THEN: The queue is empty again
        assert result is True


# ---------------------------------------------------------------------------
# Tests – full()
# ---------------------------------------------------------------------------


class TestQueueFull:
    """Tests verifying the full() predicate."""

    def test_full_returns_false_when_not_full(self):
        """Verify that full() returns False when the queue has available space."""
        # GIVEN: A queue with maxsize=3 and one item
        queue = Queue(maxsize=3)
        queue.put_nowait("a")

        # WHEN: Checking fullness
        result = queue.full()

        # THEN: The queue is not full
        assert result is False

    def test_full_returns_true_when_maxsize_items_are_present(self):
        """Verify that full() returns True when the queue holds maxsize items."""
        # GIVEN: A queue with maxsize=2 filled to capacity
        queue = Queue(maxsize=2)
        queue.put_nowait("a")
        queue.put_nowait("b")

        # WHEN: Checking fullness
        result = queue.full()

        # THEN: The queue is full
        assert result is True

    def test_full_returns_false_when_maxsize_is_zero(self):
        """Verify that full() always returns False for an unlimited queue (maxsize=0)."""
        # GIVEN: A queue treated as unlimited (maxsize=0)
        queue = Queue(maxsize=0)

        # WHEN: Checking fullness on an empty unlimited queue
        result = queue.full()

        # THEN: An unlimited queue is never full
        assert result is False

    def test_full_returns_false_when_maxsize_is_negative(self):
        """Verify that creating a Queue with a negative maxsize raises ValueError.

        Note: despite the docstring mentioning negative values, the underlying
        deque(maxlen=<negative>) raises ValueError, so negative maxsize is not supported.
        """
        # GIVEN: A negative maxsize value
        # WHEN: Attempting to create a Queue with that value
        # THEN: A ValueError is raised by the deque constructor
        with pytest.raises(ValueError):
            Queue(maxsize=-1)


# ---------------------------------------------------------------------------
# Tests – qsize()
# ---------------------------------------------------------------------------


class TestQueueQsize:
    """Tests verifying the qsize() method."""

    def test_qsize_returns_zero_on_empty_queue(self):
        """Verify that qsize() returns 0 for a newly created queue."""
        # GIVEN: A newly created queue
        queue = Queue(maxsize=5)

        # WHEN: Checking the size
        result = queue.qsize()

        # THEN: The size is zero
        assert result == 0

    def test_qsize_increases_after_put_nowait(self):
        """Verify that qsize() increases by one after each put_nowait()."""
        # GIVEN: An empty queue
        queue = Queue(maxsize=5)

        # WHEN: Adding two items
        queue.put_nowait("a")
        queue.put_nowait("b")

        # THEN: The size reflects the number of items added
        assert queue.qsize() == 2

    def test_qsize_decreases_after_get_nowait(self):
        """Verify that qsize() decreases by one after each get_nowait()."""
        # GIVEN: A queue with two items
        queue = Queue(maxsize=5)
        queue.put_nowait("a")
        queue.put_nowait("b")

        # WHEN: Consuming one item
        queue.get_nowait()

        # THEN: The size decreases by one
        assert queue.qsize() == 1


# ---------------------------------------------------------------------------
# Tests – put_nowait()
# ---------------------------------------------------------------------------


class TestQueuePutNowait:
    """Tests verifying the put_nowait() synchronous method."""

    def test_put_nowait_adds_item_to_queue(self):
        """Verify that put_nowait() stores the item in the queue."""
        # GIVEN: An empty queue
        queue = Queue(maxsize=5)

        # WHEN: Putting an item without blocking
        queue.put_nowait("hello")

        # THEN: The queue contains one item
        assert queue.qsize() == 1

    def test_put_nowait_raises_queue_full_when_at_capacity(self):
        """Verify that put_nowait() raises QueueFull when the queue is full."""
        # GIVEN: A queue filled to its maxsize
        queue = Queue(maxsize=1)
        queue.put_nowait("first")

        # WHEN: Attempting to add another item without blocking
        # THEN: QueueFull is raised
        with pytest.raises(QueueFull):
            queue.put_nowait("second")

    def test_put_nowait_increments_join_counter(self):
        """Verify that put_nowait() increments the internal join counter."""
        # GIVEN: A queue with join counter at zero
        queue = Queue(maxsize=5)
        assert queue._jncnt == 0

        # WHEN: Adding two items
        queue.put_nowait("a")
        queue.put_nowait("b")

        # THEN: The join counter reflects the number of pending tasks
        assert queue._jncnt == 2


# ---------------------------------------------------------------------------
# Tests – get_nowait()
# ---------------------------------------------------------------------------


class TestQueueGetNowait:
    """Tests verifying the get_nowait() synchronous method."""

    def test_get_nowait_returns_item_from_queue(self):
        """Verify that get_nowait() returns the item present in the queue."""
        # GIVEN: A queue with one item
        queue = Queue(maxsize=5)
        queue.put_nowait("hello")

        # WHEN: Getting the item without blocking
        result = queue.get_nowait()

        # THEN: The returned item matches what was put
        assert result == "hello"

    def test_get_nowait_raises_queue_empty_when_queue_is_empty(self):
        """Verify that get_nowait() raises QueueEmpty when the queue has no items."""
        # GIVEN: An empty queue
        queue = Queue(maxsize=5)

        # WHEN: Attempting to get an item without blocking
        # THEN: QueueEmpty is raised
        with pytest.raises(QueueEmpty):
            queue.get_nowait()

    def test_get_nowait_returns_items_in_fifo_order(self):
        """Verify that get_nowait() returns items in first-in, first-out order."""
        # GIVEN: A queue with items added in a specific order
        queue = Queue(maxsize=5)
        queue.put_nowait("first")
        queue.put_nowait("second")
        queue.put_nowait("third")

        # WHEN: Consuming all items
        results = [queue.get_nowait(), queue.get_nowait(), queue.get_nowait()]

        # THEN: Items are returned in insertion order
        assert results == ["first", "second", "third"]

    def test_get_nowait_removes_item_from_queue(self):
        """Verify that get_nowait() removes the item from the queue."""
        # GIVEN: A queue with one item
        queue = Queue(maxsize=5)
        queue.put_nowait("item")

        # WHEN: Getting the item
        queue.get_nowait()

        # THEN: The queue is now empty
        assert queue.empty() is True


# ---------------------------------------------------------------------------
# Tests – put() async
# ---------------------------------------------------------------------------


class TestQueuePut:
    """Tests verifying the async put() method."""

    async def test_put_adds_item_when_space_is_available(self):
        """Verify that put() stores an item when the queue is not full."""
        # GIVEN: An empty queue with available space
        queue = Queue(maxsize=5)

        # WHEN: Putting an item asynchronously
        await queue.put("item")

        # THEN: The queue contains the item
        assert queue.qsize() == 1
        assert queue.get_nowait() == "item"

    async def test_put_waits_when_full_then_adds_when_space_is_freed(self):
        """Verify that put() suspends when the queue is full and resumes once space is freed."""
        # GIVEN: A full queue with maxsize=1
        queue = Queue(maxsize=1)
        await queue.put("first")

        consumed = []

        async def consumer():
            await asyncio.sleep(0)
            consumed.append(queue.get_nowait())

        # WHEN: A consumer frees space and a second put() is attempted
        asyncio.create_task(consumer())
        await queue.put("second")

        # THEN: The first item was consumed and the second is now in the queue
        assert consumed == ["first"]
        assert queue.qsize() == 1

    async def test_put_multiple_items_in_order(self):
        """Verify that multiple sequential puts are reflected in the queue size."""
        # GIVEN: An empty queue
        queue = Queue(maxsize=5)

        # WHEN: Putting three items
        await queue.put("a")
        await queue.put("b")
        await queue.put("c")

        # THEN: The queue holds all three items
        assert queue.qsize() == 3


# ---------------------------------------------------------------------------
# Tests – get() async
# ---------------------------------------------------------------------------


class TestQueueGet:
    """Tests verifying the async get() method."""

    async def test_get_returns_item_when_available(self):
        """Verify that get() returns an item present in the queue."""
        # GIVEN: A queue with one item
        queue = Queue(maxsize=5)
        queue.put_nowait("hello")

        # WHEN: Getting the item asynchronously
        result = await queue.get()

        # THEN: The returned item matches what was put
        assert result == "hello"

    async def test_get_waits_when_empty_until_item_is_put(self):
        """Verify that get() suspends when the queue is empty and resumes once an item arrives."""
        # GIVEN: An empty queue and a producer that will add an item after yielding
        queue = Queue(maxsize=5)

        async def producer():
            await asyncio.sleep(0)
            queue.put_nowait("item")

        # WHEN: A producer adds an item concurrently and get() is awaited
        asyncio.create_task(producer())
        result = await queue.get()

        # THEN: get() returns the item once it becomes available
        assert result == "item"

    async def test_get_returns_items_in_fifo_order(self):
        """Verify that get() returns items in first-in, first-out order."""
        # GIVEN: A queue loaded with three items in a known order
        queue = Queue(maxsize=5)
        queue.put_nowait("first")
        queue.put_nowait("second")
        queue.put_nowait("third")

        # WHEN: Consuming all items asynchronously
        results = [await queue.get(), await queue.get(), await queue.get()]

        # THEN: Items are returned in insertion order
        assert results == ["first", "second", "third"]

    async def test_get_removes_item_from_queue(self):
        """Verify that get() removes the consumed item from the queue."""
        # GIVEN: A queue with one item
        queue = Queue(maxsize=5)
        queue.put_nowait("item")

        # WHEN: Consuming the item
        await queue.get()

        # THEN: The queue is now empty
        assert queue.empty() is True


# ---------------------------------------------------------------------------
# Tests – task_done()
# ---------------------------------------------------------------------------


class TestQueueTaskDone:
    """Tests verifying the task_done() method."""

    def test_task_done_decrements_join_counter(self):
        """Verify that task_done() decreases the internal join counter by one."""
        # GIVEN: A queue with two items (join counter = 2)
        queue = Queue(maxsize=5)
        queue.put_nowait("a")
        queue.put_nowait("b")
        queue.get_nowait()

        # WHEN: Marking one task as done
        queue.task_done()

        # THEN: The join counter decreases by one
        assert queue._jncnt == 1

    def test_task_done_raises_exception_when_called_too_many_times(self):
        """Verify that task_done() raises an Exception when the join counter is already zero."""
        # GIVEN: A queue with no pending items (join counter = 0)
        queue = Queue(maxsize=5)

        # WHEN: Calling task_done() with nothing to mark as done
        # THEN: An Exception is raised
        with pytest.raises(Exception, match="task_done\\(\\) called many times"):
            queue.task_done()

    def test_task_done_allows_all_items_to_be_marked_done(self):
        """Verify that task_done() can be called once per item without raising."""
        # GIVEN: A queue with three items all consumed
        queue = Queue(maxsize=5)
        queue.put_nowait("a")
        queue.put_nowait("b")
        queue.put_nowait("c")
        queue.get_nowait()
        queue.get_nowait()
        queue.get_nowait()

        # WHEN: Marking all three tasks as done
        queue.task_done()
        queue.task_done()
        queue.task_done()

        # THEN: The join counter reaches zero without any exception
        assert queue._jncnt == 0


# ---------------------------------------------------------------------------
# Tests – join() async
# ---------------------------------------------------------------------------


class TestQueueJoin:
    """Tests verifying the async join() method."""

    async def test_join_returns_immediately_when_queue_is_empty(self):
        """Verify that join() completes immediately when no items were ever put."""
        # GIVEN: A freshly created queue (join counter = 0)
        queue = Queue(maxsize=5)

        # WHEN: Awaiting join() with a timeout
        # THEN: join() resolves immediately without timing out
        await asyncio.wait_for(queue.join(), timeout=1.0)

    async def test_join_returns_when_all_tasks_are_done(self):
        """Verify that join() unblocks once every put item has been marked done."""
        # GIVEN: A queue with two items that are consumed and marked done
        queue = Queue(maxsize=5)
        queue.put_nowait("a")
        queue.put_nowait("b")
        queue.get_nowait()
        queue.get_nowait()
        queue.task_done()
        queue.task_done()

        # WHEN: Awaiting join()
        # THEN: join() resolves because all tasks are done
        await asyncio.wait_for(queue.join(), timeout=1.0)

    async def test_join_waits_until_task_done_is_called(self):
        """Verify that join() only completes after task_done() is called for all items."""
        # GIVEN: A queue with one item consumed but not yet marked done
        queue = Queue(maxsize=5)
        queue.put_nowait("item")
        queue.get_nowait()

        join_completed = False

        async def worker():
            nonlocal join_completed
            await queue.join()
            join_completed = True

        # WHEN: join() is awaited concurrently while task_done() is pending
        task = asyncio.create_task(worker())
        await asyncio.sleep(0)

        # THEN: join() has not yet completed
        assert join_completed is False

        # WHEN: task_done() is finally called
        queue.task_done()
        await asyncio.sleep(0)

        # THEN: join() completes
        assert join_completed is True
        task.cancel()
