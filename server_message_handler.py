import traceback

from shared_memory_obj import subscribers, response_queue


async def on_message(conn, subject, msg):
    """
    This is the handler for server messages. We then iterate the subscribers
    and send the message through the opened websockets
    """
    # iterate channels and distribute the message to correct subscribers
    try:
        for sub, channels in subscribers.items():
            if msg['stream'] in [c.replace('alpacadatav1/', '') for c in channels]:
                response_queue.put({"subscriber": sub,
                                    "response":   msg})
    except Exception as e:
        print(e)
        traceback.print_exc()
