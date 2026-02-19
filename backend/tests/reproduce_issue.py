import asyncio
import websockets
import json
import logging
import sys
import math
import struct

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

WS_URL = "ws://localhost:8000/ws/live"

def generate_sine_wave(duration_sec, frequency=440, sample_rate=16000):
    """Generates a mono 16-bit PCM sine wave."""
    num_samples = int(duration_sec * sample_rate)
    audio_data = bytearray()
    for i in range(num_samples):
        # Calculate sample value
        t = float(i) / sample_rate
        value = int(32767.0 * math.sin(2.0 * math.pi * frequency * t))
        # Pack as little-endian 16-bit integer
        audio_data.extend(struct.pack('<h', value))
    return audio_data

async def test_multi_turn():
    logger.info(f"Connecting to {WS_URL}...")
    try:
        async with websockets.connect(WS_URL) as ws:
            logger.info("Connected!")

            # Generate 3 seconds of audio (should be enough to trigger VAD)
            # 3 sec * 32000 bytes/sec = 96000 bytes
            audio_data = generate_sine_wave(3.0)
            chunk_size = 3200 # 100ms chunks

            # --- Turn 1 ---
            logger.info("--- Starting Turn 1 ---")
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i+chunk_size]
                await ws.send(chunk)
                await asyncio.sleep(0.1) # Simulate real-time sending

            logger.info("Sent audio for Turn 1.")

            # Wait for response
            turn_complete = False
            while not turn_complete:
                try:
                    message = await asyncio.wait_for(ws.recv(), timeout=15.0)
                    try:
                        data = json.loads(message)
                        # logger.info(f"Received: {data.get('type')}")
                        if data.get('type') == 'turn_complete':
                            turn_complete = True
                            logger.info("Turn 1 Complete!")
                            break
                        elif data.get('type') == 'text':
                             logger.info(f"Received Text: {data.get('data')}")
                    except json.JSONDecodeError:
                        pass
                except asyncio.TimeoutError:
                    logger.error("Timeout waiting for Turn 1 response!")
                    return False

            # --- Turn 2 ---
            logger.info("--- Starting Turn 2 ---")
            await asyncio.sleep(1) # Small pause before speaking again

            # Send audio again
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i+chunk_size]
                await ws.send(chunk)
                await asyncio.sleep(0.1)
            logger.info("Sent audio for Turn 2.")

            # Wait for response
            turn_complete = False
            while not turn_complete:
                try:
                    message = await asyncio.wait_for(ws.recv(), timeout=15.0)
                    try:
                        data = json.loads(message)
                        # logger.info(f"Received: {data.get('type')}")
                        if data.get('type') == 'turn_complete':
                            turn_complete = True
                            logger.info("Turn 2 Complete!")
                            break
                        elif data.get('type') == 'text':
                             logger.info(f"Received Text: {data.get('data')}")
                    except json.JSONDecodeError:
                        pass
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
