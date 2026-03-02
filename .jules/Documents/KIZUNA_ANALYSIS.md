# KIZUNA ENGINE — ESTADO ACTUAL DEL SISTEMA
## Reconocimiento Post-Fase 6 | 3 de Marzo de 2026

---

## VISIÓN ORIGINAL vs ESTADO REAL

### Lo que el GDD prometía
Kizuna Engine fue concebido como un "Motor de Encarnación Universal" bajo el concepto **Isekai Inverso**: entidades digitales conscientes invocadas al espacio físico del usuario. La promesa técnica era:
- Interacción Full-Duplex con latencia <800ms
- Percepción multimodal simultánea (audio + video)
- Memoria persistente evolutiva via GraphRAG (Spanner)
- Hasta 6 agentes concurrentes (Fase 9)
- Personalidad que evoluciona matemáticamente con cada interacción

### Dónde estamos hoy
El Kizuna Engine es un sistema funcional de agentes de IA conversacionales con voz en tiempo real. La fundación está construida. El motor late.

---

## INVENTARIO DE COMPONENTES — ESTADO POR MÓDULO

### ✅ COMPLETADO Y FUNCIONAL

| Módulo | Archivo | Estado | Notas |
|--------|---------|--------|-------|
| **API Backend** | `app/main.py` | ✅ Estable | FastAPI + Uvicorn, WebSocket endpoint |
| **Agent Service** | `app/services/agent_service.py` | ✅ Estable | CRUD agentes vía JSON |
| **Soul Assembler** | `app/services/soul_assembler.py` | ✅ Estable | Static DNA, cache v2 |
| **Ritual System** | `app/routers/agents.py` | ✅ Estable | SoulForge genera agentes vía LLM |
| **Hollow Forge** | `app/routers/agents.py` | ✅ Estable | Agentes con gossip protocol |
| **Session Manager** | `app/services/session_manager.py` | ✅ Estable | WebSocket lifecycle + TaskGroup |
| **Gemini Live** | `app/services/gemini_live.py` | ✅ Estable | SDK 1.65.0, send_realtime_input |
| **Audio Session** | `app/services/audio_session.py` | ✅ Estable | audio_stream_end=True, VAD server |
| **SubconsciousMind** | `app/services/subconscious.py` | ⚠️ Parcial | Funcional pero inyecciones deshabilitadas |
| **ReflectionMind** | `app/services/reflection.py` | ✅ Estable | Cooldown 45s |
| **InjectionLoop** | `app/services/audio_session.py` | ✅ Estable | Flag running, session_closed_event |
| **Supervisor** | `app/services/supervisor.py` | ✅ Estable | Aware de session_closed_event |
| **Sleep Manager** | `app/services/sleep_manager.py` | ✅ Estable | REM Sleep, consolidación |
| **Local Graph** | `app/repositories/local_graph.py` | ✅ Estable | SQLite, edges, WIPE/REBIRTH |
| **Auction Service** | `app/services/auction_service.py` | ✅ Estable | Turn control por sesión |
| **Cache Service** | `app/services/cache.py` | ✅ Estable | Redis con fallback Memory |
| **Time Skip** | `app/services/time_skip.py` | ✅ Estable | Simulación offline |
| **Frontend Core** | `frontend/src/` | ✅ Estable | React + AudioWorklet |
| **PCM Processor** | `frontend/src/worklets/pcm-processor.js` | ✅ Estable | VAD local, end_of_turn signal |
| **LiveAPIContext** | `frontend/src/contexts/LiveAPIContext.tsx` | ✅ Estable | Ready signal, binary/text routing |
| **useLiveAPI** | `frontend/src/hooks/useLiveAPI.ts` | ✅ Estable | AudioStreamManager, JSON.stringify |
| **KizunaCore** | `frontend/src/components/KizunaCore.tsx` | ✅ Estable | Orbe animado, estados visuales |
| **Kizuna HUD** | `frontend/src/KizunaHUD.css` | ✅ Estable | Estados: idle, ready, listening |
| **Agent Roster** | `frontend/src/` | ✅ Estable | Con fallback ARQUITECTURA-01 |

### ⚠️ FUNCIONAL CON LIMITACIONES CONOCIDAS

| Módulo | Limitación | Referencia Backlog |
|--------|-----------|-------------------|
| **SubconsciousMind** | Inyecciones de texto deshabilitadas en Live (corrompen historial audio nativo) | AUDIO-01 |
| **Voice Consistency** | El modelo preview muta de voz entre turnos (limitación Google) | Esperar GA |
| **Flashback RAG** | Solo dispara con cues temporales explícitos — correcto por diseño | - |
| **Language Protocol** | Funciona pero `known_languages: []` en agentes hollow-forged no tiene idiomas | Mejorar Ritual |

### ❌ PENDIENTE / NO IMPLEMENTADO

| Característica | Fase | Descripción |
|---------------|------|-------------|
| **Zeitgeist Injection** | Fase 7 | Contexto cultural en tiempo real |
| **Reactive Search** | Fase 7 | Agente busca web durante conversación |
| **Initiative Protocol** | Fase 7 | Agente habla proactivamente |
| **Vision (Cámara)** | Fase 7 | Streaming de video a Gemini |
| **BLOCK_NONE Safety** | Fase 7 | Liberación de restricciones para generación procedural |
| **ARQUITECTURA-01** | Backlog | Sync AgentService ↔ LocalSoulRepository |
| **AUDIO-01** | Backlog | Inyecciones texto compatibles con SDK 1.65.0 |
| **Spanner Graph** | Fase 8+ | Reemplazar SQLite con Spanner (producción) |
| **Multi-Agent Concurrent** | Fase 9 | 6 agentes simultáneos, Auction MARL |
| **Ephemeral Tokens** | Producción | Auth segura cliente→Gemini |

