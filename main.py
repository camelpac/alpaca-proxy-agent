#!/usr/bin/env python
import os

import nest_asyncio

nest_asyncio.apply()
import asyncio
from collections import defaultdict

import msgpack

import websockets
import threading
import alpaca_trade_api as tradeapi
from alpaca_trade_api.common import URL
from websockets.protocol import State

from server_message_handler import on_message
from shared_memory_obj import subscribers, response_queue
from version import VERSION
from asciiart import ascii_art
from threading import Lock

lock = Lock()

conn: tradeapi.Stream = None
_key_id = None
_secret_key = None
_authenticated = False
_base_url = "https://paper-api.alpaca.markets"
_pro_subscription = 'sip' if os.getenv("IS_PRO").lower() == 'true' else 'iex'
CONSUMER_STARTED = False


def consumer_thread(channels):
    try:
        # make sure we have an event loop, if not create a new one
        loop = asyncio.get_event_loop()
        # loop.set_debug(True)
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())

    global conn
    if not conn:
        conn = tradeapi.Stream(_key_id,
                               _secret_key,
                               base_url=URL(_base_url),
                               data_feed=_pro_subscription,
                               raw_data=True)
        subscribe(channels)
        conn.run()


def subscribe(channels):
    logging.info(f"Subscribing to: {channels}")
    conn.subscribe_trades(on_message, *channels['trades'])
    conn.subscribe_quotes(on_message, *channels['quotes'])
    conn.subscribe_bars(on_message, *channels['bars'])
    conn.subscribe_statuses(on_message, *channels['statuses'])
    conn.subscribe_daily_bars(on_message, *channels['dailyBars'])


def unsubscribe(channels):
    logging.info(f"Unsubscribing from: {channels}")
    try:
        conn.unsubscribe_trades(*channels['trades'])
        conn.unsubscribe_quotes(*channels['quotes'])
        conn.unsubscribe_bars(*channels['bars'])
        conn.unsubscribe_statuses(*channels['statuses'])
        conn.unsubscribe_daily_bars(*channels['dailyBars'])
    except Exception as e:
        logging.warning(f"error unsubscribing from {channels}. {e}")


def get_current_channels():
    result = defaultdict(set)
    for sub, chans in subscribers.items():
        if chans:
            for _type in chans:
                result[_type].update(set(chans[_type]))
    return result


def clear_dead_subscribers():
    # copy to be able to remove closed connections
    subs = dict(subscribers.items())
    for sub, chans in subs.items():
        if sub.state == State.CLOSED:
            del subscribers[sub]


async def serve(sub, path):
    connected = [{"T": "success", "msg": "connected"}]
    await sub.send(msgpack.packb(connected, use_bin_type=True))
    global conn, _key_id, _secret_key
    global CONSUMER_STARTED
    try:
        async for msg in sub:
            # msg = await sub.recv()
            try:
                data = msgpack.unpackb(msg)
                # print(f"< {data}")
            except Exception as e:
                print(e)

            if sub not in subscribers.keys():
                if data.get("action"):
                    if data.get("action") == "auth":
                        if not _key_id:
                            _key_id = data.get("key")
                            _secret_key = data.get("secret")
                # not really authorized yet.
                # but sending because it's expected
                authenticated = [{"T": "success", "msg": "authenticated"}]
                await sub.send(msgpack.packb(authenticated,
                                             use_bin_type=True))
                subscribers[sub] = defaultdict(list)

            else:
                new_channels = {}
                if data.get("action") == "subscribe":
                    data.pop("action")
                    new_channels = data
                else:
                    raise Exception("Got here")

                previous_channels = get_current_channels()
                if previous_channels:
                    # it is easier to first unsubscribe from previous channels
                    # and then subscribe again. this way we make sure we clean
                    # dead connections.
                    unsubscribe(previous_channels)
                    clear_dead_subscribers()
                for _type in new_channels:
                    subscribers[sub][_type].extend(new_channels[_type])
                    subscribers[sub][_type] = list(
                        set(subscribers[sub][_type]))
                with lock:
                    if not CONSUMER_STARTED:
                        CONSUMER_STARTED = True
                        threading.Thread(target=consumer_thread,
                                         args=(new_channels,)).start()
                    else:
                        channels = get_current_channels()
                        subscribe(channels)
    except Exception as e:
        # traceback.print_exc()
        print(e)
        # we clean up subscriptions upon disconnection and subscribe again
        # for still active clients
        current = get_current_channels()
        clear_dead_subscribers()
        unsubscribe(current)
        current = get_current_channels()
        if current:
            subscribe(current)

    print("Done")


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
            # print(f"send {response['response']}")
            await response["subscriber"].send(
                msgpack.packb([response["response"]]))
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
    logging.info("Using the Alpaca Websocket")
    if os.getenv("IS_LIVE"):
        logging.info("Connecting to the real account endpoint")
    else:
        logging.info("Connecting to the paper account endpoint")
    if _pro_subscription == 'sip':
        logging.info("Using the pro-subscription plan(sip)")
    else:
        logging.info("Using the free subscription plan(iex)")
    start_server = websockets.serve(serve, "0.0.0.0", 8765)

    asyncio.get_event_loop().run_until_complete(asyncio.gather(
        start_server,
        send_response_to_client(),
        return_exceptions=True,
    ))
    asyncio.get_event_loop().run_forever()
