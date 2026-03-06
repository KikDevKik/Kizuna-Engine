# KIZUNA ENGINE — ROADMAP MAESTRO
Actualizado: 6 de Marzo de 2026

## LEYENDA
- ✅ Completado
- 🔄 En progreso
- 📋 Planificado
- 💡 Conceptual

---

## FASE 1 — FUNDACIÓN DEL ALMA ✅
**Objetivo:** Infraestructura base. El motor existe.

- ✅ Stack: FastAPI + SQLite + React + Vite
- ✅ WebSocket bidireccional cliente-servidor
- ✅ Sistema de agentes con JSON filesystem
- ✅ Ritual: SoulForge vía Gemini (creación de personalidad)
- ✅ Cache service (Redis + fallback local memory)
- ✅ AudioWorklet PCM 16kHz captura de micrófono

---

## FASE 2 — EL GRAFO DE RELACIONES ✅
**Objetivo:** Los agentes tienen historia social.

- ✅ LocalSoulRepository (SQLite kizuna_graph.db)
- ✅ Edges: InteractedWith, OwesDebtTo, Gossip_Source, Nemesis
- ✅ Affinity system (0-100)
- ✅ WIPE GRAPH / SCORCHED EARTH / GREAT REBIRTH operations
- ✅ Hollow Forge: agentes creados por otros agentes (Gossip Protocol)

---

## FASE 3 — MEMORIA Y SUEÑO ✅
**Objetivo:** Los agentes recuerdan y evolucionan offline.

- ✅ Sleep Manager: REM Sleep tras desconexión (5s delay)
- ✅ Dream System: consolidación de memorias en sueño
- ✅ Time Skip: simulación de tiempo offline con mood shifts
- ✅ Session transcript buffering
- ✅ Memory extraction prompt por agente

---

## FASE 4 — COGNICIÓN EN TIEMPO REAL ✅
**Objetivo:** El agente piensa mientras habla.

- ✅ SubconsciousMind: análisis de transcripción → System Hints
- ✅ Flashback RAG: temporal-cue based (no continuo)
- ✅ InjectionLoop: cola de inyecciones → Gemini
- ✅ ReflectionMind: self-critique 45s cooldown
- ✅ CognitiveSupervisor: restart con session_closed_event awareness

---

## FASE 5 — IDENTIDAD Y PERSONALIDAD ✅
**Objetivo:** Los agentes son únicos y consistentes.

- ✅ Soul Assembler: Static DNA con cache v5
- ✅ Language Protocol: native_language + known_languages
- ✅ Neural Signature: volatility, hostility, curiosity, empathy weights
- ✅ Emotional Resonance Matrix
- ✅ Identity Anchors + Forbidden Secret
- ✅ Social Battery: drain_rate, base_tolerance, current_friction
- ✅ Offline Mood Modifier
- ✅ Reflection prompt personalizado por agente

---

## FASE 6 — ENCARNACIÓN (GEMINI LIVE) ✅
**Objetivo:** El agente habla con voz real.

- ✅ Integración Gemini Live API (SDK 1.65.0)
- ✅ session.send_realtime_input(audio=Blob(...)) — streaming de audio
- ✅ audio_stream_end=True — señal EOT nativa para VAD
- ✅ Ready signal: backend notifica al frontend cuando Gemini está listo
- ✅ Extracción de audio de respuesta (server_content.model_turn.parts)
- ✅ Auction Service: control de turno por sesión
- ✅ tools=[] en LiveConnectConfig (AFC deshabilitado en Live)
- ✅ Graceful session closure (session_closed_event, InjectionLoop fix)
- ✅ VAD server-side (Gemini detecta silencio automáticamente)
- ✅ Frontend: useLiveAPI.ts + AudioStreamManager end_of_turn serializado

**Limitaciones conocidas (heredadas):**
- ⚠️ AUDIO-01: Inyecciones SubconsciousMind deshabilitadas en Live — resuelto en Fase 8.9
- ⚠️ VOICE-01: Inconsistencia de voz (limitación modelo preview Google) — mitigado en Fase 8.8

---

