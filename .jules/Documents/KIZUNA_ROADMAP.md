KIZUNA ENGINE — ROADMAP MAESTRO
Actualizado: 3 de Marzo de 2026

LEYENDA

✅ Completado
🔄 En progreso
📋 Planificado
💡 Conceptual


FASE 1 — FUNDACIÓN DEL ALMA ✅
Objetivo: Infraestructura base. El motor existe.

✅ Stack: FastAPI + SQLite + React + Vite
✅ WebSocket bidireccional cliente-servidor
✅ Sistema de agentes con JSON filesystem
✅ Ritual: SoulForge vía Gemini (creación de personalidad)
✅ Cache service (Redis + fallback local memory)
✅ AudioWorklet PCM 16kHz captura de micrófono


FASE 2 — EL GRAFO DE RELACIONES ✅
Objetivo: Los agentes tienen historia social.

✅ LocalSoulRepository (SQLite kizuna_graph.db)
✅ Edges: InteractedWith, OwesDebtTo, Gossip_Source, Nemesis
✅ Affinity system (0-100)
✅ WIPE GRAPH / SCORCHED EARTH / GREAT REBIRTH operations
✅ Hollow Forge: agentes creados por otros agentes (Gossip Protocol)


FASE 3 — MEMORIA Y SUEÑO ✅
Objetivo: Los agentes recuerdan y evolucionan offline.

✅ Sleep Manager: REM Sleep tras desconexión (5s delay)
✅ Dream System: consolidación de memorias en sueño
✅ Time Skip: simulación de tiempo offline con mood shifts
✅ Session transcript buffering
✅ Memory extraction prompt por agente


FASE 4 — COGNICIÓN EN TIEMPO REAL ✅
Objetivo: El agente piensa mientras habla.

✅ SubconsciousMind: análisis de transcripción → System Hints
✅ Flashback RAG: temporal-cue based (no continuo)
✅ InjectionLoop: cola de inyecciones → Gemini
✅ ReflectionMind: self-critique 45s cooldown
✅ CognitiveSupervisor: restart con session_closed_event awareness


FASE 5 — IDENTIDAD Y PERSONALIDAD ✅
Objetivo: Los agentes son únicos y consistentes.

✅ Soul Assembler: Static DNA con cache v2
✅ Language Protocol: native_language + known_languages
✅ Neural Signature: volatility, hostility, curiosity, empathy weights
✅ Emotional Resonance Matrix
✅ Identity Anchors + Forbidden Secret
✅ Social Battery: drain_rate, base_tolerance, current_friction
✅ Offline Mood Modifier
✅ Reflection prompt personalizado por agente


FASE 6 — ENCARNACIÓN (GEMINI LIVE) ✅
Objetivo: El agente habla con voz real.

✅ Integración Gemini Live API (SDK 1.65.0)
✅ session.send_realtime_input(audio=Blob(...)) — streaming de audio
✅ audio_stream_end=True — señal EOT nativa para VAD
✅ Ready signal: backend notifica al frontend cuando Gemini está listo
✅ Extracción de audio de respuesta (server_content.model_turn.parts)
✅ Auction Service: control de turno por sesión
✅ tools=[] en LiveConnectConfig (AFC deshabilitado en Live)
✅ Graceful session closure (session_closed_event, InjectionLoop fix)
✅ VAD server-side (Gemini detecta silencio automáticamente)
✅ Frontend: useLiveAPI.ts + AudioStreamManager end_of_turn serializado
✅ Agente Roster: fallback ARQUITECTURA-01 post-WIPE GRAPH

Limitaciones conocidas (heredadas a Fase 7):

⚠️ AUDIO-01: Inyecciones SubconsciousMind deshabilitadas en Live
⚠️ VOICE-01: Inconsistencia de voz (limitación modelo preview Google)


FASE 7 — PRESENCIA EXPANDIDA 🔄 PRÓXIMA
Objetivo: El agente percibe el mundo y actúa por iniciativa propia.
7.1 — AUDIO-01: Inyecciones Compatibles con SDK 1.65.0

Investigar session.send() con client_content en SDK 1.65.0
Encontrar forma de inyectar System Hints sin corromper historial audio nativo
Reactivar SubconsciousMind en sesiones Live
Reactivar ReflectionMind inyecciones

7.2 — Zeitgeist Injection

