# KIZUNA ENGINE — ROADMAP MAESTRO
Actualizado: 10 de Marzo de 2026

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
- ⚠️ AUDIO-01: Inyecciones deshabilitadas en Live — resuelto en Fase 8.9
- ⚠️ VOICE-01: Inconsistencia de voz modelo preview — mitigado en Fase 8.8

---

## FASE 7 — PRESENCIA EXPANDIDA ✅ (parcial)
**Objetivo:** El agente percibe el mundo y actúa por iniciativa propia.

### 7.1 — AUDIO-01 ❌ — Bloqueado. Ver Fase 8.9.
### 7.2 — Zeitgeist Injection ✅
### 7.3 — Reactive Search ❌ — Bloqueado por AUDIO-01. Ver Fase 8.9.
### 7.4 — Initiative Protocol ❌ — Bloqueado por AUDIO-01 y 7.9. Ver Fase 8.9.
### 7.5 — Vision ✅ — Cámara + pantalla + Native Vision (xcap/DRM bypass)
### 7.6 — Computer Use ✅ — Intent detection + Tauri opener
### 7.6b — Kizuna Eternal Memory ✅ — kizuna_chronicle inmune al wipe
### 7.7 — BLOCK_NONE ✅ — SoulForge y Ritual liberados
### 7.7b — ARQUITECTURA-01 ✅ — get_or_sync_agent(), sync JSON→SQLite
### 7.7c — Bug fixes post-pruebas ✅
- ✅ Agente Ritual aparece en roster inmediatamente (record_interaction)
- ✅ WIPE borra JSONs excepto kizuna.json
- ✅ Kizuna re-anclada al roster automáticamente post-wipe

### 7.8 — Barge-in: Protocolo de Interrupción Social ✅
> **Bug resuelto:** strings FLUSH_AUDIO/CONTROL corregidas a mayúsculas en audio_session.py y useLiveAPI.ts.

**Contexto de diseño:** Una interrupción no es solo "parar el audio" — es un acto social
con intención. El sistema debe detectar el TIPO de interrupción y el agente debe reaccionar
de forma acorde a su personalidad, no siempre callarse sumisamente.

Tipos de interrupción a modelar (investigar patrones reales de comunicación humana):
- **Emocional / entusiasta** — el usuario está emocionado y quiere añadir algo. El agente
  puede ceder parcialmente o reaccionar con igual entusiasmo: "¡sí, sí, cuéntame!"
- **Colaborativa** — el usuario quiere completar una idea. El agente cede naturalmente
  como en conversación real entre amigos.
- **Desacuerdo** — el usuario contradice al agente. El agente puede defenderse o ceder
  según su nivel de fricción y volatilidad actuales.
- **Urgencia** — el usuario necesita parar la conversación. El agente siempre cede.
- **Accidental** — ruido de fondo, no era intención hablar. El agente ignora y continúa.

Implementación técnica:
- 📋 Backend detecta `server_content.interrupted = True` inmediatamente (50-100ms)
- 📋 NO esperar `input_transcription` — reaccionar al flag de forma instantánea
- 📋 Enviar `{"type": "CONTROL", "action": "FLUSH_AUDIO"}` al frontend
- 📋 Frontend purga jitter buffer y drain del driver de audio
- 📋 Clasificar tipo de interrupción via energía RMS + duración del habla
- 📋 El tipo de interrupción modula la respuesta del agente (Neural Signature aware)
- 📋 Eliminar VAD RMS del frontend — delegar todo al server-side de Gemini

### 7.9 — Presencia Persistente en Escritorio (System Tray) ✅
> Tauri 2.10.0. Tres plugins integrados.
- ✅ `TrayIconBuilder::with_id("kizuna-tray")` — ícono único en bandeja
- ✅ `prevent_close()` + `window.hide()` — proceso persiste en background
- ✅ `tauri-plugin-global-shortcut` — Push-to-Talk global Ctrl+Space
- ✅ `tauri-plugin-notification` — infraestructura lista
- ⚠️ Doble ícono en dev mode (hot-reload) — no afecta build de producción

