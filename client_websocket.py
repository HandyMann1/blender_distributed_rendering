import asyncio
import websockets
from time import sleep

async def connect_to_server():
    async with websockets.connect("ws://127.0.0.1:5000/ws") as websocket:
        while True:
            response = await websocket.recv()


asyncio.get_event_loop().run_until_complete(connect_to_server())
