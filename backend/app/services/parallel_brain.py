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
        self.latest_context: str | None = None  # NUEVO
        self.last_search_time: datetime = datetime.min  # NUEVO
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
                    logger.info(f"🔍 ParallelBrain: Evaluating segment: '{full_text[:60]}'")

                    # Verificar si la consulta merece búsqueda web
                    if not self._needs_search(full_text):
                        continue

                    logger.info(f"🔍 ParallelBrain: Search triggered for: '{full_text[:60]}...'")

                    # Ejecutar búsqueda en background sin bloquear
                    result = await self._search(full_text, agent_id)

                    if result and not reconnect_queue.full():
                        logger.info(f"🔍 ParallelBrain: Search result ready. Signaling reconnect.")
                        # Guardar el contexto más reciente para que SessionManager lo lea
                        self.latest_context = result

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
        # Cooldown de 45 segundos entre búsquedas
        if (datetime.now() - self.last_search_time).seconds < 45:
            return False
            
        if len(text.split()) < 4:  # Mínimo 4 palabras
            return False

        # Solo triggers muy explícitos — preguntas directas sobre el mundo
        hard_triggers = [
            "noticias", "noticia", "news",
            "precio", "price", "bitcoin", "dólar",
            "qué pasó", "what happened", "qué ocurrió",
            "busca", "buscar", "search", "investiga",
            "quién ganó", "who won",
            "cuánto vale", "how much",
        ]
        
        # Palabras que indican nombre propio o saludo — EXCLUIR
        exclude = ["kisuna", "kizuna", "hola", "hello", "ola", "hi"]
        text_lower = text.lower()
        
        if any(e in text_lower for e in exclude) and len(text.split()) < 6:
            return False
            
        return any(t in text_lower for t in hard_triggers)

    async def _search(self, query: str, agent_id: str) -> str | None:
        if not self.client:
            return None

        self.last_search_time = datetime.now()

        try:
            # PASO 1: Limpiar e interpretar la query garbled
            clean_response = await asyncio.wait_for(
                self.client.aio.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=f"El siguiente texto es una transcripción de voz con errores de reconocimiento: '{query}'. ¿Qué información real está buscando el usuario? Responde SOLO con una query de búsqueda limpia en español, máximo 8 palabras. Si no puedes determinar la intención, responde exactamente: UNCLEAR",
                ),
                timeout=8.0,
            )

            if not clean_response or not clean_response.text:
                return None

            clean_query = clean_response.text.strip()
            
            if "UNCLEAR" in clean_query or len(clean_query) < 3:
                logger.info(f"🔍 ParallelBrain: Query unclear after cleaning — skipping search.")
                return None

            logger.info(f"🔍 ParallelBrain: Cleaned query: '{clean_query}'")

            # PASO 2: Buscar con la query limpia
            response = await asyncio.wait_for(
                self.client.aio.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=f"Busca información actual sobre: {clean_query}. Resume en máximo 3 oraciones con datos concretos y fechas si las hay. Si no hay información reciente confiable, responde: SIN_DATOS",
                    config=types.GenerateContentConfig(
                        tools=[types.Tool(google_search=types.GoogleSearch())],
                    ),
                ),
                timeout=15.0,
            )

            if response and response.text:
                result = response.text.strip()
                if "SIN_DATOS" in result:
                    logger.info(f"🔍 ParallelBrain: No reliable data found for '{clean_query}'.")
                    return None
                return f"[BÚSQUEDA WEB - {clean_query}]: {result}"

        except asyncio.TimeoutError:
            logger.warning("ParallelBrain: Search timed out.")
        except Exception as e:
            logger.warning(f"ParallelBrain: Search failed: {e}")

        return None

# Singleton
parallel_brain = ParallelBrain()
