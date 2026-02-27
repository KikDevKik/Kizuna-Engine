import asyncio
import os
import logging
from dotenv import load_dotenv
from pathlib import Path
from google import genai
from google.genai import types

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load Environment
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    logger.error("No API key found in .env")
    exit(1)

client = genai.Client(api_key=API_KEY)

async def test_text_injection():
    config = types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        system_instruction=types.Content(parts=[types.Part.from_text(text="You are a helpful test bot. Speak in a robotic voice if possible, but you must reply out loud.")])
    )

    logger.info("Connecting to Gemini Live...")
    try:
        async with client.aio.live.connect(
            model="gemini-2.5-flash-native-audio-preview-12-2025",
            config=config
        ) as session:
            logger.info("Connected.")
            
            # FORMAT 2: Using the proper types.Part object (The Bastion Hypothesis)
            test_prompt = "Hello. I am the user. Please reply to this exact sentence with a spoken greeting."
            logger.info(f"Sending Format 2: types.Part -> {test_prompt}")
            
            # The core test: Does the SDK accept a Part object?
            
            payload = types.Part.from_text(text=test_prompt)
            logger.info("Attempting to send as types.Part...")
            
            # Wait for setupComplete (simulate normal flow)
            async for response in session.receive():
                if response.server_content is None:
                     logger.info("Setup complete received.")
                     break
            
            # We send the text. We must use end_of_turn=True to force a response.
            try:
                await session.send(input=payload, end_of_turn=True)
                logger.info("Payload sent successfully without SDK crash.")
            except Exception as e:
                logger.error(f"SDK Rejected format: {e}")
                return

            logger.info("Waiting for audio response...")
            async for response in session.receive():
                if response.server_content and response.server_content.model_turn:
                    for part in response.server_content.model_turn.parts:
                        if part.inline_data:
                            logger.info("✅ SUCCESS! Audio bytes received from text injection.")
                            return
                        if part.text:
                            logger.info(f"Received Text: {part.text}")
                if response.server_content and response.server_content.turn_complete:
                    logger.info("Turn Complete. Did we get audio?")
                    break

                    
    except Exception as e:
         logger.error(f"Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_text_injection())
