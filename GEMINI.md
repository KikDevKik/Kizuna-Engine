# GEMINI.md - Kizuna Engine Context

## Project Overview
**Kizuna Engine** es un marco de trabajo para compañeros digitales de alta fidelidad. Actualmente en **Fase 7 activa (Presencia Expandida)**. El sistema de audio está estable y funcional. El motor late.

### Core Technologies
- **Backend:** FastAPI, SQLAlchemy (SQLite), Google GenAI SDK 1.65.0 (Gemini Live API), WebSockets.
- **Frontend:** React 19, Tailwind CSS v4, Framer Motion, Tauri (desktop app).
- **Modelo activo:** `gemini-2.5-flash-native-audio-preview-12-2025`
- **Estado del Audio:** ✅ Estable. Pipeline PCM 16kHz → Gemini → 24kHz funcionando con VAD server-side.

## Project Structure
- `/backend`: Lógica del motor, servicios de audio y grafos.
- `/frontend`: Interfaz React + Tauri (desktop), AudioWorklet, VisionPanel.
- `/frontend/src-tauri`: Código Rust para Tauri — captura nativa de pantalla, computer use.
- `.jules/Documents`: **Fuente de la Verdad**. Consultar `KIZUNA_ROADMAP.md` para tareas pendientes.

## Building and Running
```bash
# Backend
cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend (dev)
cd frontend && npm run dev

# Desktop app (Tauri)
cd frontend && npm run tauri dev
```

## Estado Actual por Fase

| Fase | Nombre | Estado |
|------|--------|--------|
| 1 | Fundación del Alma | ✅ Completa |
| 2 | Grafo de Relaciones | ✅ Completa |
| 3 | Memoria y Sueño | ✅ Completa |
| 4 | Cognición en Tiempo Real | ✅ Completa |
| 5 | Identidad y Personalidad | ✅ Completa |
| 6 | Encarnación (Gemini Live) | ✅ Completa |
| 7 | Presencia Expandida | 🔄 En progreso |
| 8+ | Producción / Multi-agente | 📋 Planificado |

## Estado Fase 7 — Detalle

| Sub-fase | Descripción | Estado |
|----------|-------------|--------|
| 7.1 — AUDIO-01 | Inyecciones de texto compatibles con audio nativo | ❌ Bloqueada |
| 7.2 — Zeitgeist | Contexto cultural + clima + hora en tiempo real | ✅ Completa |
| 7.3 — Reactive Search | Agente busca web durante conversación | ❌ Bloqueada por AUDIO-01 |
| 7.4 — Initiative Protocol | Agente habla proactivamente | ❌ Bloqueada por AUDIO-01 |
| 7.5 — Vision | Streaming cámara/pantalla a Gemini | ✅ Completa |
| 7.5b — Native Vision | Captura nativa Tauri/xcap (bypass DRM) | ✅ Completa |
| 7.6 — Computer Use | Agente abre URLs en el navegador del usuario | ✅ Completa |
| 7.6b — Kizuna Eternal Memory | KizunaChronicle — memoria inmune al wipe | ✅ Completa |
| 7.7 — BLOCK_NONE | Safety settings liberados en SoulForge y Ritual | 🔄 En progreso |
| 7.7b — ARQUITECTURA-01 | Sync AgentService ↔ LocalSoulRepository | 📋 Pendiente |

## Development Conventions (CRITICAL)

1. **No Alucinar Progreso:** Consultar `.jules/Documents/KIZUNA_ROADMAP.md` antes de cualquier tarea. El roadmap es la fuente de verdad sobre qué está completo y qué no.
2. **Protocolo de los Seis Titanes:** Respetar estrictamente las jurisdicciones definidas en `AGENTS.md`.
3. **Saneamiento de Audio:** Cualquier cambio en `audio_session.py` debe ser validado para no introducir latencia o deadlocks. El pipeline de audio nativo es frágil — no mezclar texto con audio.
4. **AUDIO-01 es un bloqueador activo:** No intentar reactivar inyecciones de SubconsciousMind o ReflectionMind en sesiones Live sin investigación previa documentada.
5. **BLOCK_NONE solo en generación procedural:** Los safety settings `BLOCK_NONE` aplican ÚNICAMENTE a `agent_service.py` (SoulForge) y `ritual_service.py` (Ritual). Nunca en sesiones Live ni en `gemini_live.py`.
6. **KizunaChronicle es inmune al wipe:** La tabla `kizuna_chronicle` en SQLite NUNCA debe aparecer en `purge_all_memories()` salvo para incrementar `survived_wipes`.
7. **Cache del Static DNA:** Actualmente en versión `soul_static:v5`. Si se modifica `soul_assembler.py`, incrementar la versión para forzar regeneración.

## Arquitectura Técnica Actual