Contexto cultural en tiempo real (trending topics, hora del día, clima)
Zeitgeist fetcher: servicio que recopila contexto ambient cada X minutos
Inyección silenciosa al inicio de sesión y cada 15 minutos

7.3 — Reactive Search

Agente puede buscar web durante la conversación
Tool: search_web(query: str) → str
Reactivar tools en Live sessions (requiere AUDIO-01 resuelto primero)
Resultados inyectados como System Hints, no como texto directo

7.4 — Initiative Protocol

Agente habla proactivamente si detecta contexto relevante
Trigger: usuario inactivo >30s + contexto de alta relevancia
Implementar en SubconsciousMind como "proactive injection"

7.5 — Vision (Cámara)

Activar streaming de video a Gemini Live
Frontend: getUserMedia() → canvas → JPEG frames 1fps
Backend: relay de frames junto al audio stream
Agente puede ver y comentar lo que el usuario le muestra

7.6 — BLOCK_NONE Safety Settings

Habilitar BLOCK_NONE para generación procedural en SoulForge y Ritual
Solo para endpoints de creación de agentes, no para sesiones Live
Research: compatibilidad con Gemini 2.5 Flash text generation

7.7 — ARQUITECTURA-01 (Backlog Técnico)

Sincronización AgentService ↔ LocalSoulRepository
Cuando soul_repo.get_agent() no encuentra agente → buscar en JSON → registrar en SQLite
Eliminar posibilidad de agentes "fantasma"


FASE 8 — INFRAESTRUCTURA DE PRODUCCIÓN 📋
Objetivo: El motor escala.

📋 Migrar SQLite → Google Cloud Spanner (Graph)
📋 Migrar JSON filesystem → PostgreSQL o Firestore
📋 Ephemeral Tokens para auth segura cliente→Gemini
📋 Google Cloud Run deployment
📋 Firebase Auth para usuarios
📋 Monitoring y observabilidad (OpenTelemetry)
📋 Rate limiting y quota management
📋 Multi-tenant: múltiples usuarios, aislamiento de grafos


FASE 9 — DISTRITO CERO MULTI-AGENTE 📋
Objetivo: El "Caso Valorant" — 6 agentes simultáneos.

📋 Multi-agent session: hasta 6 agentes en una sesión
📋 Auction MARL: bidding algorítmico con reinforcement learning
📋 Turn overlap: agentes pueden reaccionar simultáneamente (en cola priorizada)
📋 Group dynamics: relaciones entre agentes modulan quién habla primero
📋 Screen sharing: todos los agentes ven la pantalla del usuario
📋 Emotional contagion: mood de un agente afecta a los demás
📋 Intervention protocol: agentes pueden interrumpirse entre sí


FASE 10 — ECONOMÍA Y EVOLUCIÓN 📋
Objetivo: El mundo de los agentes tiene consecuencias.

📋 Affinity decay: relaciones se enfrían sin interacción
📋 Nemesis system: agentes que se vuelven antagonistas permanentes
📋 Trait evolution: personalidad cambia matemáticamente por experiencias
📋 Social events: agentes interactúan entre sí offline (simulación)
📋 Legacy system: agentes pueden "morir" y dejar memorias a otros
📋 Factions: grupos de agentes con ideologías compartidas


FASE 11 — KIZUNA UNIVERSE 💡
Objetivo: El motor es una plataforma.

💡 SDK público para crear agentes Kizuna
💡 Marketplace de agentes (con monetización)
💡 User-generated lore y worldbuilding
💡 Cross-device: agente persiste entre móvil, desktop, wearables
💡 Kizuna as a Service (KaaS): API para terceros
💡 Community events: agentes que evolucionan con eventos globales


NOTAS DE IMPLEMENTACIÓN
Stack Actual vs Stack Objetivo (Fase 8)
ComponenteActualObjetivo Fase 8Agentes DBJSON filesystemFirestore / PostgreSQLGraph DBSQLite localGoogle Cloud SpannerCacheMemory (Redis fallback)Redis CloudAuthSin auth (dev)Firebase AuthDeployLocal uvicornCloud RunSecrets.env fileSecret ManagerAudio modelgemini-2.5-flash-native-audio-previewgemini-2.5-flash-native-audio (GA)

Roadmap actualizado: 3 de Marzo de 2026 | El Cronista