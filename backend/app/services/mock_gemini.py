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
        self._received_bytes = 0

    async def send(self, input, end_of_turn=False):
        # We just consume the input.
        if "data" in input:
            data = input["data"]
            await self._input_queue.put(data)
            self._received_bytes += len(data)

            # Simulate VAD: trigger after ~1000 bytes received (Mock threshold)
            # Previously was 5 items * 320 = 1600 bytes.
            if self._received_bytes >= 1600:
                # Clear queue/counter to simulate processing consumed audio
                while not self._input_queue.empty():
                    self._input_queue.get_nowait()
                self._received_bytes = 0

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
    async def connect(system_instruction: str = None, voice_name: str = None) -> AsyncGenerator[MockSession, None]:
        logger.info(f"Connecting to MOCK Gemini Service with instruction len: {len(system_instruction) if system_instruction else 0} (Voice: {voice_name})")
        session = MockSession()
        yield session
        logger.info("Mock Gemini Session closed.")