## FASE 7 — PRESENCIA EXPANDIDA ✅ (parcial)
**Objetivo:** El agente percibe el mundo y actúa por iniciativa propia.

### 7.1 — AUDIO-01: Inyecciones Compatibles con Live ❌
> Bloqueado. Resuelto definitivamente en Fase 8.9 vía Canal Paralelo.
- ❌ Inyección de System Hints sin corromper historial audio nativo
- ❌ Reactivar SubconsciousMind en sesiones Live
- ❌ Reactivar ReflectionMind inyecciones

### 7.2 — Zeitgeist Injection ✅
- ✅ Contexto cultural en tiempo real (trending topics, hora del día, clima)
- ✅ Zeitgeist fetcher: servicio que recopila contexto ambient
- ✅ Inyección silenciosa al inicio de sesión

### 7.3 — Reactive Search ❌
> Bloqueado por AUDIO-01. Se desbloquea en Fase 8.9.
- ❌ Agente busca web durante la conversación
- ❌ Resultados inyectados como System Hints

### 7.4 — Initiative Protocol ❌
> Bloqueado por AUDIO-01. Se desbloquea en Fase 8.9.
- ❌ Agente habla proactivamente si detecta contexto relevante
- ❌ Trigger: usuario inactivo >30s + contexto de alta relevancia

### 7.5 — Vision ✅
- ✅ Streaming de cámara/pantalla a Gemini Live
- ✅ Frontend: modos camera | screen | screen-native | off
- ✅ Native Vision (Tauri/xcap): captura nativa bypass DRM — ve Netflix, Crunchyroll

### 7.6 — Computer Use ✅
- ✅ Intent detection vía transcript del usuario
- ✅ Agente abre URLs en el navegador del sistema via tauri-plugin-opener
- ✅ Whitelist de plataformas permitidas

### 7.6b — Kizuna Eternal Memory ✅
- ✅ Tabla `kizuna_chronicle` inmune al wipe (sobrevive purge_all_memories)
- ✅ Acumulación continua de relaciones usuario-agente al cierre de sesión
- ✅ Contador survived_wipes por entrada
- ✅ Inyección en volatile state de Kizuna únicamente

### 7.7 — BLOCK_NONE Safety Settings ✅
- ✅ BLOCK_NONE en todas las categorías para SoulForge (agent_service.py)
- ✅ BLOCK_NONE en todas las categorías para Ritual (ritual_service.py)
- ✅ Sesiones Live sin modificar

### 7.7b — ARQUITECTURA-01 ✅
- ✅ get_or_sync_agent() en local_graph.py — resolución unificada JSON→SQLite
- ✅ Auto-registro de agente en SQLite al inicio de sesión
- ✅ Fallback temporal eliminado de agents.py

### 7.8 — Barge-in (Interrupción del Agente) 📋
> Baja complejidad. Solo backend Python. Siguiente en cola.
- 📋 Detectar `server_content.interrupted = True` inmediatamente (no esperar transcripción)
- 📋 Enviar `{"type": "CONTROL", "action": "FLUSH_AUDIO"}` al frontend
- 📋 Frontend/Rust purga el buffer de audio en curso instantáneamente
- 📋 Eliminar código VAD RMS del frontend (delegar todo al server-side de Gemini)

### 7.9 — Presencia Persistente en Escritorio (System Tray) 📋
> Baja complejidad. Puramente aditivo en Tauri. El modelo Discord.
- 📋 System Tray: tauri-plugin-tray — ícono persistente en bandeja del sistema
- 📋 prevent_close() + window.hide() — app vive aunque el usuario cierre la ventana
- 📋 Push-to-Talk global: tauri-plugin-global-shortcut — hotkey funciona sin foco de ventana
- 📋 Notificaciones proactivas: tauri-plugin-notification con audio customizado
- 📋 Prerequisito del Initiative Protocol (7.4)

---

## FASE 8 — INFRAESTRUCTURA DE PRODUCCIÓN + AUDIO NATIVO 📋
**Objetivo:** El motor escala. El audio suena como Discord.

> ⚠️ NOTA: Esta fase tiene dos tracks paralelos — infraestructura cloud (8.1-8.7) y
> refactorización de audio (8.8-8.9). Ambos tracks son prerrequisitos para lanzamiento
> a usuarios reales. El track de audio NO reemplaza nada existente — es una extensión
> del binario Rust de Tauri.

