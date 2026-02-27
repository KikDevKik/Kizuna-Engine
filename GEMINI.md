# GEMINI.md - Kizuna Engine Context

## Project Overview
**Kizuna Engine** es un marco de trabajo para compañeros digitales de alta fidelidad. Actualmente en estado de **Regresión Técnica en la Fase 6 (Distrito Cero)**. El sistema visual es estable, pero el sistema de audio/habla está bajo reconstrucción tras un intento fallido de avanzar a la Fase 7.

### Core Technologies
- **Backend:** FastAPI, SQLAlchemy (SQLite), Google GenAI (Gemini Live API), WebSockets.
- **Frontend:** React 19, Tailwind CSS v4, Framer Motion.
- **Estado del Audio:** Inestable. El motor de habla presenta bloqueos por umbrales de ruido mal configurados y fallos en el servicio de subastas de micrófono.

## Project Structure
- `/backend`: Lógica del motor, servicios de audio y grafos.
- `/frontend`: Interfaz 3D y manejo de streams de audio.
- `.jules/Documents`: **Fuente de la Verdad**. Consultar `KIZUNA_ROADMAP.md` para tareas pendientes.

## Building and Running
(Ver instrucciones estándar de npm y uvicorn)

## Development Conventions (CRITICAL)
1. **No Alucinar Progreso:** La Fase 7 NO está completa. No intentar implementar funciones de la Fase 7 sin antes estabilizar el audio de la Fase 6.
2. **Protocolo de los Seis Titanes:** Respetar estrictamente las jurisdicciones definidas en `AGENTS.md`.
3. **Saneamiento de Audio:** Cualquier cambio en `audio_session.py` debe ser validado para no introducir latencia o bloqueos de silencio (Deadlocks).

## Recent Shifts
- 2026-02-27: Regresión decretada por El Cronista. Foco total en purgar parches experimentales de la Fase 7 que rompieron el habla en la Fase 6.
