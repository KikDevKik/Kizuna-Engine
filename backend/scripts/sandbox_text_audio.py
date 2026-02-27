import asyncio
import os
import logging
from dotenv import load_dotenv
from pathlib import Path
from google import genai
from google.genai import types

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)

async def test_live_text():
    config = types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        system_instruction=types.Content(parts=[types.Part.from_text(text="You are a test bot. Respond to text by speaking out loud.")])
    )

    logger.info("Connecting...")
    async with client.aio.live.connect(model="gemini-2.5-flash-native-audio-preview-12-2025", config=config) as session:
        logger.info("Connected.")
        
        async def receive_loop():
            async for response in session.receive():
                if response.setup_complete:
                    logger.info("Server: setupComplete")
                elif response.server_content and response.server_content.model_turn:
                    for part in response.server_content.model_turn.parts:
                        if part.text:
                            logger.info(f"Server Text: {part.text}")
                        if part.inline_data:
                            logger.info(f"Server Audio: {len(part.inline_data.data)} bytes")
                elif response.server_content and response.server_content.turn_complete:
                    logger.info("Server: turnComplete")
        
        async def send_loop():
            await asyncio.sleep(2) # wait for setup
            
            logger.info("Sending prompt as plain string...")
            await session.send(input="Please say 'Hello World' out loud.", end_of_turn=True)
            logger.info("Sent.")
            
            await asyncio.sleep(5)
            
            logger.info("Sending prompt as Part object...")
            await session.send(input=types.Part.from_text(text="Please say 'Test 2' out loud."), end_of_turn=True)
            logger.info("Sent.")
            
            await asyncio.sleep(10)
            
        await asyncio.gather(receive_loop(), send_loop())

if __name__ == "__main__":
    asyncio.run(test_live_text())
