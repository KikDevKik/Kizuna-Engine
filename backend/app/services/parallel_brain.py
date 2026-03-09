import asyncio
import logging
import re
from datetime import datetime
from asyncio import Queue

logger = logging.getLogger(__name__)

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None

from core.config import settings

class ParallelBrain:
    """
    Canal 2 — El Lóbulo Frontal.
    Worker asíncrono que analiza transcripciones en background
    y ejecuta búsquedas web sin tocar el pipeline de audio del Canal 1.
    Cuando encuentra algo relevante, señaliza al SessionManager
    para ejecutar una Micro-Reconexión Sincronizada.
    """

    def __init__(self):
        self.client = None
        if genai and settings.GEMINI_API_KEY:
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    async def start(
        self,
        transcript_queue: Queue,
        reconnect_queue: Queue,
        user_id: str,
        agent_id: str,
        session_closed_event: asyncio.Event,
    ):
        """
        Loop principal del Canal 2.
        Escucha transcripciones y decide si lanzar una búsqueda.
        """
        logger.info(f"🧠 ParallelBrain: Canal 2 activated for {agent_id}")
        buffer = []

        try:
            while not session_closed_event.is_set():
                try:
                    # Esperar transcripción con timeout para poder chequear session_closed
                    try:
                        segment = await asyncio.wait_for(
                            transcript_queue.get(), timeout=2.0
                        )
                    except asyncio.TimeoutError:
                        continue

                    if not segment:
                        continue

                    buffer.append(segment)

                    # Acumular al menos 1 segmento antes de analizar (evaluar individualmente)
                    if len(buffer) < 1:
                        continue

                    full_text = " ".join(buffer)
                    buffer = []  # Limpiar buffer

                    # Verificar si la consulta merece búsqueda web
                    if not self._needs_search(full_text):
                        continue

                    logger.info(f"🔍 ParallelBrain: Search triggered for: '{full_text[:60]}...'")

                    # Ejecutar búsqueda en background sin bloquear
                    result = await self._search(full_text, agent_id)

                    if result and not reconnect_queue.full():
                        logger.info(f"🔍 ParallelBrain: Search result ready. Signaling reconnect.")
                        try:
                            reconnect_queue.put_nowait(result)
                        except asyncio.QueueFull:
                            logger.warning("ParallelBrain: Reconnect queue full — dropping result.")

                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    logger.error(f"ParallelBrain iteration error: {e}")
                    await asyncio.sleep(1)

        except asyncio.CancelledError:
            raise
        finally:
            logger.info("🧠 ParallelBrain: Canal 2 deactivated.")

    def _needs_search(self, text: str) -> bool:
        """
        Heurística simple: ¿La consulta del usuario implica
        información factual, actual o externa?
        """
        triggers = [
            # Preguntas sobre el mundo real
            "qué es", "quién es", "cuándo", "dónde está", "cómo funciona",
            "what is", "who is", "when did", "where is", "how does",
            # Referencias a noticias o eventos actuales
            "últimas noticias", "qué pasó", "recientemente", "hoy",
            "latest news", "what happened", "recently", "today",
            # Búsquedas explícitas
            "busca", "buscar", "investiga", "dime sobre",
            "search", "look up", "find out", "tell me about",
        ]
        text_lower = text.lower()
        return any(t in text_lower for t in triggers)

    async def _search(self, query: str, agent_id: str) -> str | None:
        """
        Ejecuta búsqueda web usando Gemini con Google Search Grounding.
        Retorna un string de contexto listo para inyectar en system_instruction.
        """
        if not self.client:
            logger.warning("ParallelBrain: No Gemini client available for search.")
            return None

        try:
            response = await asyncio.wait_for(
                self.client.aio.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=f"Busca información sobre: {query}. Resume los hallazgos más relevantes en máximo 3 oraciones concisas.",
                    config=types.GenerateContentConfig(
                        tools=[types.Tool(google_search=types.GoogleSearch())],
                    ),
                ),
                timeout=15.0,
            )

            if response and response.text:
                result = response.text.strip()
                # Formatear como contexto inyectable
                return f"[BÚSQUEDA WEB RECIENTE]: {result}"

        except asyncio.TimeoutError:
            logger.warning("ParallelBrain: Search timed out.")
        except Exception as e:
            logger.warning(f"ParallelBrain: Search failed: {e}")

        return None

# Singleton
parallel_brain = ParallelBrain()
