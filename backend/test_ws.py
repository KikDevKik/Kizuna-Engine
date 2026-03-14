import asyncio
import websockets

async def test_ws():
    uri = 'ws://127.0.0.1:8000/ws/live?agent_id=kizuna&lang=en'
    print(f'Connecting to {uri}...')
    try:
        async with websockets.connect(uri) as websocket:
            print('Connected!')
            while True:
                msg = await websocket.recv()
                print(f'Received: {msg}')
    except Exception as e:
        print(f'Connection failed: {e}')

asyncio.run(test_ws())
