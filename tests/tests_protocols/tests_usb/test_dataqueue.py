import importlib

import pytest

import src.protocols.usb.dataqueue as dataqueue_module
from src.core.queue import Queue

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def fresh_dataqueue():
    """Reload the dataqueue module before each test to reset singleton state."""
    importlib.reload(dataqueue_module)
    yield dataqueue_module


# ---------------------------------------------------------------------------
# Tests – data_received
# ---------------------------------------------------------------------------


class TestDataReceived:
    """Tests verifying the data_received queue instance."""

    def test_data_received_is_a_queue_instance(self, fresh_dataqueue):
        """Verify that data_received is an instance of Queue."""
        # GIVEN: The dataqueue module is freshly loaded
        # WHEN: Accessing the data_received attribute
        # THEN: The object is a Queue instance
        assert isinstance(fresh_dataqueue.data_received, Queue)

    def test_data_received_maxsize_is_30(self, fresh_dataqueue):
        """Verify that data_received is configured with a maxsize of 30."""
        # GIVEN: The dataqueue module is freshly loaded
        # WHEN: Reading the maxsize attribute
        # THEN: The maxsize equals 30
        assert fresh_dataqueue.data_received.maxsize == 30

    def test_data_received_is_empty_on_import(self, fresh_dataqueue):
        """Verify that data_received contains no items when the module is first imported."""
        # GIVEN: The dataqueue module is freshly loaded
        # WHEN: Checking the queue state
        # THEN: The queue is empty
        assert fresh_dataqueue.data_received.empty() is True
        assert fresh_dataqueue.data_received.qsize() == 0

    def test_data_received_accepts_items(self, fresh_dataqueue):
        """Verify that data_received can store and retrieve items."""
        # GIVEN: A fresh data_received queue
        queue = fresh_dataqueue.data_received

        # WHEN: Putting an item without blocking
        queue.put_nowait("frame_data")

        # THEN: The item is stored and can be retrieved in FIFO order
        assert queue.qsize() == 1
        assert queue.get_nowait() == "frame_data"

    def test_data_received_respects_maxsize(self, fresh_dataqueue):
        """Verify that data_received raises QueueFull once 30 items are stored."""
        from src.core.queue import QueueFull

        # GIVEN: A fresh data_received queue filled to its maxsize of 30
        queue = fresh_dataqueue.data_received
        for i in range(30):
            queue.put_nowait(i)

        # WHEN: Attempting to add a 31st item
        # THEN: QueueFull is raised
        with pytest.raises(QueueFull):
            queue.put_nowait("overflow")


# ---------------------------------------------------------------------------
# Tests – data_to_response
# ---------------------------------------------------------------------------


class TestDataToResponse:
    """Tests verifying the data_to_response queue instance."""

    def test_data_to_response_is_a_queue_instance(self, fresh_dataqueue):
        """Verify that data_to_response is an instance of Queue."""
        # GIVEN: The dataqueue module is freshly loaded
        # WHEN: Accessing the data_to_response attribute
        # THEN: The object is a Queue instance
        assert isinstance(fresh_dataqueue.data_to_response, Queue)

    def test_data_to_response_maxsize_is_30(self, fresh_dataqueue):
        """Verify that data_to_response is configured with a maxsize of 30."""
        # GIVEN: The dataqueue module is freshly loaded
        # WHEN: Reading the maxsize attribute
        # THEN: The maxsize equals 30
        assert fresh_dataqueue.data_to_response.maxsize == 30

    def test_data_to_response_is_empty_on_import(self, fresh_dataqueue):
        """Verify that data_to_response contains no items when the module is first imported."""
        # GIVEN: The dataqueue module is freshly loaded
        # WHEN: Checking the queue state
        # THEN: The queue is empty
        assert fresh_dataqueue.data_to_response.empty() is True
        assert fresh_dataqueue.data_to_response.qsize() == 0

    def test_data_to_response_accepts_items(self, fresh_dataqueue):
        """Verify that data_to_response can store and retrieve items."""
        # GIVEN: A fresh data_to_response queue
        queue = fresh_dataqueue.data_to_response

        # WHEN: Putting an item without blocking
        queue.put_nowait(b"\x01\x02\x03")

        # THEN: The item is stored and can be retrieved in FIFO order
        assert queue.qsize() == 1
        assert queue.get_nowait() == b"\x01\x02\x03"

    def test_data_to_response_respects_maxsize(self, fresh_dataqueue):
        """Verify that data_to_response raises QueueFull once 30 items are stored."""
        from src.core.queue import QueueFull

        # GIVEN: A fresh data_to_response queue filled to its maxsize of 30
        queue = fresh_dataqueue.data_to_response
        for i in range(30):
            queue.put_nowait(i)

        # WHEN: Attempting to add a 31st item
        # THEN: QueueFull is raised
        with pytest.raises(QueueFull):
            queue.put_nowait("overflow")


# ---------------------------------------------------------------------------
# Tests – independence between the two queues
# ---------------------------------------------------------------------------


class TestDataqueuesIndependence:
    """Tests verifying that data_received and data_to_response are independent objects."""

    def test_queues_are_distinct_objects(self, fresh_dataqueue):
        """Verify that data_received and data_to_response are not the same object."""
        # GIVEN: The dataqueue module is freshly loaded
        # WHEN: Comparing the two queue instances
        # THEN: They are different objects
        assert fresh_dataqueue.data_received is not fresh_dataqueue.data_to_response

    def test_putting_item_in_data_received_does_not_affect_data_to_response(self, fresh_dataqueue):
        """Verify that writing to data_received leaves data_to_response unaffected."""
        # GIVEN: Both queues are empty
        received = fresh_dataqueue.data_received
        to_response = fresh_dataqueue.data_to_response

        # WHEN: Adding an item to data_received only
        received.put_nowait("incoming")

        # THEN: data_to_response remains empty
        assert to_response.empty() is True

    def test_putting_item_in_data_to_response_does_not_affect_data_received(self, fresh_dataqueue):
        """Verify that writing to data_to_response leaves data_received unaffected."""
        # GIVEN: Both queues are empty
        received = fresh_dataqueue.data_received
        to_response = fresh_dataqueue.data_to_response

        # WHEN: Adding an item to data_to_response only
        to_response.put_nowait("outgoing")

        # THEN: data_received remains empty
        assert received.empty() is True

    def test_each_queue_maintains_its_own_fifo_order(self, fresh_dataqueue):
        """Verify that each queue maintains its own independent FIFO order."""
        # GIVEN: Items added to both queues in different orders
        received = fresh_dataqueue.data_received
        to_response = fresh_dataqueue.data_to_response

        received.put_nowait("rx_first")
        received.put_nowait("rx_second")
        to_response.put_nowait("tx_first")
        to_response.put_nowait("tx_second")

        # WHEN: Consuming items from each queue
        rx_items = [received.get_nowait(), received.get_nowait()]
        tx_items = [to_response.get_nowait(), to_response.get_nowait()]

        # THEN: Each queue returns its own items in insertion order
        assert rx_items == ["rx_first", "rx_second"]
        assert tx_items == ["tx_first", "tx_second"]
