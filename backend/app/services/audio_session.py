import asyncio
import base64
import logging
import json
import re
from fastapi import WebSocket, WebSocketDisconnect

from .auction_service import auction_service
from .agent_service import agent_service
from ..models.graph import GraphEdge
from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from ..repositories.base import SoulRepository

# Try importing types for robust multimodal handling
try:
    from google.genai import types
except ImportError:
    types = None

try:
    from websockets.exceptions import ConnectionClosed, ConnectionClosedOK, ConnectionClosedError
except ImportError:
    class ConnectionClosed(Exception): pass
    class ConnectionClosedOK(Exception): pass
    class ConnectionClosedError(Exception): pass

logger = logging.getLogger(__name__)

# 16000 Hz * 2 bytes = 32000 bytes/sec
# 3200 bytes = 100ms
AUDIO_BUFFER_THRESHOLD = 3200

async def send_injections_to_gemini(session, injection_queue: asyncio.Queue):
    """
    Task C: Subconscious -> Gemini
    Injects system hints (text) into the active session without ending the turn.
    """
    try:
        while True:
            try:
                hint_payload = await injection_queue.get()
                text = hint_payload.get("text", "")
                turn_complete = hint_payload.get("turn_complete", False)

                if not text:
                    continue

                logger.info(f"🤫 Whispering to Gemini: {text}")
                system_text = f"[SYSTEM_CONTEXT]: {text}"
                await session.send(input=system_text, end_of_turn=turn_complete)

            except asyncio.CancelledError:
                raise 
            except Exception as e:
                logger.error(f"⚠️ Injection failed (continuing): {e}")
                continue

    except asyncio.CancelledError:
        logger.info("Injection loop cancelled.")
    except Exception as e:
        logger.error(f"CRITICAL: Injection loop died: {e}")
        pass


async def send_to_gemini(websocket: WebSocket, session, transcript_buffer: list[str] | None = None, transcript_queue: asyncio.Queue | None = None):
    """
    Task A: Client -> Gemini
    Reads audio bytes from WebSocket and sends to Gemini session.
    """
    try:
        audio_buffer = bytearray()
        carry_over = bytearray()

        while True:
            message = await websocket.receive()
            data = message.get("bytes")
            text = message.get("text")

            if data:
                # 🏰 BASTION: RMS Energy Gate
                import math
                import struct
                count = len(data) // 2
                if count > 0:
                    sum_sq = 0
                    for i in range(0, len(data), 20): 
                        try:
                            sample = struct.unpack_from('<h', data, i)[0]
                            sum_sq += sample * sample
                        except: break
                    rms = math.sqrt(sum_sq / (count / 10)) if count > 0 else 0
                    
                    if rms > 500: # Threshold for speech
                        await auction_service.interrupt()

                if carry_over:
                    data = carry_over + data
                    carry_over.clear()

                if len(data) % 2 != 0:
                    carry_over.extend(data[-1:])
                    data = data[:-1]

                audio_buffer.extend(data)

                if len(audio_buffer) >= AUDIO_BUFFER_THRESHOLD:
                    await session.send(input={"data": bytes(audio_buffer), "mime_type": "audio/pcm;rate=16000"})
                    audio_buffer.clear()

            elif text:
                try:
                    payload = json.loads(text)
                    if payload.get("type") == "control" and payload.get("action") == "interrupt":
                        logger.info("🛑 SOVEREIGN VOICE: User Interrupted")
                        await auction_service.interrupt()
                        continue

                    if payload.get("type") == "native_transcript":
                        transcript_text = payload.get("text")
                        if transcript_text:
                            # Kill echo if agent is speaking
                            if auction_service._current_winner is not None:
                                continue
                            
                            if transcript_buffer is not None:
                                transcript_buffer.append(f"User: {transcript_text}")
                            if transcript_queue:
                                transcript_queue.put_nowait(transcript_text)
                            continue

                except Exception as e:
                    logger.error(f"Error handling text message: {e}")

    except Exception as e:
        logger.warning(f"Connection dropped in send_to_gemini: {e}")
        raise e