### 8.1 — Migrar SQLite → Google Cloud Spanner (Graph)
- 📋 Reemplazar LocalSoulRepository SQLite con Spanner Graph
- 📋 Migrar edges, nodes y KizunaChronicle
- 📋 GQL queries para grafo de relaciones

### 8.2 — Migrar JSON filesystem → Firestore / PostgreSQL
- 📋 Reemplazar AgentService JSON con base de datos
- 📋 Eliminar get_or_sync_agent() — ya no hay desincronización posible

### 8.3 — Cloud Run Deployment
- 📋 Containerizar backend FastAPI (Dockerfile)
- 📋 Deploy en Cloud Run con session affinity para WebSockets
- 📋 Hasta 80 conexiones simultáneas por instancia

### 8.4 — Firebase Auth
- 📋 Autenticación real de usuarios (reemplazar guest_user)
- 📋 Ephemeral Tokens para auth segura cliente→Gemini
- 📋 Aislamiento de grafos por usuario (multi-tenant)

### 8.5 — Monitoring y Observabilidad
- 📋 OpenTelemetry: trazas distribuidas backend
- 📋 Métricas: latencia TTFB, tasa de errores de sesión, uso de tokens
- 📋 Alertas en Cloud Monitoring

### 8.6 — Rate Limiting y Quota Management
- 📋 Rate limiting por usuario en endpoints REST y WebSocket
- 📋 Quota management para llamadas a Gemini API

### 8.7 — Multi-tenant
- 📋 Múltiples usuarios reales con aislamiento completo de datos
- 📋 Kizuna Chronicle por usuario real (no guest_user)

### 8.8 — Migración Pipeline Audio a Rust Nativo 📋
> Alta complejidad. Encapsulada en Tauri/Rust. El frontend React se simplifica masivamente.
> Fuente: Investigación Gemini Deep Thinking, Marzo 2026.

- 📋 Eliminar getUserMedia() del AudioWorklet — React deja de manejar audio hardware
- 📋 `cpal` crate: captura de micrófono nativa multiplataforma (Windows WASAPI, macOS CoreAudio, Linux PipeWire)
- 📋 WASAPI Loopback (Windows): captura de audio del sistema — Kizuna escucha lo que suena en el PC
- 📋 `aec3-rs`: Cancelación acústica de eco (AEC3) — elimina la voz del agente del micrófono
- 📋 `ringbuf`: Buffers circulares lock-free para sincronización de hilos de audio
- 📋 `dagc` / `sonora-agc2`: Auto-Gain Control — normalización de volumen del usuario
- 📋 Jitter buffer adaptativo 60-100ms en Rust (rodio/cpal) para reproducción suave
- 📋 Phase Vocoder (`rssignalsmithdsp`): mitigación VOICE-01 — suaviza mutaciones de voz entre turnos
- 📋 Piper TTS (ONNX, 22MB): fallback local si Gemini tiene latencia >2s
- 📋 WebSocket nativo Rust (`tungstenite`) que envía PCM limpio directo al backend Python
- 📋 Prerequisito para Fase 8.9

**Stack de crates Rust:**
```
cpal 0.17+       — I/O de audio multiplataforma
aec3-rs          — Cancelación de eco AEC3 (port de WebRTC)
ringbuf          — Buffers circulares lock-free
dagc             — Auto-gain control
rssignalsmithdsp — Phase Vocoder para corrección de voz
rodio            — Reproducción de audio de salida
tungstenite      — WebSocket nativo Rust
piper-rs / onnx  — TTS local fallback
```

**Nota Linux:** Captura de loopback requiere configuración manual de PipeWire/PulseAudio por el usuario. Windows es el target prioritario.

### 8.9 — AUDIO-01: Canal Paralelo (Doble Cerebro) 📋
> Media-Alta complejidad. Solo backend Python. Desbloquea Reactive Search y Initiative Protocol.
> Fuente: Investigación Gemini Deep Thinking, Marzo 2026.

