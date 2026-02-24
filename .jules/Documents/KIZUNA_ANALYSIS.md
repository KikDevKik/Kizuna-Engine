# Kizuna Engine: Análisis de Arquitectura y Visión

Este documento analiza el estado actual de Kizuna Engine, identifica problemas críticos en la implementación y describe la arquitectura de la "Simulación de Realidad Multi-Agente".

## 1. Arquitectura Actual (Estado Actual)
La arquitectura actual es un sistema de simulación autónoma respaldado por un Grafo de Conocimiento Temporal (GraphRAG), operando sobre un stream multimodal full-duplex y un Event Loop asíncrono blindado.

### Backend (backend/app/)
- **Tecnología**: Python, FastAPI, Uvicorn, google-genai SDK.
- **Orquestación de Sesión**: La lógica WebSocket es gestionada por `SessionManager`, utilizando `asyncio.TaskGroup` para gestionar simultáneamente:
    - `audio_session.send_to_gemini`: Streaming de audio upstream.
    - `audio_session.receive_from_gemini`: Streaming downstream.
    - `subconscious_mind.start`: Análisis paralelo de sentimientos.
- **Estabilidad (The Bastion)**:
    - **Asyncio Shield**: `SleepManager` protege la escritura de memorias (`repository.save_episode`) con `asyncio.shield()`, asegurando integridad de datos ante desconexiones.
    - **Deadlock Prevention**: `LocalSoulRepository` utiliza un patrón de "Unsafe Methods" (`_get_resonance_unsafe`) y "Split-Lock Strategies" para evitar bloqueos recursivos.
- **Flujo de Datos**:
    1. **Recepción Multimodal (Client -> Gemini)**:
       - **Audio**: Recibe audio PCM (16kHz, 16-bit, mono) con buffering de ~100ms.
       - **Visión**: Recibe frames JPEG base64 (max 480px, calidad 0.5) para análisis visual.
       - **Bio-Feedback**: Endpoint `/api/bio/submit` ingesta BPM para modular hints del sistema (vía `SubconsciousMind`).
       - **True Echo Protocol**: Recibe transcripciones nativas del navegador (`native_transcript`) para evitar re-procesamiento de speech-to-text en el backend.
    2. **Envío (Gemini -> Client)**: Recibe chunks de audio y texto de Gemini en tiempo real y los reenvía al cliente mediante un protocolo JSON personalizado (`{'type': 'audio', ...}`, `{'type': 'turn_complete'}`).
- **Model Waterfall**: Implementa estrategia de fallback (Cascada) en `SubconsciousMind` y `RitualService`. Si un modelo devuelve error 429 (Rate Limit), el sistema intenta automáticamente con el siguiente en la lista configurada (`settings.MODEL_SUBCONSCIOUS`), asegurando continuidad operativa.
- **Memoria y Mente (The Soul Architect)**:
    - **Local Vector Parity**: `LocalSoulRepository` implementa búsqueda semántica utilizando similitud coseno y `embedding_service`, permitiendo RAG real sin dependencias externas pesadas.
    - **RAG (Soul Assembler)**: Inyecta episodios recientes (`MemoryEpisodeNode`), eventos de mundo (`CollectiveEventNode`) y el último sueño (`DreamNode`) en el prompt del sistema.
    - **Semantic Bridge**: `SubconsciousMind` detecta similitudes semánticas en tiempo real e inyecta "Flashbacks" (`SYSTEM_HINT`) en la conversación.
    - **Sleep Manager**: Gestiona el ciclo de sueño REM. Persiste la intención de consolidación en Redis (`sleep_intent:*`) con un sistema de "Rescue Protocol" en background.

### Frontend (frontend/src/) - The Forgemaster
- **Tecnología**: React, TypeScript, Vite.
- **Captura de Audio**: Utiliza AudioWorklet (`pcm-processor.js`) para procesar audio crudo (PCM 16-bit) directamente en un hilo separado.
- **True Echo Protocol**: `useLiveAPI.ts` implementa `SpeechRecognition` nativo del navegador para capturar lo que el usuario dice y enviarlo como texto, reduciendo latencia y costes.
- **Gestión de Audio (AudioStreamManager)**:
    - **Jitter Buffer Dinámico**: Implementa un buffer elástico (objetivo 60ms). Si la latencia sube (>200ms), acelera la reproducción (1.05x) para alcanzar el tiempo real sin cortes bruscos ("catch-up").
- **Visión (UseVision)**: Hook `useVision` permite capturar frames de cámara o pantalla, con throttling agresivo para no saturar el WebSocket.
- **Estrategia de Conexión**: Implementa una filosofía de "Conexión Indestructible" y "Silent Grace". No se muestra error al usuario ante caídas momentáneas.

--------------------------------------------------------------------------------

