#!/usr/bin/env python

# WS server example

import asyncio
import json
import websockets
import queue
import threading
import alpaca_trade_api as tradeapi
from websockets.protocol import State

subscribers = {}
q_mapping = {}
register_queue = queue.Queue()
response_queue = queue.Queue()

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


async def on_quotes(conn, subject, msg):
    msg._raw['time'] = msg.timestamp.to_pydatetime().timestamp()
    # copy to be able to remove closed connections or add new ones
    subs = dict(subscribers.items())
    for sub, channels in subs.items():
        if "alpacadatav1/Q." + msg.symbol in channels:
            if sub.state != State.CLOSED:
                await sub.send(json.dumps(msg._raw))
            else:
                del subscribers[sub]


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
        conn = tradeapi.StreamConn(key_id=_key_id,
                                   secret_key=_secret_key,
                                   base_url=_base_url,
                                   data_stream="alpacadatav1")

        conn.on('authenticated')(on_auth)
        conn.on(r'Q.*')(on_quotes)
        conn.on(r'account_updates')(on_account)
        conn.on(r'trade_updates')(on_trade)
    asyncio.get_event_loop().run_until_complete(conn.subscribe(channels))
    asyncio.get_event_loop().run_until_complete(conn.consume())


async def serve(sub, path):
    global conn, _key_id, _secret_key
    global CONSUMER_STARTED
    try:
        async for msg in sub:
            # msg = await sub.recv()
            data = json.loads(msg)
            # print(f"< {data}")

            if sub not in subscribers.keys():
                if data.get("action"):
                    if data.get("action") == "authenticate":
                        if not _key_id:
                            _key_id = data.get("data").get("key_id")
                            _secret_key = data.get("data").get("secret_key")
                subscribers[sub] = []

                # not really authorized yet. but sending because it's expected
                response = json.dumps({"data": {"status": "authorized"}})
                await sub.send(response)
            else:
                if data.get("action"):
                    if data.get("action") == "listen":
                        channels = data.get("data").get("streams")
                        subscribers[sub] = channels

                        # conn.run(channels)
                        # loop = asyncio.get_event_loop()
                        if not CONSUMER_STARTED:
                            CONSUMER_STARTED = True
                            threading.Thread(target=consumer_thread, args=(channels, )).start()
                        else:
                            # channels = [for s in subscribers.values():

                            await conn.subscribe(channels)
    except:
        pass
    print("Done")

    # while 1:
    #     count += 1
    #     await websocket.send(f"{greeting} {count}")
    #     # print(f"> {greeting}")
    #     await asyncio.sleep(3)

async def a():
    while 1:
        await asyncio.sleep(1)
        print("a")


async def b():
    while 1:
        await asyncio.sleep(1)
        print("B")


if __name__ == '__main__':
    # asyncio.gather(a(), b())
    # asyncio.get_event_loop().run_until_complete(a())
    # asyncio.get_event_loop().run_until_complete(b())
    # asyncio.get_event_loop().run_forever()
    #
    start_server = websockets.serve(serve, "localhost", 8765)

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()

"""
main thread:
- accepts new connections
  - registers the symbols

- thread for alpaca ws. 



"""