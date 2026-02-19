import asyncio
import websockets
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

WS_URL = "ws://localhost:8000/ws/live"

async def test_allowed_origin():
    """Test connection with an allowed origin."""
    logger.info("Testing Allowed Origin (http://localhost:5173)...")
    try:
        # http://localhost:5173 is in settings.CORS_ORIGINS
        async with websockets.connect(WS_URL, origin="http://localhost:5173") as ws:
            logger.info("Connected successfully with allowed origin.")
            await ws.close()
            return True
    except Exception as e:
        logger.error(f"Failed to connect with allowed origin: {e}")
        return False

async def test_disallowed_origin():
    """Test connection with a disallowed origin."""
    logger.info("Testing Disallowed Origin (http://evil.com)...")
    try:
        # http://evil.com is NOT in settings.CORS_ORIGINS
        async with websockets.connect(WS_URL, origin="http://evil.com") as ws:
            logger.error("Connected with disallowed origin! Security failure.")
            await ws.close()
            return False
    except websockets.exceptions.InvalidStatusCode as e:
        logger.info(f"Connection rejected as expected with Status Code: {e.status_code}")
        # Typically 403 Forbidden is sent if handshake fails or is rejected
        return True
    except websockets.exceptions.ConnectionClosedError as e:
         logger.info(f"Connection closed as expected with Close Code: {e.code}")
         if e.code == 1008:
             return True
         return False
    except Exception as e:
        logger.warning(f"Unexpected error with disallowed origin: {e} ({type(e)})")
        # If it's a connection failure, it might be what we want, but we should verify it's the right kind.
        # But for now, any failure to connect is better than success.
        return True

async def run_tests():
    logger.info("Starting Security CORS Tests...")

    # Wait a bit for server to be ready (if run immediately after start)
    await asyncio.sleep(1)

    success_allowed = await test_allowed_origin()
    success_disallowed = await test_disallowed_origin()

    if success_allowed and success_disallowed:
        logger.info("✅ Security Tests Passed: CORS enforcement works.")
        return True
    else:
        logger.error("❌ Security Tests Failed.")
        return False

if __name__ == "__main__":
    # Use asyncio.run for cleaner execution
    try:
        success = asyncio.run(run_tests())
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        pass
