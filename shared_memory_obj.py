import queue
from collections import defaultdict

subscribers = defaultdict(list)
q_mapping = {}
register_queue = queue.Queue()
response_queue = queue.Queue()