## 2. Historial de Problemas y Correcciones

### ✅ SOLUCIONADO: El Bucle de Retroalimentación de Audio (Feedback Loop)
Anteriormente, en `frontend/src/hooks/useLiveAPI.ts`, existía una conexión errónea que conectaba el micrófono directamente a los altavoces: `source.connect(ctx.destination);`
**Estado Actual**: El problema ha sido corregido. La línea problemática fue eliminada.

### ✅ SOLUCIONADO: Limitación Unimodal (Visión Implementada)
Originalmente, Kizuna solo transmitía audio.
**Estado Actual**: Se ha implementado el pipeline de visión. El frontend captura frames (JPEG comprimido) y el backend (`audio_session.py`) los enruta a la sesión multimodal de Gemini.

### ✅ SOLUCIONADO: Memoria Epistémica Híbrida (Local Vector Parity)
Originalmente una simulación simple.
**Estado Actual**: Se ha implementado `LocalSoulRepository` con soporte completo para vectores (embeddings) y búsqueda por similitud de coseno.

--------------------------------------------------------------------------------

## 3. Arquitectura Base (Implementada)
El sistema ha alcanzado el estado de "Motor de Encarnación Universal".

### A. Flujo de Audio Full-Duplex (✅ IMPLEMENTADO)
El sistema actual cumple con el objetivo de latencia total (boca-a-oído) de 400ms-600ms.

### B. Sistema de Memoria Epistémica (Deep Memory) - (✅ IMPLEMENTADO)
La infraestructura para que Kizuna recuerde hechos está activa con capacidades vectoriales:
1. **RAG Contextual**: `SoulAssembler` recupera episodios recientes y sueños pasados.
2. **Mente Subconsciente**: `SubconsciousMind` analiza en segundo plano usando un "Waterfall" de modelos.

### C. Percepción Multimodal (Visión) (✅ IMPLEMENTADO)
Para que Kizuna "vea":
1. **Captura de Video**: El frontend captura frames (cámara o pantalla).
2. **Envío por WebSocket**: Mensajes JSON `{ "type": "image", ... }`.
3. **Integración Backend**: `session.send(input={"data": image_bytes, "mime_type": "image/jpeg"})`.

--------------------------------------------------------------------------------

## 4. La Nueva Realidad: Simulación Multi-Agente (Temporal Knowledge Graph)
El sistema ha evolucionado de un chatbot multimodal a una **Simulación de Realidad Autónoma** gestionada por 6 Titanes arquitectónicos.

### A. Temporal Knowledge Graph (El Cerebro)
La estructura de datos central ya no es una lista de mensajes, sino un Grafo Temporal (`backend/app/models/graph.py`):
- **Nodos**: `UserNode`, `AgentNode` (con `traits` y `social_battery`), `MemoryEpisodeNode` (recuerdos), `DreamNode` (síntesis onírica), `SystemConfigNode` (directivas globales), `CollectiveEventNode` (eventos de mundo).
- **Aristas**: `ResonanceEdge` (afinidad emocional dinámica), `KnowsEdge` (hechos verificados), `ShadowEdge` (relación con sueños).

### B. Ciclo de Vida Autónomo & Simulación Offline
- **Vigilia**: El `Forgemaster` (Frontend/Audio) gestiona la interacción en tiempo real.
- **Reflexión**: El `Anthropologist` gestiona la "Batería Social" (Decay & Drain) y la afinidad dinámica.
- **Simulación Offline (Time-Skips)**: El `TimeSkipService` simula la vida de los agentes cuando el usuario no está (`CollectiveEventNode`), aplicando recarga de batería y decaimiento de afinidad (Curva del Olvido de Ebbinghaus).
- **Sueño (Consolidación)**: El `SleepManager` y `Chief Architect` consolidan memorias a largo plazo y generan sueños (`DreamNode`) que influencian la personalidad futura.

### C. Infraestructura de los 6 Titanes
La arquitectura de código respeta ahora estrictamente la división de poderes:
1. **The Forgemaster 🦾**: Frontend, Audio, Vision, WebSockets (`frontend/`, `audio_session.py`).
2. **The Chief Architect 🏗️**: Grafo Temporal, Time-Skips, Ontología (`graph.py`, `time_skip.py`).
3. **The Anthropologist 🌍**: Dinámicas Sociales, Batería Social, Límites (`subconscious.py` battery logic).
4. **The Soul Architect 🕸️**: RAG, Memorias, Sueños, Puente Semántico (`soul_assembler.py`, `subconscious.py`).
5. **The Bastion 🛡️**: Estabilidad, Seguridad, Asyncio Shield (`session_manager.py`, `sleep_manager.py`).
6. **The Chronicler 📜**: Documentación, Roadmap, Data Hygiene (`AGENTS.md`, `.jules/Documents/`).