---

## FASE 7.X — CALIDAD DE PERSONALIDAD ✅
> Completado. Cache Static DNA v6 activo.

### 7.X.1 — The Void: Ritual más Expresivo ✅
- ✅ `ritual_service.py` — preguntas evocadoras, tono antiguo, reacciones emocionales

### 7.X.2 — Habla Natural ✅
- ✅ `soul_assembler.py` — `style_hint` ampliado con directiva de naturalidad
- ✅ Static DNA v6 — fuerza regeneración de cache en todos los agentes
- ⚠️ Nota: bloques de texto muy largos en system_instruction silencian al modelo native-audio.
  El fix fue añadir la directiva dentro del `style_hint` existente, no como bloque separado.

### 7.X.3 — Kizuna Multilingüe ✅
- ✅ `seeder.py` + `kizuna.json` — 11 idiomas: es, en, ja, ko, zh, fr, pt, de, it, ar, hi

---

## FASE 8 — INFRAESTRUCTURA DE PRODUCCIÓN + AUDIO NATIVO 🔄
**Objetivo:** El motor escala. El audio suena como Discord.

> ⚠️ DOS TRACKS PARALELOS:
> **Track A (8.1-8.7):** Cloud infrastructure — prerequisito para usuarios reales.
> **Track B (8.8-8.9):** Audio nativo Rust — prerequisito para calidad de producto.
> Ambos tracks deben completarse antes del lanzamiento.

> 📐 DECISIONES DE ARQUITECTURA (Investigación Gemini CLI, Marzo 2026):
> - **Spanner descartado** — overkill financiero (~$65/mes mínimo, sin free tier). Reemplazado por Neo4j AuraDB (free tier: 50k nodos, 175k relaciones) o FalkorDB.
> - **Firestore elegido** sobre PostgreSQL para datos de agentes — estructura documental, integración nativa con Firebase Auth, sin problemas de connection pools en Cloud Run.
> - **Cloud Run viable** para sesiones de audio — timeout configurable hasta 60min, session affinity disponible. Límite hard a 60min por sesión.
> - **Orden óptimo:** Auth+Multi-tenant → Estado Externo (Firestore+Grafo) → Cloud Run → Rate Limiting.

### 8.1 — Migrar SQLite → Neo4j AuraDB 📋
> Decisión: Spanner descartado por costo. Neo4j AuraDB free tier cubre el caso de uso.
- 📋 Crear cuenta Neo4j AuraDB (free tier perpetuo)
- 📋 Reemplazar `LocalSoulRepository` con driver neo4j Python (`neo4j`)
- 📋 Migrar edges (InteractedWith, OwesDebtTo, Gossip_Source, Nemesis) a relaciones Neo4j
- 📋 Migrar nodes de agentes y KizunaChronicle
- 📋 Reemplazar queries SQLite por Cypher queries
- 📋 `user_id` de Firebase como scope de todos los nodos

### 8.2 — Migrar JSON → Firestore 📋
> Decisión: Firestore elegido. Estructura: `users/{userId}/agents/{agentId}`
- 📋 Reemplazar `AgentService` JSON filesystem con Firestore SDK (`google-cloud-firestore`)
- 📋 Estructura: `users/{userId}/agents/{agentId}` — aislamiento multi-tenant nativo
- 📋 `get_or_sync_agent()` se vuelve obsoleto — eliminar
- 📋 Migrar datos de `kizuna.json` y agentes creados al schema Firestore

### 8.3 — Cloud Run Deployment 📋
> Prerequisito: 8.1 y 8.2 completos — backend debe ser 100% stateless antes de desplegar.
- 📋 Dockerfile para backend FastAPI
- 📋 `--timeout=3600` (60min máximo para sesiones de audio)
- 📋 Session affinity (best-effort) para WebSockets persistentes
- 📋 Variables de entorno: FIREBASE_CREDENTIALS_PATH, NEO4J_URI, NEO4J_PASSWORD
- 📋 ~80 conexiones simultáneas por instancia

