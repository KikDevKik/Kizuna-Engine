import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
import json

logger = logging.getLogger(__name__)

class MockInlineData:
    def __init__(self, data):
        self.data = data

class MockFunctionCall:
    def __init__(self, name, args):
        self.name = name
        self.args = args

class MockPart:
    def __init__(self, text=None, inline_data=None, function_call=None):
        self.text = text
        self.inline_data = inline_data
        self.function_call = function_call

class MockModelTurn:
    def __init__(self, parts):
        self.parts = parts

class MockServerContent:
    def __init__(self, model_turn=None, turn_complete=False):
        self.model_turn = model_turn
        self.turn_complete = turn_complete

class MockResponse:
    def __init__(self, server_content=None, text=None):
        self.server_content = server_content
        self.text = text

class MockSession:
    def __init__(self):
        self._input_queue = asyncio.Queue()
        self._output_queue = asyncio.Queue()
        self._received_bytes = 0

    async def send_realtime_input(self, audio=None, video=None, audio_stream_end=False):
        if video is not None:
            logger.debug(f"Mock: Vision frame received ({len(video.data) if hasattr(video, 'data') else '?'} bytes) — ignored in mock")
            return

        if audio is not None and hasattr(audio, 'data'):
            input = {"data": audio.data}
        else:
            return

        if isinstance(input, dict) and "data" in input:
            data = input["data"]
            await self._input_queue.put(data)
            self._received_bytes += len(data)

            if self._received_bytes >= 1600:
                while not self._input_queue.empty():
                    self._input_queue.get_nowait()
                self._received_bytes = 0

                logger.info("Mock: Generating response...")

                await self._output_queue.put(MockResponse(
                    server_content=MockServerContent(
                        model_turn=MockModelTurn(
                            parts=[MockPart(text="Mock response from Kizuna")]
                        )
                    )
                ))
                for _ in range(5):
                    dummy_audio = b'\x00' * 320
                    await self._output_queue.put(MockResponse(
                        server_content=MockServerContent(
                            model_turn=MockModelTurn(
                                parts=[MockPart(inline_data=MockInlineData(dummy_audio))]
                            )
                        )
                    ))
                await self._output_queue.put(MockResponse(
                    server_content=MockServerContent(turn_complete=True)
                ))
        elif isinstance(input, str) or (isinstance(input, dict) and "text" in input):
            logger.info(f"Mock received text input: {input}")
            pass

    async def receive(self):
        while True:
            response = await self._output_queue.get()
            yield response

class MockAioModels:
    async def generate_content(self, model, contents, config=None):
        logger.info(f"Mocking generate_content for model: {model}")
        content_str = str(contents)

        if "You are designing one location within District Zero" in content_str:
            mock_loc = {
                "name": f"Mock Location {hash(content_str) % 1000}",
                "type": "practical_mundane",
                "description": "A mocked procedural location generated during testing.",
                "atmosphere": "Mundane but slightly off",
                "who_comes_here": "Developers and testers",
                "what_happens_here": "Verification of code functionality",
                "district_zero_rules_posted": "Do not break the build.",
                "a_secret": "It's all 1s and 0s."
            }
            return MockResponse(text=json.dumps(mock_loc))

        # Assume hollow agent prompt otherwise
        mock_profile = {
            "name": f"Mock Stranger {hash(content_str) % 1000}",
            "base_instruction": "A mocked procedural backstory for testing.",
            "interiority": {},
            "daily_life_in_district_zero": "I wander around mocked components.",
            "emotional_resonance_matrix": {},
            "voice_name": "Puck",
            "traits": {"curiosity": "high", "patience": "low"},
            "base_tolerance": 50,
            "identity_anchors": ["Mock anchor 1", "Mock anchor 2"],
            "forbidden_secret": "I am not real.",
            "neural_signature": {
                "weights": {"volatility": 0.5, "hostility": 0.1, "curiosity": 0.9, "empathy": 0.5},
                "narrative": {"core_conflict": "None"}
            },
            "false_memories": [
                {"memory_text": "I remember being instantiated.", "importance": 0.9, "emotional_valence": "neutral"}
            ],
            "native_language": "English",
            "known_languages": ["English"]
        }
        return MockResponse(text=json.dumps(mock_profile))

class MockAioClient:
    def __init__(self):
        self.models = MockAioModels()

class MockClient:
    def __init__(self):
        self.aio = MockAioClient()

class MockGeminiService:
    def __init__(self):
        self.aio = MockAioClient()
        self.client = MockClient()

    @staticmethod
    @asynccontextmanager
    async def connect(system_instruction: str = None, voice_name: str = None) -> AsyncGenerator[MockSession, None]:
        logger.info(f"Connecting to MOCK Gemini Service with instruction len: {len(system_instruction) if system_instruction else 0} (Voice: {voice_name})")
        session = MockSession()
        yield session
        logger.info("Mock Gemini Session closed.")
