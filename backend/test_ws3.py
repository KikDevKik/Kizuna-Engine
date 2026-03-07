import asyncio
from websockets.asyncio.client import connect

async def test_ws():
    try:
        print('Connecting...')
        async with connect('ws://127.0.0.1:8000/ws/live?agent_id=kizuna&lang=en') as websocket:
            print('Connected!')
            try:
                msg = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                print(f'Received 1: {msg}')
            except asyncio.TimeoutError:
                print('Timeout waiting for message.')
            except Exception as e:
                 print(f"recv error: {e}")
            await asyncio.sleep(2)
            
    except Exception as e:
        print(f'Connection failed: {e}')

asyncio.run(test_ws())