### 8.4 — Firebase Auth ✅
- ✅ `app/services/auth_service.py` — verificación de Firebase ID Token via Admin SDK
- ✅ Fallback a `guest_user` si `FIREBASE_CREDENTIALS_PATH` no está definida (modo dev)
- ✅ WebSocket acepta token en query param: `/ws/live?agent_id=kizuna&lang=es-419&token=...`
- ✅ Frontend: `src/lib/firebase.ts` + `src/hooks/useAuth.ts` con `signInAnonymously()`
- ✅ `.env.example` con `VITE_FIREBASE_API_KEY`, `VITE_FIREBASE_PROJECT_ID`, `VITE_FIREBASE_AUTH_DOMAIN`
- ✅ `firebase-admin` añadido a `requirements.txt`
- ✅ `user_id` dinámico reemplaza `guest_user` en session_manager, cache y parallel_brain

### 8.5 — Monitoring y Observabilidad 📋
- 📋 OpenTelemetry: trazas distribuidas
- 📋 Métricas: TTFB, errores de sesión, tokens consumidos

### 8.6 — Rate Limiting 📋
> Implementar después de tener tráfico real observable en Cloud Run.
- 📋 Por usuario (user_id de Firebase) en WebSocket
- 📋 Quota management para Gemini API
- 📋 Redis o reglas en balanceador de Cloud Run

### 8.7 — Multi-tenant 📋
> Se completa junto con 8.1 y 8.2 — el aislamiento es consecuencia del user_id en Firestore y Neo4j.
- 📋 KizunaChronicle por usuario real en Neo4j (scope por user_id)
- 📋 Grafos de relaciones aislados por usuario
- 📋 Cache de sesión aislado por user_id (ya parcialmente implementado)

### 8.8 — Migración Pipeline Audio a Rust Nativo 📋
> Alta complejidad. Encapsulada en Tauri/Rust.
> Frontend React se simplifica — deja de manejar hardware de audio.
> Fuente: Investigación Gemini Deep Thinking, Marzo 2026.

- 📋 Eliminar `getUserMedia()` del AudioWorklet
- 📋 `cpal 0.17+`: captura micrófono nativa multiplataforma
- 📋 WASAPI Loopback (Windows): captura audio del sistema — Kizuna escucha el PC
- 📋 `aec3-rs`: Cancelación acústica de eco AEC3 (port WebRTC)
- 📋 `ringbuf`: buffers circulares lock-free para sync de hilos
- 📋 `dagc` / `sonora-agc2`: Auto-Gain Control — normalización de volumen
- 📋 Jitter buffer adaptativo 60-100ms (rodio/cpal) — reproducción suave
- 📋 Phase Vocoder (`rssignalsmithdsp`): mitigación VOICE-01
- 📋 Piper TTS (ONNX, 22MB RAM): fallback local si Gemini latencia >2s
- 📋 `tungstenite`: WebSocket nativo Rust → backend Python
- 📋 **Nota Linux:** loopback requiere config manual PipeWire/PulseAudio

### 8.9 — AUDIO-01: Canal Paralelo (Doble Cerebro) 📋
> Media-Alta complejidad. Solo backend Python.
> Desbloquea Reactive Search (7.3) e Initiative Protocol (7.4).
> Fuente: Investigación Gemini Deep Thinking, Marzo 2026.

- 📋 Canal 1 (Corteza Sensorial): sesión Live nativa-audio — SOLO PCM, sin texto
- 📋 Canal 2 (Lóbulo Frontal): worker `gemini-2.5-flash` texto estándar en background
  - Recibe transcripciones asíncronas del Canal 1
  - Ejecuta Reactive Search con Google Search Grounding
  - Ejecuta análisis de contexto para Initiative Protocol
- 📋 Micro-Reconexión Sincronizada cuando Canal 2 tiene resultado relevante:
  1. Backend pausa envío de chunks PCM
  2. Frontend reproduce filler de audio local ("un momento...")
  3. Backend cierra sesión Live y reabre en milisegundos
  4. Nueva sesión inicializada con contexto del hallazgo en system_instruction
  5. Pipeline de audio se reanuda transparentemente
