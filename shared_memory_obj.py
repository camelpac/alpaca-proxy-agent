import queue

subscribers = {}
q_mapping = {}
register_queue = queue.Queue()
response_queue = queue.Queue()
