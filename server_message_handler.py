import traceback

from shared_memory_obj import subscribers, response_queue


async def on_message(msg):
    """
    This is the handler for server messages. We then iterate the subscribers
    and send the message through the opened websockets
    the message is received with msgpack short types, but when we subscribe
    we use long types (e.g 't' vs 'trades') and this is how we keep track of it
    we need to translate it first and then send it.
    """
    msg_type = msg.get('T')
    symbol = msg.get('S')
    if msg_type == 't':
        _type = 'trades'
    elif msg_type == 'q':
        _type = 'quotes'
    elif msg_type == 'b':
        _type = 'bars'
    elif msg_type == 'd':
        _type = 'dailyBars'
    elif msg_type == 's':
        _type = 'statuses'
    else:
        return
    try:
        for sub, channels in subscribers.items():
            if symbol in channels[_type]:
                response_queue.put({"subscriber": sub,
                                    "response":   msg})
    except Exception as e:
        print(e)
        traceback.print_exc()
