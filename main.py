#!/usr/bin/env python

import asyncio
import json

import websockets
import threading
import alpaca_trade_api as tradeapi
from alpaca_trade_api.common import URL
from websockets.protocol import State

from server_message_handler import on_message
from shared_memory_obj import q_mapping, subscribers, response_queue
from version import VERSION
from asciiart import ascii_art
from threading import Lock

lock = Lock()


conn: tradeapi.StreamConn = None
_key_id = None
_secret_key = None
_authenticated = False
_base_url = "https://paper-api.alpaca.markets"
_data_url = "https://data.alpaca.markets"


async def on_auth(conn, stream, msg):
    pass


async def on_account(conn, stream, msg):
    q_mapping[msg.symbol].put(msg)


async def listen(conn, channel, msg):
    if hasattr(msg, 'error'):
        print('listening error', msg.error)


async def on_trade(conn, stream, msg):
    if msg.order['symbol'] in q_mapping:
        q_mapping[msg.order['symbol']].put(msg.order)


CONSUMER_STARTED = False
def consumer_thread(channels):
    try:
        # make sure we have an event loop, if not create a new one
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())
    global conn
    if not conn:
        conn = tradeapi.StreamConn(
            key_id=_key_id,
            secret_key=_secret_key,
            base_url=URL(_base_url),
            data_url=URL(_data_url),
            data_stream='alpacadatav1',
            raw_data=True,
        )

        conn.on('authenticated')(on_auth)
        conn.on(r'Q.*')(on_message)
        conn.on(r'T.*')(on_message)

        conn.on(r'listening')(listen)


        conn.on(r'AM.*')(on_message)
        conn.on(r'account_updates')(on_account)
        conn.on(r'trade_updates')(on_trade)
        conn.run(channels)


async def get_current_channels():
    result = []
    for sub, chans in subscribers.items():
        result.extend(chans)
    result = list(set(result))  # we want the list to be unique
    return result


async def clear_dead_subscribers():
    # copy to be able to remove closed connections
    subs = dict(subscribers.items())
    for sub, chans in subs.items():
        if sub.state == State.CLOSED:
            del subscribers[sub]


async def serve(sub, path):
    global conn, _key_id, _secret_key
    global CONSUMER_STARTED
    try:
        async for msg in sub:
            # msg = await sub.recv()
            try:
                data = json.loads(msg)
                print(f"< {data}")
            except Exception as e:
                print(e)

            if sub not in subscribers.keys():
                if data.get("action"):
                    if data.get("action") == "authenticate":
                        if not _key_id:
                            _key_id = data.get("data").get("key_id")
                            _secret_key = data.get("data").get(
                                "secret_key")
                # not really authorized yet.
                # but sending because it's expected
                response = json.dumps({
                    "data": {"status": "authorized"},
                    "stream": "authorization"
                })
                await sub.send(response)
                subscribers[sub] = []

            else:
                if data.get("action") == "listen":
                    new_channels = data.get("data").get("streams")

                previous_channels = await get_current_channels()
                if previous_channels:
                    await conn.unsubscribe(previous_channels)
                    await clear_dead_subscribers()

                subscribers[sub] = new_channels
                with lock:
                    if not CONSUMER_STARTED:
                        CONSUMER_STARTED = True
                        threading.Thread(target=consumer_thread,
                                         args=(new_channels, )).start()
                    else:
                        channels = await get_current_channels()
                        await conn.subscribe(channels)
    except Exception as e:
        print(e)
    print("Done")

    # while 1:
    #     count += 1
    #     await websocket.send(f"{greeting} {count}")
    #     # print(f"> {greeting}")
    #     await asyncio.sleep(3)


async def send_response_to_client():
    """
    The messages sent back to the clients should be sent from the same thread
    that accepted the connection. it a websocket issue.
    messages from the server are received via a different thread and passed to
    this thread(the main thread) using a queue. then this thread( the main
    thread) is passing the messages to the clients.
    :return:
    """
    while 1:
        try:
            if response_queue.empty():
                await asyncio.sleep(0.05)
                continue
            response = response_queue.get()
            await response["subscriber"].send(json.dumps(response["response"]))
        except:
            pass


if __name__ == '__main__':
    import logging

    logging.basicConfig(format='%(asctime)s %(name)s %(message)s',
                        level=logging.INFO)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger('websockets').setLevel(logging.INFO)

    #
    print(ascii_art)
    logging.info(f"Alpaca Proxy Agent v{VERSION}")
    logging.info(f"Using the Alpaca Websocket")
    start_server = websockets.serve(serve, "0.0.0.0", 8765)

    # asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_until_complete(asyncio.gather(
        start_server,
        send_response_to_client(),
        return_exceptions=True,
    ))
    asyncio.get_event_loop().run_forever()
