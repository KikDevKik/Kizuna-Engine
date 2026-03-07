import asyncio
from websockets.sync.client import connect

def test_ws():
    try:
        with connect('ws://127.0.0.1:8000/ws/live?agent_id=kizuna&lang=en') as websocket:
            print('Connected!')
            msg = websocket.recv()
            print(f'Received: {msg}')
    except Exception as e:
        print(f'Connection failed: {e}')

test_ws()
