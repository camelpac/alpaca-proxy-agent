#!/usr/bin/env python

# WS server example

import asyncio
import json
import websockets
import queue
import threading
import alpaca_trade_api as tradeapi
from alpaca_trade_api.common import URL
from alpaca_trade_api.entity import quote_mapping
from alpaca_trade_api.polygon.entity import quote_mapping as \
    polygon_quote_mapping
from websockets.protocol import State

subscribers = {}
q_mapping = {}
register_queue = queue.Queue()
response_queue = queue.Queue()
reverse_qoute_mapping = {v: k for k, v in quote_mapping.items()}
reverse_polygon_qoute_mapping = {
    v: k for k, v in polygon_quote_mapping.items()
}

conn: tradeapi.StreamConn = None
_key_id = None
_secret_key = None
_authenticated = False
_base_url = "https://paper-api.alpaca.markets"
USE_POLYGON = False
_data_url = "https://data.alpaca.markets"
QUOTE_PREFIX = "Q." if USE_POLYGON else "alpacadatav1/Q."

async def on_auth(conn, stream, msg):
    pass


async def on_account(conn, stream, msg):
    q_mapping[msg.symbol].put(msg)


async def on_quotes(conn, subject, msg):
    def _restructure_original_msg(m):
        """
        the sdk translate the message received from the server to a more
        readable format. so this is how we get it (readable). but when we pass
        it to the clients using this proxy, the clients expects the message to
        be not readable (or, server compact), and tries to translate it to
        readable format. so this method converts it back to the expected format
        :param m:
        :return:
        """
        if USE_POLYGON:
            data = {reverse_polygon_qoute_mapping[k]: v for
                    k, v in m._raw.items() if
                    k in reverse_polygon_qoute_mapping}
            data['ev'] = 'Q'
            data['sym'] = m.symbol
            message = [data]
        else:
            message = {
                'stream': f"Q.{m.symbol}",
                'data': {reverse_qoute_mapping[k]: v for k, v in
                         m._raw.items() if k in reverse_qoute_mapping}
            }
        return message
    msg._raw['time'] = msg.timestamp.to_pydatetime().timestamp()

    # copy subscribers list to be able to remove closed connections or add new
    # ones
    subs = dict(subscribers.items())
    # iterate channels and distribute the message to correct subscribers
    for sub, channels in subs.items():
        if QUOTE_PREFIX + msg.symbol in channels:
            if sub.state != State.CLOSED:
                await sub.send(json.dumps(_restructure_original_msg(msg)))
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
        conn = tradeapi.StreamConn(
            key_id=_key_id,
            secret_key=_secret_key if not USE_POLYGON else 'DUMMY',
            base_url=URL(_base_url),
            data_url=URL(_data_url),
            data_stream='polygon' if USE_POLYGON else 'alpacadatav1')

        conn.on('authenticated')(on_auth)
        conn.on(r'Q.*')(on_quotes)
        conn.on(r'account_updates')(on_account)
        conn.on(r'trade_updates')(on_trade)
        conn.run(channels)


async def get_current_channels():
    # copy to be able to remove closed connections
    subs = dict(subscribers.items())
    result = []
    for sub, chans in subs.items():
        if sub.state == State.CLOSED:
            del subscribers[sub]
        else:
            result.extend(chans)
    result = list(set(result))  # we want the list to be unique
    return result


async def serve(sub, path):
    if USE_POLYGON:
        await sub.send(json.dumps([
            {
                "ev": "status",
                "status": "connected",
                "message": "Connected Successfully"
            }
        ]))
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
                if USE_POLYGON:
                    if data.get("action"):
                        if data.get("action") == "auth":
                            if not _key_id:
                                _key_id = data.get("params")
                    # not really authorized yet.
                    # but sending because it's expected
                    response = json.dumps([
                        {
                            'ev': 'status',
                            'status': 'auth_success',
                            'message': 'authenticated'
                        }
                    ])
                    await sub.send(response)
                else:
                    if data.get("action"):
                        if data.get("action") == "authenticate":
                            if not _key_id:
                                _key_id = data.get("data").get("key_id")
                                _secret_key = data.get("data").get(
                                    "secret_key")
                    # not really authorized yet.
                    # but sending because it's expected
                    response = json.dumps({"data": {"status": "authorized"}})
                    await sub.send(response)
                subscribers[sub] = []

            else:
                if USE_POLYGON:
                    if data.get("action") == "subscribe":
                        new_channels = data.get("params")
                        new_channels = [new_channels] if \
                            isinstance(new_channels, str) else new_channels
                else:
                    if data.get("action") == "listen":
                        new_channels = data.get("data").get("streams")

                # previous_channels = await get_current_channels()
                # if previous_channels:
                #     await conn.unsubscribe(previous_channels)

                subscribers[sub] = new_channels

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


if __name__ == '__main__':
    import logging

    logging.basicConfig(format='%(asctime)s %(name)s %(message)s',
                        level=logging.INFO)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger('websockets').setLevel(logging.INFO)
    # asyncio.gather(a(), b())
    # asyncio.get_event_loop().run_until_complete(a())
    # asyncio.get_event_loop().run_until_complete(b())
    # asyncio.get_event_loop().run_forever()
    #
    start_server = websockets.serve(serve, "0.0.0.0", 8765)

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()

"""
main thread:
- accepts new connections
  - registers the symbols

- thread for alpaca ws. 



"""