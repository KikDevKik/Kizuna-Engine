import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

logger = logging.getLogger(__name__)

# Mock classes to mimic google.genai.types structure
class MockInlineData:
    def __init__(self, data):
        self.data = data

class MockPart:
    def __init__(self, text=None, inline_data=None):
        self.text = text
        self.inline_data = inline_data

class MockModelTurn:
    def __init__(self, parts):
        self.parts = parts

class MockServerContent:
    def __init__(self, model_turn=None, turn_complete=False):
        self.model_turn = model_turn
        self.turn_complete = turn_complete

class MockResponse:
    def __init__(self, server_content=None):
        self.server_content = server_content

class MockSession:
    def __init__(self):
        self._input_queue = asyncio.Queue()
        self._output_queue = asyncio.Queue()

    async def send(self, input, end_of_turn=False):
        # We just consume the input.
        if "data" in input:
            await self._input_queue.put(input["data"])

            # Simple logic: if queue has 5 items, generate response
            # This simulates VAD triggering after some audio is received.
            if self._input_queue.qsize() >= 5:
                # Clear queue to simulate processing consumed audio
                while not self._input_queue.empty():
                    self._input_queue.get_nowait()

                logger.info("Mock: Generating response...")

                # Enqueue responses
                # 1. Text response
                await self._output_queue.put(MockResponse(
                    server_content=MockServerContent(
                        model_turn=MockModelTurn(
                            parts=[MockPart(text="Mock response from Kizuna")]
                        )
                    )
                ))
                # 2. Audio response (simulated silence)
                # Send a few chunks of audio
                for _ in range(5):
                    # dummy audio bytes
                    dummy_audio = b'\x00' * 320
                    await self._output_queue.put(MockResponse(
                        server_content=MockServerContent(
                            model_turn=MockModelTurn(
                                parts=[MockPart(inline_data=MockInlineData(dummy_audio))]
                            )
                        )
                    ))

                # 3. Turn complete
                await self._output_queue.put(MockResponse(
                    server_content=MockServerContent(turn_complete=True)
                ))

    async def receive(self):
        while True:
            response = await self._output_queue.get()
            yield response

class MockGeminiService:
    @staticmethod
    @asynccontextmanager
    async def connect() -> AsyncGenerator[MockSession, None]:
        logger.info("Connecting to MOCK Gemini Service.")
        session = MockSession()
        yield session
        logger.info("Mock Gemini Session closed.")
