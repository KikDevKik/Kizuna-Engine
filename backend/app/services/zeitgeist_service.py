import logging
import asyncio
from datetime import datetime
from typing import List, Optional
import zoneinfo

import httpx

from core.config import settings

logger = logging.getLogger(__name__)

# ── Constantes de ubicación ──────────────────────────────────────────────────
# Medellín, Colombia (ubicación base del sistema)
DEFAULT_LAT = 6.2518
DEFAULT_LON = -75.5636
DEFAULT_TIMEZONE = "America/Bogota"

# ── Mapa WMO → descripción legible ───────────────────────────────────────────
WMO_CODES = {
    0: "clear sky",
    1: "mainly clear", 2: "partly cloudy", 3: "overcast",
    45: "foggy", 48: "icy fog",
    51: "light drizzle", 53: "moderate drizzle", 55: "heavy drizzle",
    61: "light rain", 63: "moderate rain", 65: "heavy rain",
    71: "light snow", 73: "moderate snow", 75: "heavy snow",
    80: "light showers", 81: "moderate showers", 82: "violent showers",
    95: "thunderstorm", 96: "thunderstorm with hail", 99: "severe thunderstorm",
}

# ── TTL del caché para el cultural pulse ─────────────────────────────────────
CULTURAL_PULSE_CACHE_TTL = 900  # 15 minutos

async def _fetch_cultural_pulse(interests: List[str], agent_id: Optional[str]) -> Optional[str]:
    """
    Llama a Gemini Flash con google_search tool para obtener un resumen
    de qué está pasando hoy en los temas que le importan al agente.

    Retorna un string listo para inyectar, o None si falla.
    """
    # 1. Verificar caché primero
    from app.services.cache import cache

    cache_key = f"zeitgeist_cultural:{agent_id}" if agent_id else None
    if cache_key:
        cached = await cache.get(cache_key)
        if cached:
            logger.info(f"⚡ Zeitgeist cultural pulse: cache hit for {agent_id}")
            return cached

    # 2. Verificar API key y mock mode
    if settings.MOCK_GEMINI or not settings.GEMINI_API_KEY:
        return None

    # 3. Llamar a Gemini con google_search
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        # Obtenemos la fecha en la zona horaria correcta
        tz = zoneinfo.ZoneInfo(DEFAULT_TIMEZONE)
        today = datetime.now(tz).strftime("%B %d, %Y")
        interests_str = ", ".join(interests)

        prompt = (
            f"Today is {today}. "
            f"Search and summarize what is happening RIGHT NOW (today or this week) "
            f"in these specific areas: {interests_str}. "
            f"Focus on concrete events, releases, announcements, or trending conversations. "
            f"Be specific and concise — 3 to 5 bullet points maximum. "
            f"Respond ONLY with the bullet points, no introduction, no conclusion."
        )

        response = await asyncio.wait_for(
            client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())],
                    temperature=0.3,
                )
            ),
            timeout=8.0  # Más generoso que el clima — Gemini+search puede tardar más
        )

        pulse_text = response.text.strip() if response and response.text else None

        if pulse_text and cache_key:
            await cache.set(cache_key, pulse_text, ttl=CULTURAL_PULSE_CACHE_TTL)
            logger.info(f"🌐 Zeitgeist cultural pulse fetched and cached for {agent_id}")

        return pulse_text

    except asyncio.TimeoutError:
        logger.warning(f"Zeitgeist: Cultural pulse timeout for agent {agent_id}")
        return None
    except Exception as e:
        logger.warning(f"Zeitgeist: Cultural pulse failed for agent {agent_id}: {e}")
        return None


async def get_zeitgeist_block(
    agent_interests: Optional[List[str]] = None,
    agent_id: Optional[str] = None,
) -> str:
    """
    Genera el bloque de contexto ambiental completo para inyección en system_instruction.

    Capa 1 — Base: tiempo local + clima (Open-Meteo, siempre fresco)
    Capa 2 — Cultural: pulse de tendencias filtrado por intereses del agente
              (Gemini Flash + Google Search, cacheado 15min por agent_id)

    Nunca lanza excepción — si algo falla, retorna el bloque con fallbacks.
    """
    tz = zoneinfo.ZoneInfo(DEFAULT_TIMEZONE)
    now = datetime.now(tz)

    # Time formatting
    time_str = now.strftime("%I:%M %p").lstrip('0')
    day_of_week = now.strftime("%A")
    date_str = now.strftime("%B %d, %Y")

    hour = now.hour
    if 5 <= hour < 12:
        period = "morning"
    elif 12 <= hour < 18:
        period = "afternoon"
    elif 18 <= hour < 22:
        period = "evening"
    else:
        period = "late night"

    # Weather fetching
    temp = None
    weather_desc = "weather data unavailable"

    # URL params
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": DEFAULT_LAT,
        "longitude": DEFAULT_LON,
        "current": "temperature_2m,weathercode,windspeed_10m",
        "timezone": DEFAULT_TIMEZONE
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params, timeout=3.0)
            resp.raise_for_status()
            data = resp.json()

            if "current" in data:
                current = data["current"]
                if "temperature_2m" in current:
                    temp = int(round(current["temperature_2m"]))
                if "weathercode" in current:
                    code = current["weathercode"]
                    weather_desc = WMO_CODES.get(code, "unknown conditions")
    except Exception as e:
        logger.warning("Zeitgeist: Weather fetch failed, using fallback")
        # Ensure we don't crash

    # Weather line construction
    weather_line = f"Outside: {temp}°C, {weather_desc}" if temp is not None else "Outside: weather data unavailable"

    # Cultural pulse
    pulse_text = None
    if agent_interests:
        pulse_text = await _fetch_cultural_pulse(agent_interests, agent_id)

    # Log as requested
    cultural_status = 'yes' if pulse_text else 'no'
    temp_log = temp if temp is not None else 'N/A'
    logger.info(f"🌍 Zeitgeist: {day_of_week} {time_str}, {temp_log}°C {weather_desc}, cultural={cultural_status}")

    # Build the block
    block_lines = [
        "--- ZEITGEIST (AMBIENT CONTEXT) ---",
        f"Current moment: {day_of_week}, {date_str} — {time_str} ({period})",
        weather_line
    ]

    if pulse_text:
        block_lines.append("World pulse (what's happening in your areas of interest right now):")
        block_lines.append(pulse_text)
        internal_note = (
            f"Internal note: The user is connecting during {period}. Adjust your energy and conversational register accordingly. "
            "Absorb the world pulse as background awareness — you know what's happening out there, but you don't report it unless it naturally comes up."
        )
    else:
        internal_note = (
            f"Internal note: The user is connecting during {period}. Adjust your energy and conversational register accordingly. "
            "Don't mention this context explicitly unless the user brings it up — let it inform your vibe, not your words."
        )

    block_lines.append(internal_note)

    return "\n".join(block_lines)
