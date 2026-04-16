from src.core.queue import Queue

# Queue to store data received from USB communication. Max size is 30, but it can be changed if needed.
data_received = Queue(maxsize=30)

# Queue to store data to send back to the USB opened connection. Max size is 30, but it can be changed if needed.
data_to_response = Queue(maxsize=30)
