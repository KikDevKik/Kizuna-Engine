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

async def test_formats():
    config = types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        system_instruction=types.Content(parts=[types.Part.from_text(text="You are a test bot. Say 'Format Accepted' out loud.")])
    )

    logger.info("Connecting to Gemini Live...")
    try:
        async with client.aio.live.connect(
            model="gemini-2.5-flash-native-audio-preview-12-2025",
            config=config
        ) as session:
            logger.info("Connected. Waiting for setupComplete...")
            
            async for response in session.receive():
                if response.server_content is None:
                     logger.info("Setup complete received.")
                     break
            
            logger.info("TESTING FORMAT: String")
            try:
                await session.send(input="Hello. Say 'String Accepted' out loud.", end_of_turn=True)
                logger.info("String format sent successfully.")
            except Exception as e:
                logger.error(f"String rejected: {e}")

            logger.info("Waiting for response...")
            try:
                async with asyncio.timeout(5.0):
                    async for response in session.receive():
                        if response.server_content and response.server_content.model_turn:
                            for part in response.server_content.model_turn.parts:
                                if part.inline_data:
                                    logger.info("✅ SUCCESS! Audio received for String format.")
                                    return
                                if part.text:
                                    logger.info(f"Received Text: {part.text}")
                        if response.server_content and response.server_content.turn_complete:
                            logger.info("Turn Complete.")
                            break
            except asyncio.TimeoutError:
                logger.warning("Timeout waiting for response to String.")

            logger.info("TESTING FORMAT: dict with 'text' key")
            try:
                await session.send(input={"text": "Hello. Say 'Dict Accepted' out loud."}, end_of_turn=True)
                logger.info("Dict format sent successfully.")
            except Exception as e:
                logger.error(f"Dict rejected: {e}")

            logger.info("Waiting for response...")
            try:
                async with asyncio.timeout(5.0):
                    async for response in session.receive():
                        if response.server_content and response.server_content.model_turn:
                            for part in response.server_content.model_turn.parts:
                                if part.inline_data:
                                    logger.info("✅ SUCCESS! Audio received for Dict format.")
                                    return
                                if part.text:
                                    logger.info(f"Received Text: {part.text}")
                        if response.server_content and response.server_content.turn_complete:
                            logger.info("Turn Complete.")
                            break
            except asyncio.TimeoutError:
                logger.warning("Timeout waiting for response to Dict.")

    except Exception as e:
         logger.error(f"Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_formats())
