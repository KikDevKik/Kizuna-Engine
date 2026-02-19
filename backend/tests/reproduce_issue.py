import asyncio
import websockets
import json
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

WS_URL = "ws://localhost:8000/ws/live"

async def test_multi_turn():
    logger.info(f"Connecting to {WS_URL}...")
    try:
        async with websockets.connect(WS_URL) as ws:
            logger.info("Connected!")

            # Turn 1
            logger.info("--- Starting Turn 1 ---")
            # Send simulated audio (a few chunks)
            for i in range(10):
                # 320 bytes (10ms of 16kHz mono 16-bit PCM)
                audio_chunk = b'\x00' * 320
                await ws.send(audio_chunk)
                await asyncio.sleep(0.01)

            logger.info("Sent audio for Turn 1.")

            # Wait for response
            turn_complete = False
            start_time = asyncio.get_event_loop().time()
            while not turn_complete:
                try:
                    message = await asyncio.wait_for(ws.recv(), timeout=10.0)
                    try:
                        data = json.loads(message)
                        logger.info(f"Received: {data.get('type')}")
                        if data.get('type') == 'turn_complete':
                            turn_complete = True
                            logger.info("Turn 1 Complete!")
                            break # Explicit break
                    except json.JSONDecodeError:
                        logger.warning(f"Received non-JSON message: {message}")
                except asyncio.TimeoutError:
                    logger.error("Timeout waiting for Turn 1 response!")
                    return False

            # Turn 2
            logger.info("--- Starting Turn 2 ---")
            # Send simulated audio again
            for i in range(10):
                audio_chunk = b'\x00' * 320
                await ws.send(audio_chunk)
                await asyncio.sleep(0.01)
            logger.info("Sent audio for Turn 2.")

            # Wait for response
            turn_complete = False
            while not turn_complete:
                try:
                    message = await asyncio.wait_for(ws.recv(), timeout=10.0)
                    try:
                        data = json.loads(message)
                        logger.info(f"Received: {data.get('type')}")
                        if data.get('type') == 'turn_complete':
                            turn_complete = True
                            logger.info("Turn 2 Complete!")
                            break
                    except json.JSONDecodeError:
                        logger.warning(f"Received non-JSON message: {message}")
                except asyncio.TimeoutError:
                    logger.error("Timeout waiting for Turn 2 response!")
                    return False

            logger.info("Test Passed: Multiple turns successful.")
            return True

    except Exception as e:
        logger.error(f"Test Failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_multi_turn())
    if not success:
        sys.exit(1)
