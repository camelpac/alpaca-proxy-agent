#!/usr/bin/env python

# WS client example

import asyncio
import json

cred = json.load(open(".env"))


import websockets

async def register():
    uri = "ws://localhost:8765/test"
    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({
            'action': 'authenticate',
            'data':   {
                'key_id':     cred['key_id'],
                'secret_key': cred['secret_key'],
            }
        }))

        response = json.loads(await ws.recv())
        print(response)

        await ws.send(json.dumps({
            'action': 'listen',
            'data':   {
                'streams': ["alpacadatav1/Q.AAPL"],
            }
        }))

        get_aapl = False
        while 1:
            try:
                response = await ws.recv()
                print(json.loads(response))
                await ws.send(json.dumps({
                    'action': 'listen',
                    'data':   {
                        'streams': ["alpacadatav1/Q.{}".format("AA" if get_aapl
                                                               else "TSLA")],
                    }
                }))
                get_aapl = not get_aapl
            except Exception as e:
                print(e)
            await asyncio.sleep(0.5)

        # await ws.close()

import logging
logger = logging.getLogger('websockets')
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())
loop = asyncio.get_event_loop()
loop.set_debug(True)
asyncio.get_event_loop().run_until_complete(register())
asyncio.get_event_loop().run_forever()