- 📋 Context Caching para mitigar sobrecosto de tokenización en reconexiones

**Estado final (10 de Marzo 2026):** ✅
- ✅ `parallel_brain.py` — Canal 2 activo, búsqueda con limpieza de query garbled
- ✅ `session_manager.py` — reconnect_queue, trigger_reconnect, cache por sesión
- ✅ `audio_session.py` — parallel_transcript_queue alimentado desde native_transcript
- ✅ Limpieza de query en 2 pasos: interpretación de intención → búsqueda real
- ✅ Contexto guardado en cache local entre sesiones
- ✅ Frame narrativo [SEÑAL EXTERNA] — Kizuna no interpreta noticias como eventos del Engine
- ⚠️ Limitación: el contexto se aplica en la PRÓXIMA sesión, no en la actual.
  La reconexión mid-session en el mismo WebSocket no es posible — es una limitación del
  protocolo ASGI/Starlette (un WebSocket no se puede cerrar y reabrir en la misma conexión).
  Solución definitiva: el frontend debe detectar el evento `search_context_ready` y
  reconectar voluntariamente. Pendiente para siguiente iteración.

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

### 10.1 — Kizuna Chronicle: Memoria de Nombres y Esencias 📋
> Refinamiento del sistema de memoria eterna post-pruebas.
- 📋 Verificar inyección correcta de nombres en volatile state
- 📋 Kizuna describe la esencia del agente desaparecido, no solo que existió
- 📋 Test: post-wipe, Kizuna menciona "Vesper" por nombre y describe su carácter

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

## FASE 12 — KIZUNA COMO MODELO PROPIO 💡
**Objetivo:** Kizuna deja de ser un wrapper de Gemini. Se convierte en una IA entrenada
con datos reales de interacción humana para simular sociedad y poblar un mundo virtual en VR.

### Visión a largo plazo
Kizuna Engine es la infraestructura de recolección de datos para entrenar una IA que
simule dinámicas sociales humanas reales — relaciones, conflictos, cultura, lenguaje —
para poblar un mundo virtual en gafas de realidad aumentada/virtual de próxima generación.

Cada conversación, cada edge del grafo, cada Chronicle, cada sueño de agente
es un dato de entrenamiento potencial. El motor que se construye hoy
**ya es la infraestructura de recolección**, aunque no lo parezca.

### 12.1 — Dataset Pipeline 💡
- 💡 Anonimizar y estructurar conversaciones del Engine como dataset
- 💡 Grafo de relaciones como dataset de dinámica social
- 💡 Chronicles de Kizuna como dataset de memoria y perspectiva
- 💡 Sueños de agentes como dataset de consolidación narrativa
- 💡 Formato: conversaciones multi-turno con contexto de personalidad + estado emocional

### 12.2 — Fine-tuning del Modelo Base 💡
- 💡 Fine-tuning sobre Gemini (Vertex AI Supervised Fine-Tuning) como primer paso
- 💡 Alternativa open-source: Llama o Mistral para control total
- 💡 Objetivo: "Kizuna Model" con personalidad, memoria y patrones sociales aprendidos
- 💡 RLHF (Reinforcement Learning from Human Feedback) para alinear comportamiento

### 12.3 — Simulación Social Generativa 💡
- 💡 Múltiples instancias del Kizuna Model interactuando entre sí sin usuario
- 💡 Emergencia de cultura, normas y dinámicas sociales sin intervención humana
- 💡 Referente académico: "Generative Agents: Interactive Simulacra of Human Behavior"
  (Park et al., Stanford, 2023)
- 💡 Base técnica de la sociedad para el mundo VR