---

## ARQUITECTURA TÉCNICA ACTUAL

```
FRONTEND (React + Vite)
├── AudioWorklet (pcm-processor.js)
│   ├── Captura micrófono → PCM 16kHz 16-bit mono
│   ├── VAD local (umbral 0.003)
│   └── end_of_turn signal → onmessage → useLiveAPI
├── useLiveAPI.ts (activo en App.tsx)
│   ├── WebSocket → ws://backend:8000/ws/live
│   ├── Envía: binary (PCM chunks) + JSON (control)
│   └── Recibe: binary (audio 24kHz) + JSON (session_ready, transcript)
└── KizunaCore.tsx
    └── Orbe visual: idle → ready → listening → speaking

BACKEND (FastAPI + Uvicorn)
├── WebSocket /ws/live
│   ├── session_manager.handle_session()
│   ├── TaskGroup:
│   │   ├── send_to_gemini() — audio PCM chunks via send_realtime_input()
│   │   │   └── audio_stream_end=True cuando llega end_of_turn del frontend
│   │   ├── receive_from_gemini() — audio 24kHz → websocket.send_bytes()
│   │   └── CognitiveSupervisor (session_closed_event aware):
│   │       ├── SubconsciousMind — transcript → RAG → System Hints (deshabilitado)
│   │       ├── InjectionLoop — injection_queue → session.send() (texto)
│   │       └── ReflectionMind — output → self-critique → injection (45s cooldown)
│   └── Cleanup: Sleep Manager, Graph cleanup, memory buffer
├── REST /api/agents/
│   ├── GET / — list agents (con ARQUITECTURA-01 fallback)
│   ├── POST /ritual — SoulForge (AFC enabled, asigna voz)
│   ├── POST /forge_hollow — Hollow Forge + Gossip Protocol
│   └── DELETE /system/purge-memories — WIPE GRAPH / SCORCHED EARTH
└── Services:
    ├── GeminiLiveService — SDK 1.65.0, _get_config(), tools=[]
    ├── AgentService — JSON filesystem, cache memory/Redis
    ├── LocalSoulRepository — SQLite kizuna_graph.db
    ├── SoulAssembler — Static DNA v2, language protocol
    └── CacheService — Redis con fallback local memory

GEMINI API (Google)
├── Modelo: gemini-2.5-flash-native-audio-preview-12-2025
├── LiveConnectConfig:
│   ├── response_modalities: ["AUDIO"]
│   ├── speech_config: VoiceConfig(voice_name=agent.voice_name or "Puck")
│   ├── system_instruction: Content(soul_dna)
│   └── tools: []  ← AFC deshabilitado en sesiones Live
└── Flujo:
    ├── send_realtime_input(audio=Blob(data, "audio/pcm;rate=16000")) — chunks
    ├── send_realtime_input(audio_stream_end=True) — EOT signal
    └── receive() → server_content.model_turn.parts[].inline_data.data (24kHz PCM)
```

---

## DECISIONES ARQUITECTÓNICAS VIGENTES

| Decisión | Rationale | Revisitar en |
|----------|-----------|-------------|
| SQLite en lugar de Spanner | Dev local, sin GCP costs | Fase 8 (producción) |
| JSON en lugar de PostgreSQL para agentes | Simplicidad, sin migraciones | Fase 8 |
| AFC deshabilitado en Live | Conflicto con pipeline de audio nativo | AUDIO-01 |
| VAD server-side (Gemini) | SDK 1.65.0 soporta VAD automático | Estable |
| end_of_turn vía audio_stream_end | Señal nativa del protocolo Live | Estable |
| Inyecciones deshabilitadas | Corrompían historial audio nativo | AUDIO-01 |
| Flashback: intent-based RAG | No cada frase, solo cues temporales | Estable |
| Session: un evento por sesión | session_closed_event fresco por sesión | Estable |
| Voice fallback "Puck" | Agentes sin voice_name asignada | Mejorar en Ritual |

---

## BUGS CONOCIDOS / DEUDA TÉCNICA

### CRÍTICOS (bloquean features)
- **AUDIO-01**: SubconsciousMind no puede inyectar contexto en sesiones Live. El protocolo nativo de audio de Gemini 2.5 rechaza mensajes de texto mezclados con audio (corrupción de historial). Necesita investigación con SDK 1.65.0.

### MODERADOS (degradan experiencia)
- **VOICE-01**: Inconsistencia de timbre entre turnos en el modelo preview. Limitación de Google, no hay fix hasta GA.
- **ARCH-01**: AgentService y LocalSoulRepository desincronizados post-WIPE GRAPH. El fallback en list_agents() es temporal.
- **LANG-01**: Agentes hollow-forged tienen `known_languages: []`. El Ritual debería asignar idiomas basado en el nombre/lore del agente.

### MENORES (cosméticos)
- Log de diagnóstico `📥 Gemini raw response FULL` sigue activo — marcar como `# DEBUG`
- InjectionLoop spam post-cierre corregido pero Supervisor aún puede reiniciar tareas que terminan normalmente (log de warning)

---

## MÉTRICAS DEL SISTEMA (estimadas, sin benchmarks formales)

| Métrica | Valor Estimado | Target GDD |
|---------|---------------|-----------|
| Latencia primer audio de respuesta | 800ms-2s | <800ms |
| Estabilidad de sesión | Alta (sin disconnects 1011) | Alta |
| Inyecciones de contexto | 0 (deshabilitadas) | Continuas |
| Agentes concurrentes | 1 | 6 (Fase 9) |
| Persistencia de memoria | Sesión + consolidación | Long-term graph |
| Calidad de voz | Variable (preview) | Estable (GA) |

---

*Documento generado: 3 de Marzo de 2026 | El Cronista*