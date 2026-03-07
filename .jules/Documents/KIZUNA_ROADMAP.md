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

### 7.8 — Barge-in: Protocolo de Interrupción Social 📋
> Baja-Media complejidad. Backend Python + frontend Rust.
> **Bug confirmado en pruebas:** el usuario no puede interrumpir al agente mientras habla.

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

### 7.9 — Presencia Persistente en Escritorio (System Tray) 📋
> Baja complejidad. Puramente aditivo en Tauri. El modelo Discord.
- 📋 `tauri-plugin-tray` — ícono persistente, app vive aunque se cierre la ventana
- 📋 `prevent_close()` + `window.hide()` — proceso persiste en background
- 📋 `tauri-plugin-global-shortcut` — Push-to-Talk global sin necesidad de foco
- 📋 `tauri-plugin-notification` — notificaciones proactivas con audio customizado
- 📋 Prerequisito del Initiative Protocol (7.4)

---

## FASE 7.X — CALIDAD DE PERSONALIDAD 📋
> Refinamiento de expresividad y naturalidad. Sin código nuevo — solo prompts.
> Aplicar antes de pruebas de usuario externas.

### 7.X.1 — The Void: Ritual más Expresivo 📋
> Solo `ritual_service.py`. Cambio de prompt.

**Problema confirmado en pruebas:** The Void hace preguntas funcionales pero predecibles.
Las preguntas suenan a formulario. Le falta provocación y capacidad de sorprender.

- 📋 Preguntas filosóficas y evocadoras — el usuario no debe sentir que llena un formulario
- 📋 The Void reacciona emocionalmente a lo que describe el usuario — si es oscuro, se
  interesa más; si es luminoso, se distancia levemente
- 📋 Menos opciones binarias ("¿A o B?") — más preguntas abiertas
- 📋 The Void puede hacer comentarios sobre lo que está emergiendo, no solo preguntar
- 📋 Máximo 2-3 intercambios antes de ofrecer crear — no alargar innecesariamente
- 📋 El lenguaje de The Void debe sentirse antiguo, extraño, no corporativo

### 7.X.2 — Habla Natural: Fin del Robotismo 📋
> Solo `soul_assembler.py`. Directivas de impredecibilidad en Static DNA.

**Problema confirmado en pruebas:** Los agentes responden de forma demasiado estructurada.
Cada respuesta parece calculada. Les falta la textura de la conversación real.

- 📋 Directiva de **impredecibilidad verbal** en el DNA de todos los agentes:
  el agente puede cambiar de tema si algo le llama la atención, interrumpirse a sí mismo,
  hacer preguntas retóricas, dejar frases incompletas
- 📋 **Muletillas y pausas** acordes al lore del personaje — no genéricas
- 📋 **Reacciones espontáneas verbalizadas**: "espera—", "eso es...", "no, no, escucha"
- 📋 Respuestas cortas cuando la situación lo pide — no siempre párrafos
- 📋 El agente no siempre tiene la respuesta — puede expresar genuina incertidumbre
- 📋 Incrementar versión Static DNA a v6 tras aplicar (forzar regeneración de cache)

### 7.X.3 — Kizuna Multilingüe 📋
> Solo `seeder.py`. Una línea de cambio.

**Problema:** Kizuna hardcodeada con solo español e inglés. Como producto global necesita
hablar con usuarios asiáticos, europeos y de otras culturas desde el día uno.

- 📋 Ampliar `known_languages` en seeder: japonés, coreano, chino mandarín, francés,
  portugués, alemán, italiano, árabe, hindi
- 📋 El Language Protocol ya maneja esto — solo es data
- 📋 Forzar regeneración de Static DNA de Kizuna (versión v6)

---

## FASE 8 — INFRAESTRUCTURA DE PRODUCCIÓN + AUDIO NATIVO 📋
**Objetivo:** El motor escala. El audio suena como Discord.

> ⚠️ DOS TRACKS PARALELOS:
> **Track A (8.1-8.7):** Cloud infrastructure — prerequisito para usuarios reales.
> **Track B (8.8-8.9):** Audio nativo Rust — prerequisito para calidad de producto.
> Ambos tracks deben completarse antes del lanzamiento.

### 8.1 — Migrar SQLite → Google Cloud Spanner 📋
- 📋 Reemplazar LocalSoulRepository con Spanner Graph
- 📋 Migrar edges, nodes, KizunaChronicle
- 📋 GQL queries para grafo de relaciones

### 8.2 — Migrar JSON → Firestore / PostgreSQL 📋
- 📋 Reemplazar AgentService JSON filesystem
- 📋 get_or_sync_agent() se vuelve obsoleto — eliminar

### 8.3 — Cloud Run Deployment 📋
- 📋 Dockerfile para backend FastAPI
- 📋 Session affinity para WebSockets persistentes
- 📋 ~80 conexiones simultáneas por instancia

### 8.4 — Firebase Auth 📋
- 📋 Autenticación real (reemplazar guest_user)
- 📋 Ephemeral Tokens para auth segura cliente→Gemini
- 📋 Aislamiento multi-tenant por usuario

### 8.5 — Monitoring y Observabilidad 📋
- 📋 OpenTelemetry: trazas distribuidas
- 📋 Métricas: TTFB, errores de sesión, tokens consumidos

### 8.6 — Rate Limiting 📋
- 📋 Por usuario en REST y WebSocket
- 📋 Quota management para Gemini API

### 8.7 — Multi-tenant 📋
- 📋 KizunaChronicle por usuario real (no guest_user)
- 📋 Grafos de relaciones aislados por usuario

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

### Próximos pasos inmediatos (en orden)

1. **7.8 — Barge-in** — el agente no para cuando el usuario habla encima
2. **7.X.1 — The Void** — mejorar calidad del Ritual (solo prompt)
3. **7.X.2 — Habla Natural** — eliminar robotismo (solo prompt)
4. **7.X.3 — Kizuna Multilingüe** — ampliar idiomas (una línea en seeder)
5. **7.9 — System Tray** — presencia persistente desktop
6. **Fase 8** — después de pruebas de usuario externas

---

*Roadmap actualizado: 6 de Marzo de 2026 | El Cronista*