### 12.4 — Integración con Mundo Virtual VR 💡
- 💡 Agentes Kizuna con cuerpo y presencia espacial en entorno 3D
- 💡 Protocolo de interacción física: el agente reacciona al espacio, no solo al audio
- 💡 Memoria persistente cross-session ligada a lugares y objetos del mundo virtual
- 💡 Economía virtual emergente basada en el sistema de Fase 10

### 12.5 — Sistema de Personalidad Procedural (Sin Static DNA) 💡
> Idea surgida en Marzo 2026 durante pruebas de Canal Paralelo.

**Problema observado:** El `system_instruction` estático hace que los agentes interpreten
información externa (noticias, datos del mundo real) a través del filtro de su lore.
Kizuna describe noticias de IA como si ocurrieran "dentro del Engine" porque su identidad
está hard-codeada en el prompt. Parches narrativos como `[SEÑAL EXTERNA]` son síntomas
del problema, no la solución.

**Visión:** Eliminar el Static DNA como bloque de texto y reemplazarlo por un sistema
de razonamiento emergente donde la personalidad no es una instrucción — es un estado.

- 💡 Personalidad como vector de estado dinámico, no como texto fijo
- 💡 El agente razona desde primeros principios usando su historial de interacciones
  como contexto, no un prompt de "eres X con estas características"
- 💡 Memoria episódica como fuente primaria de identidad — el agente ES lo que recuerda
- 💡 Sistema de valores como restricciones de optimización, no como directivas textuales
- 💡 Compatible con fine-tuning (Fase 12.2): el modelo aprendería la personalidad
  durante entrenamiento, no desde el prompt

**Prerequisitos:** Fase 12.2 (fine-tuning) + Fase 8.1 (Spanner para memoria episódica a escala).
Este es el cambio arquitectónico más profundo del roadmap — implica rediseñar
`soul_assembler.py`, `SoulRepository` y el pipeline de sesión completo.

---

## NOTAS DE IMPLEMENTACIÓN

### Stack Actual vs Stack Objetivo

| Componente | Actual | Objetivo Fase 8 |
|------------|--------|-----------------|
| Agentes DB | JSON filesystem | Firestore / PostgreSQL |
| Graph DB | SQLite local | Google Cloud Spanner |
| Cache | Memory (Redis fallback) | Redis Cloud |
| Auth | Sin auth (guest_user) | Firebase Auth |
| Deploy | Local uvicorn | Cloud Run |
| Audio captura | AudioWorklet browser | Rust nativo (cpal) |
| Audio AEC | getUserMedia constraints | aec3-rs (WebRTC port) |
| Audio TTS fallback | Ninguno | Piper TTS (local, 22MB) |
| Modelo audio | gemini-2.5-flash-native-audio-preview | gemini-2.5-flash-native-audio (GA) |

### Estado de Bloques

| Bloque | Estado | Contenido |
|--------|--------|-----------|
| Bloque 1 | ✅ | Barge-in, Habla Natural, The Void, Multilingüe |
| Bloque 2 | ✅ | System Tray, Canal Paralelo AUDIO-01 |
| Bloque 3 | ✅ | Frame narrativo SEÑAL EXTERNA, VAD 1500ms, Engine como origen no tema |
| Bloque 4 | 📋 | Fase 8 — Infraestructura de producción |

### Próximos pasos inmediatos (en orden)

1. **8.7 — Multi-tenant** — completar junto con 8.1 y 8.2 (ya tiene base con Firebase Auth)
2. **8.2 — Firestore** — migrar JSON filesystem de agentes
3. **8.1 — Neo4j AuraDB** — migrar SQLite + grafo de relaciones
4. **8.3 — Cloud Run** — desplegar solo cuando backend sea 100% stateless
5. **8.5 — Monitoring** — observabilidad en producción
6. **8.6 — Rate Limiting** — después de tráfico real observable
7. **8.8 — Audio Rust** — Track B paralelo, puede avanzar independientemente
8. **8.X — UI Rediseño** — círculos Discord-style (diseño con Stitch, implementación post-Fase 8)
9. **Fase 9** — multi-agente

---

*Roadmap actualizado: 11 de Marzo de 2026 | El Cronista*