async def receive_from_gemini(
    websocket: WebSocket,
    session,
    transcript_queue: asyncio.Queue | None = None,
    reflection_queue: asyncio.Queue | None = None,
    transcript_buffer: list[str] | None = None,
    agent_name: str = "AI",
    agent_id: Optional[str] = None,
    soul_repo: Optional["SoulRepository"] = None
):
    """
    Task B: Gemini -> Client
    Phase 6.9: Cognitive Silence Architecture.
    """
    try:
        # 🏰 BASTION: Turn-scoped state
        turn_aborted = False
        
        while True:
            try:
                async for response in session.receive():
                    if response.server_content is None:
                        continue

                    server_content = response.server_content
                    model_turn = server_content.model_turn

                    if model_turn:
                        for part in model_turn.parts:
                            if turn_aborted:
                                continue

                            # 1. TOOL HANDLING (Gossip)
                            if part.function_call:
                                fc = part.function_call
                                if fc.name == "spawn_stranger":
                                    try:
                                        name = fc.args.get("name", "Unknown")
                                        relation = fc.args.get("relation", "Associate")
                                        vibe = fc.args.get("vibe", "Mysterious")
                                        new_agent = await agent_service.create_agent(
                                            name=name, role="Stranger",
                                            base_instruction=f"You are {name}, a {relation} of {agent_name}.",
                                            voice_name="Puck", traits={"gossip_spawn": True},
                                            tags=["hollow", "gossip"]
                                        )
                                        if soul_repo and agent_id:
                                            await soul_repo.create_agent(new_agent)
                                            await soul_repo.create_edge(GraphEdge(
                                                source_id=agent_id, target_id=new_agent.id,
                                                type="Gossip_Source", properties={"relation": relation}
                                            ))
                                        await session.send(input={"function_responses": [{"name": "spawn_stranger", "response": {"result": "success", "agent_id": new_agent.id}}]})
                                    except Exception as e:
                                        logger.error(f"Tool Failed: {e}")
                                continue

                            # 2. AUDIO HANDLING (The Vocal Handshake)
                            if part.inline_data:
                                if agent_id:
                                    # Bid for mic
                                    won = await auction_service.bid(agent_id, 1.0)
                                    if not won:
                                        logger.info(f"🔇 {agent_name} lost auction. Aborting TURN.")
                                        turn_aborted = True
                                        continue

                                try:
                                    await websocket.send_bytes(part.inline_data.data)
                                except Exception:
                                    raise WebSocketDisconnect()

                            # 3. TEXT HANDLING (Cognitive Silence)
                            if part.text:
                                text_to_process = part.text
                                
                                # 🏰 BASTION: Aggressive Monologue Filter
                                # If text arrives BEFORE any audio in this turn, it's 99% CoT.
                                # Also filter common CoT markers.
                                if not turn_aborted:
                                    stripped = text_to_process.strip()
                                    is_monologue = any(stripped.startswith(s) for s in ["Okay,", "So,", "I ", "The user", "Thinking:", "Based on"])
                                    if is_monologue or "[THOUGHT]" in stripped or "**" in stripped:
                                        # logger.debug(f"🤫 Filtered Monologue: {stripped[:30]}...")
                                        continue

                                    # Send real dialogue to client
                                    if transcript_buffer is not None:
                                        transcript_buffer.append(f"{agent_name}: {stripped}")
                                    
                                    try:
                                        await websocket.send_json({"type": "text", "data": stripped})
                                    except Exception:
                                        raise WebSocketDisconnect()

                                    if reflection_queue:
                                        reflection_queue.put_nowait(stripped)

                    if server_content.turn_complete:
                        # Reset turn state
                        turn_aborted = False
                        if agent_id:
                            await auction_service.release(agent_id)
                        try:
                            await websocket.send_json({"type": "turn_complete"})
                        except: pass

            except (WebSocketDisconnect, ConnectionClosed) as e:
                raise e
            except Exception as e:
                logger.error(f"Loop Error: {e}")
                raise e

    except Exception as e:
        logger.error(f"Fatal Session Error: {e}")
        raise e
