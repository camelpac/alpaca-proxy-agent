#!/usr/bin/env python

import os
import asyncio
import json
from enum import Enum

import websockets
import queue
import threading
import alpaca_trade_api as tradeapi
from alpaca_trade_api.common import URL
from alpaca_trade_api.entity import quote_mapping, agg_mapping, trade_mapping
from alpaca_trade_api.polygon.entity import quote_mapping as \
    polygon_quote_mapping, agg_mapping as polygon_aggs_mapping, \
    trade_mapping as polygon_trade_mapping
from websockets.protocol import State

from version import VERSION
from asciiart import ascii_art
from threading import Lock

lock = Lock()

subscribers = {}
q_mapping = {}
register_queue = queue.Queue()
response_queue = queue.Queue()
reverse_qoute_mapping = {v: k for k, v in quote_mapping.items()}
reverse_polygon_qoute_mapping = {
    v: k for k, v in polygon_quote_mapping.items()
}

reverse_trade_mapping = {v: k for k, v in trade_mapping.items()}
reverse_polygon_trade_mapping = {
    v: k for k, v in polygon_trade_mapping.items()
}

reverse_minute_agg_mapping = {v: k for k, v in agg_mapping.items()}
reverse_polygon_aggs_mapping = {
    v: k for k, v in polygon_aggs_mapping.items()
}

conn: tradeapi.StreamConn = None
_key_id = None
_secret_key = None
_authenticated = False
_base_url = "https://paper-api.alpaca.markets"
USE_POLYGON = True if os.environ.get("USE_POLYGON") == 'true' else False

_data_url = "https://data.alpaca.markets"
QUOTE_PREFIX = "Q." if USE_POLYGON else "alpacadatav1/Q."
TRADE_PREFIX = "T." if USE_POLYGON else "alpacadatav1/T."
# MINUTE_AGG_PREFIX = "AM." if USE_POLYGON else "alpacadatav1/AM."
MINUTE_AGG_PREFIX = "AM."
SECOND_AGG_PREFIX = "A."


class MessageType(Enum):
    Quote = 1
    MinuteAgg = 2
    SecondAgg = 3  # only with polygon
    Trade = 4


async def on_auth(conn, stream, msg):
    pass


async def on_account(conn, stream, msg):
    q_mapping[msg.symbol].put(msg)


async def listen(conn, channel, msg):
    if hasattr(msg, 'error'):
        print('listening error', msg.error)

async def on_message(conn, subject, msg):
    def _restructure_original_msg(m, _type: MessageType):
        """
        the sdk translate the message received from the server to a more
        readable format. so this is how we get it (readable). but when we pass
        it to the clients using this proxy, the clients expects the message to
        be not readable (or, server compact), and tries to translate it to
        readable format. so this method converts it back to the expected format
        :param m:
        :return:
        """
        def _get_correct_mapping():
            """
            we may handle different message types (aggs, quotes, trades)
            this method decide what reverese mapping to use
            :return:
            """
            if _type == MessageType.Quote:
                stream = 'Q' if USE_POLYGON else f"Q.{m.symbol}"
                _mapping = reverse_polygon_qoute_mapping if USE_POLYGON else \
                    reverse_qoute_mapping
            elif _type == MessageType.Trade:
                stream = 'T' if USE_POLYGON else f"T.{m.symbol}"
                _mapping = reverse_polygon_trade_mapping if USE_POLYGON else \
                    reverse_trade_mapping
            elif _type == MessageType.MinuteAgg:
                stream = 'AM' if USE_POLYGON else f"AM.{m.symbol}"
                _mapping = reverse_polygon_aggs_mapping if USE_POLYGON else \
                    reverse_minute_agg_mapping
            elif _type == MessageType.SecondAgg:
                # only supported in polygon
                stream = 'A'
                _mapping = reverse_polygon_aggs_mapping
            return stream, _mapping

        stream, _mapping = _get_correct_mapping()

        def _construct_message():
            """
            polygon and alpaca message structure is different
            :return:
            """
            if USE_POLYGON:
                data = {_mapping[k]: v for
                        k, v in m._raw.items() if
                        k in _mapping}
                data['ev'] = stream
                data['sym'] = m.symbol
                message = [data]
            else:
                message = {
                    'stream': stream,
                    'data': {_mapping[k]: v for k, v in
                             m._raw.items() if k in _mapping}
                }
            return message

        return _construct_message()

    # msg._raw['time'] = msg.timestamp.to_pydatetime().timestamp()

    # copy subscribers list to be able to remove closed connections or
    # add new ones
    subs = dict(subscribers.items())

    # iterate channels and distribute the message to correct subscribers
    for sub, channels in subs.items():
        if QUOTE_PREFIX + msg.symbol in channels:
            restructured = _restructure_original_msg(msg,
                                                     MessageType.Quote)
        elif TRADE_PREFIX + msg.symbol in channels:
            restructured = _restructure_original_msg(msg,
                                                     MessageType.Trade)
        elif MINUTE_AGG_PREFIX + msg.symbol in channels:
            restructured = _restructure_original_msg(msg,
                                                     MessageType.MinuteAgg)
        elif SECOND_AGG_PREFIX + msg.symbol in channels:
            restructured = _restructure_original_msg(msg,
                                                     MessageType.SecondAgg)

        if sub.state != State.CLOSED:
            await sub.send(json.dumps(restructured))
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
        conn.on(r'Q.*')(on_message)
        conn.on(r'T.*')(on_message)

        conn.on(r'listening')(listen)


        if USE_POLYGON:
            conn.on(r'A.*')(on_message)
        conn.on(r'AM.*')(on_message)
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
                        new_channels = data.get("params").split(",")
                else:
                    if data.get("action") == "listen":
                        new_channels = data.get("data").get("streams")

                # previous_channels = await get_current_channels()
                # if previous_channels:
                #     await conn.unsubscribe(previous_channels)

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


if __name__ == '__main__':
    import logging

    logging.basicConfig(format='%(asctime)s %(name)s %(message)s',
                        level=logging.INFO)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger('websockets').setLevel(logging.INFO)

    #
    print(ascii_art)
    logging.info(f"Alpaca Proxy Agent v{VERSION}")
    logging.info(f"Using the {'Polygon' if USE_POLYGON else 'Alpaca'} "
                 f"Websocket")
    start_server = websockets.serve(serve, "0.0.0.0", 8765)

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
