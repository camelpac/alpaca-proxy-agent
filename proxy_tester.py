#!/usr/bin/env python

# WS client example

import asyncio
import json

cred = json.load(open(".env"))


import websockets

async def register():
    uri = "ws://localhost:8765/test"
    ws = await websockets.connect(uri)

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
            response = (await ws.recv())
            print(json.loads(response))
            await ws.send(json.dumps({
                'action': 'listen',
                'data':   {
                    'streams': ["alpacadatav1/Q.{}".format("AA" if get_aapl else "TSLA")],
                }
            }))
            get_aapl = not get_aapl
        except Exception as e:
            print(e)
        await asyncio.sleep(1)

    # await ws.close()

asyncio.get_event_loop().run_until_complete(register())
asyncio.get_event_loop().run_forever()