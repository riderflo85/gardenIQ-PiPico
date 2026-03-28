# This code is a fork of a GitHub public repo
#   https://github.com/peterhinch/micropython-async/blob/master/v3/primitives/queue.py.
# Credit to Peter Hinch
# Change Queue._queue list type to collections.deque type.
# Secure Queue.task_done. Add check to ensure the all tasks in queue are done.

import asyncio
from collections import deque


# Exception raised by get_nowait().
class QueueEmpty(Exception):
    pass


# Exception raised by put_nowait().
class QueueFull(Exception):
    pass


class Queue:
    """
    An asynchronous queue implementation using asyncio Events and collections.deque.
    This queue provides both async and non-blocking methods for putting and getting items.
    It supports task synchronization through join() to wait for all queued tasks to complete.

    Attributes:
        maxsize (int): Maximum number of items the queue can hold. If 0, the queue is unbounded.
        _queue (deque): Internal deque storing queue items with a maximum length.
        _evput (asyncio.Event): Event triggered when an item is put into the queue.
        _evget (asyncio.Event): Event triggered when an item is removed from the queue.
        _jncnt (int): Counter tracking the number of unprocessed tasks in the queue.
        _jnevt (asyncio.Event): Event used to signal when all tasks have been processed (join counter <= 0).

    Methods:
        get(): Asynchronously retrieve and remove an item from the queue. Waits if queue is empty.
        get_nowait(): Non-blocking retrieval. Raises QueueEmpty if queue is empty.
        put(val): Asynchronously add an item to the queue. Waits if queue is full.
        put_nowait(val): Non-blocking insertion. Raises QueueFull if queue is full.
        qsize(): Return the current number of items in the queue.
        empty(): Return True if the queue contains no items.
        full(): Return True if the queue has reached maxsize capacity.
        task_done(): Decrement the join counter. Call after processing a queued task.
        join(): Asynchronously wait until all queued tasks have been marked as done.

    Raises:
        QueueEmpty: Raised by get_nowait() when attempting to get from an empty queue.
        QueueFull: Raised by put_nowait() when attempting to put into a full queue.
        Exception: Raised by task_done() if called more times than items were put in the queue.
    """

    def __init__(self, maxsize: int):
        self.maxsize = maxsize
        self._queue = deque(maxlen=self.maxsize)
        self._evput = asyncio.Event()  # Triggered by put, tested by get
        self._evget = asyncio.Event()  # Triggered by get, tested by put

        self._jncnt = 0
        self._jnevt = asyncio.Event()
        self._upd_jnevt(0)  # update join event

    def _get(self):
        self._evget.set()  # Schedule all tasks waiting on get
        self._evget.clear()
        return self._queue.popleft()

    async def get(self):  # Usage: item = await queue.get()
        while self.empty():  # May be multiple tasks waiting on get()
            # Queue is empty, suspend task until a put occurs
            # 1st of N tasks gets, the rest loop again
            await self._evput.wait()
        return self._get()

    def get_nowait(self):  # Remove and return an item from the queue.
        # Return an item if one is immediately available, else raise QueueEmpty.
        if self.empty():
            raise QueueEmpty()
        return self._get()

    def _put(self, val):
        self._upd_jnevt(1)  # update join event
        self._evput.set()  # Schedule tasks waiting on put
        self._evput.clear()
        self._queue.append(val)

    async def put(self, val):  # Usage: await queue.put(item)
        while self.full():
            # Queue full
            await self._evget.wait()
            # Task(s) waiting to get from queue, schedule first Task
        self._put(val)

    def put_nowait(self, val):  # Put an item into the queue without blocking.
        if self.full():
            raise QueueFull()
        self._put(val)

    def qsize(self) -> int:  # Number of items in the queue.
        return len(self._queue)

    def empty(self) -> bool:  # Return True if the queue is empty, False otherwise.
        return len(self._queue) == 0

    def full(self) -> bool:  # Return True if there are maxsize items in the queue.
        # Note: if the Queue was initialized with maxsize=0 then full() is never True.
        return self.maxsize > 0 and self.qsize() >= self.maxsize

    def _upd_jnevt(self, inc: int):  # Update join count and join event
        self._jncnt += inc
        if self._jncnt <= 0:
            self._jnevt.set()
        else:
            self._jnevt.clear()

    def task_done(self):  # Task Done decrements counter
        if self._jncnt <= 0:
            raise Exception("task_done() called many times. Join counter: %s" % self._jncnt)
        self._upd_jnevt(-1)

    async def join(self):  # Wait for join event
        await self._jnevt.wait()
