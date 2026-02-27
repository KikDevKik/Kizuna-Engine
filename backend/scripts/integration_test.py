import asyncio
import websockets
import sqlite3
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestClient")

DB_PATH = Path(__file__).resolve().parent.parent / "kizuna_graph.db"

async def test_kizuna():
    # 1. Fetch Agent ID
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM nodes WHERE label='AgentNode' LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        logger.error("No agents found in DB.")
        return
        
    agent_id = row[0]
    logger.info(f"Using Agent ID: {agent_id}")
    
    uri = f"ws://localhost:8000/ws/live?agent_id={agent_id}&lang=es"
    
    logger.info("Connecting to Kizuna Engine...")
    try:
        async with websockets.connect(uri, extra_headers={"Origin": "http://localhost:5173"}) as websocket:
            logger.info("Connected successfully.")
            
            # Send initial greeting
            test_msg = {"type": "native_transcript", "text": "Hola, ¿puedes escucharme?"}
            await websocket.send(json.dumps(test_msg))
            logger.info("Sent native transcript.")
            
            # Send mock audio data (silence) to trigger processing if needed
            # Or just wait for response
            try:
                async with asyncio.timeout(15.0):
                    while True:
                        msg = await websocket.recv()
                        if isinstance(msg, bytes):
                            logger.info(f"Received Audio: {len(msg)} bytes")
                        else:
                            data = json.loads(msg)
                            logger.info(f"Received JSON: {data}")
            except asyncio.TimeoutError:
                logger.info("Test timeout reached (expected if no audio response yet).")
    except Exception as e:
        logger.error(f"WebSocket test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_kizuna())