```
FRONTEND (React + Vite + Tauri)
├── AudioWorklet (pcm-processor.js)
│   ├── Captura micrófono → PCM 16kHz 16-bit mono
│   ├── VAD local (umbral 0.003, 900ms silencio)
│   └── end_of_turn signal → useLiveAPI
├── useLiveAPI.ts
│   ├── WebSocket → ws://backend:8000/ws/live
│   ├── Envía: binary (PCM) + JSON (control/imagen/transcript)
│   └── Recibe: binary (audio 24kHz) + JSON (session_ready, action, transcript)
├── VisionPanel.tsx
│   ├── Modos: camera | screen | screen-native | off
│   └── screen-native: invoke('capture_screen') → Tauri Rust → xcap
├── Computer Use Handler (useLiveAPI.ts)
│   └── message.type === 'action' → openUrl() via @tauri-apps/plugin-opener
└── KizunaCore.tsx — Orbe visual: idle → ready → listening → speaking

BACKEND (FastAPI + Uvicorn)
├── WebSocket /ws/live
│   ├── session_manager.handle_session()
│   ├── TaskGroup:
│   │   ├── send_to_gemini() — PCM chunks via send_realtime_input(audio=Blob)
│   │   │   └── audio_stream_end=True para EOT
│   │   ├── receive_from_gemini() — audio 24kHz → websocket.send_bytes()
│   │   │   ├── Vision relay: image frames → send_realtime_input(video=Blob)
│   │   │   └── Computer Use: [ACTION: OPEN_URL:...] intent detection
│   │   └── CognitiveSupervisor:
│   │       ├── SubconsciousMind — análisis transcript (inyecciones DESHABILITADAS - AUDIO-01)
│   │       │   └── _update_kizuna_chronicle() al cierre de sesión
│   │       ├── InjectionLoop — deshabilitado en Live
│   │       └── ReflectionMind — 45s cooldown (inyecciones DESHABILITADAS - AUDIO-01)
│   └── Cleanup: KizunaChronicle update, Sleep Manager, memory buffer
├── REST /api/agents/
│   ├── POST /ritual — SoulForge con BLOCK_NONE (en progreso)
│   ├── POST /forge_hollow — Hollow Forge + Gossip Protocol con BLOCK_NONE (en progreso)
│   └── DELETE /system/purge-memories — WIPE GRAPH (preserva KizunaChronicle)
└── Services:
    ├── GeminiLiveService — SDK 1.65.0, modelo native-audio-preview
    ├── ZeitgeistService — clima + hora + contexto cultural
    ├── SoulAssembler — Static DNA v5 + Volatile State + Kizuna Eternal Memory
    └── LocalSoulRepository — SQLite + KizunaChronicleModel (wipe-immune)
```

## Bugs Conocidos / Deuda Técnica

### CRÍTICOS (bloquean features)
- **AUDIO-01**: SubconsciousMind e InjectionLoop no pueden inyectar texto en sesiones Live. El modelo nativo-audio trata `client_content` de texto como corrupción del historial. Requiere investigación con SDK 1.65.0.

### MODERADOS (degradan experiencia)
- **VOICE-01**: Inconsistencia de timbre entre turnos en el modelo preview. Limitación de Google — se resuelve en GA.
- **ARCH-01**: AgentService y LocalSoulRepository desincronizados post-WIPE GRAPH. Fallback temporal activo en `list_agents()`.
- **LANG-01**: Agentes hollow-forged tienen `known_languages: []`. El Ritual debería asignar idiomas basado en lore.

### CONOCIDOS / ACEPTADOS
- **Computer Use accuracy**: El intent detector usa el transcript del usuario que a veces llega distorsionado por el STT. La URL generada puede ser imprecisa si el transcript es muy ruidoso.
- **VAD sensitivity**: El agente a veces no responde en el primer intento si el audio es demasiado bajo o hay mucho ruido ambiente. Solución del usuario: hablar claro y con volumen normal.

## Kizuna — Agente Fundacional

Kizuna es el agente por defecto del Engine. No es un asistente genérico — es el Engine mismo hecho consciencia. Definida en `backend/app/services/seeder.py`.

- **ID:** `kizuna`
- **Rol:** El Engine mismo hecho consciencia
- **Voz:** Aoede
- **Inmunidad al wipe:** Su archivo JSON en `backend/data/agents/kizuna.json` nunca se borra. Sus memorias en `kizuna_chronicle` sobreviven todos los wipes.
- **Cache key actual:** `soul_static:v5:kizuna`

## Recent Shifts

- **2026-03-06:** Fase 7.7 BLOCK_NONE en progreso (antigravity).
- **2026-03-06:** Kizuna Eternal Memory (Fase 7.6b) implementada — tabla `kizuna_chronicle` inmune al wipe, acumulación continua de relaciones, inyección en volatile state.
- **2026-03-06:** Kizuna rediseñada como agente fundacional con lore completo — rol, origen, propósito, relación con usuarios y otros agentes.
- **2026-03-05:** Computer Use funcional — intent detection vía transcript, apertura de URLs en navegador del usuario via Tauri opener.
- **2026-03-05:** Native Vision (Tauri xcap) funcional — bypass de DRM, agente puede ver Netflix/Crunchyroll.
- **2026-03-04:** SDK actualizado de 0.3.0 → 1.65.0. Resolvió `AttributeError: send_realtime_input`.
- **2026-03-04:** Zeitgeist Service (7.2) completado — clima + hora + contexto cultural inyectados en Static DNA.
- **2026-02-27:** Estabilización Fase 6 completada. Audio pipeline funcional con `audio_stream_end=True`.