- 📋 Canal 1 (Corteza Sensorial): sesión Live nativa-audio — SOLO PCM, sin texto
- 📋 Canal 2 (Lóbulo Frontal): worker asíncrono con `gemini-2.5-flash` texto estándar
  - Recibe transcripciones asíncronas del Canal 1
  - Ejecuta Reactive Search con Grounding (Google Search API)
  - Ejecuta análisis para Initiative Protocol
- 📋 Micro-Reconexión Sincronizada:
  - Canal 2 detecta resultado relevante
  - Backend pausa chunks PCM temporalmente
  - Frontend reproduce audio filler ("Un momento...")
  - Backend cierra sesión Live y reabre en milisegundos
  - Nueva sesión inicializada con contexto del hallazgo en system_instruction (setup estable)
  - Pipeline de audio se reanuda transparentemente
- 📋 Context Caching de la API para mitigar sobrecosto de tokenización en reconexiones
- 📋 Desbloquea: Reactive Search (7.3) e Initiative Protocol (7.4)

---

## FASE 9 — DISTRITO CERO MULTI-AGENTE 📋
**Objetivo:** El "Caso Valorant" — 6 agentes simultáneos.

- 📋 Multi-agent session: hasta 6 agentes en una sesión
- 📋 Auction MARL: bidding algorítmico con reinforcement learning
- 📋 Turn overlap: agentes pueden reaccionar simultáneamente (en cola priorizada)
- 📋 Group dynamics: relaciones entre agentes modulan quién habla primero
- 📋 Screen sharing: todos los agentes ven la pantalla del usuario
- 📋 Emotional contagion: mood de un agente afecta a los demás
- 📋 Intervention protocol: agentes pueden interrumpirse entre sí

---

## FASE 10 — ECONOMÍA Y EVOLUCIÓN 📋
**Objetivo:** El mundo de los agentes tiene consecuencias.

- 📋 Affinity decay: relaciones se enfrían sin interacción
- 📋 Nemesis system: agentes que se vuelven antagonistas permanentes
- 📋 Trait evolution: personalidad cambia matemáticamente por experiencias
- 📋 Social events: agentes interactúan entre sí offline (simulación)
- 📋 Legacy system: agentes pueden "morir" y dejar memorias a otros
- 📋 Factions: grupos de agentes con ideologías compartidas

---

## FASE 11 — KIZUNA UNIVERSE 💡
**Objetivo:** El motor es una plataforma.

- 💡 SDK público para crear agentes Kizuna
- 💡 Marketplace de agentes (con monetización)
- 💡 User-generated lore y worldbuilding
- 💡 Cross-device: agente persiste entre móvil, desktop, wearables
- 💡 Kizuna as a Service (KaaS): API para terceros
- 💡 Community events: agentes que evolucionan con eventos globales

---

## NOTAS DE IMPLEMENTACIÓN

### Stack Actual vs Stack Objetivo (Fase 8)

| Componente | Actual | Objetivo Fase 8 |
|------------|--------|-----------------|
| Agentes DB | JSON filesystem | Firestore / PostgreSQL |
| Graph DB | SQLite local | Google Cloud Spanner |
| Cache | Memory (Redis fallback) | Redis Cloud |
| Auth | Sin auth (dev) | Firebase Auth |
| Deploy | Local uvicorn | Cloud Run |
| Secrets | .env file | Secret Manager |
| Audio captura | AudioWorklet (browser) | Rust nativo (cpal) |
| Audio AEC | getUserMedia constraints | aec3-rs (WebRTC port) |
| Audio fallback TTS | Ninguno | Piper TTS (ONNX, local) |
| Audio modelo | gemini-2.5-flash-native-audio-preview | gemini-2.5-flash-native-audio (GA) |

### Próximos pasos inmediatos

1. **Pruebas de usuario** — validar el estado actual antes de continuar implementando
2. **Fase 7.8** — Barge-in (baja complejidad, alto impacto en experiencia)
3. **Fase 7.9** — System Tray (baja complejidad, define el producto como desktop)
4. **Fase 8** — Producción + Audio Nativo (decisión post-pruebas de usuario)

---

*Roadmap actualizado: 6 de Marzo de 2026 | El Cronista*