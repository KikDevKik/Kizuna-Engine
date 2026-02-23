# Kizuna Engine: Análisis de Arquitectura y Visión

Este documento analiza el estado actual de Kizuna Engine, identifica problemas críticos en la implementación y propone la arquitectura ideal para cumplir con la visión de "Motor de Encarnación Universal".

## 1. Arquitectura Actual (Estado Actual)
La arquitectura actual está diseñada como un sistema de streaming multimodal (Audio + Video) full-duplex utilizando WebSockets para conectar un frontend React con un backend FastAPI que orquesta la API de Gemini Live.

### Backend (backend/app/)
- **Tecnología**: Python, FastAPI, Uvicorn, google-genai SDK.
- **Orquestación de Sesión**: La lógica WebSocket es gestionada por `SessionManager`, utilizando `asyncio.TaskGroup` para gestionar simultáneamente:
    - `audio_session.send_to_gemini`: Streaming de audio upstream.
    - `audio_session.receive_from_gemini`: Streaming downstream.
    - `subconscious_mind.start`: Análisis paralelo de sentimientos.
- **Flujo de Datos**:
    1. **Recepción Multimodal (Client -> Gemini)**:
       - **Audio**: Recibe audio PCM (16kHz, 16-bit, mono) con buffering de ~100ms.
       - **Visión**: Recibe frames JPEG base64 (max 480px, calidad 0.5) para análisis visual.
       - **Bio-Feedback**: Endpoint `/api/bio/submit` ingesta BPM para modular hints del sistema (vía `SubconsciousMind`).
       - **True Echo Protocol**: Recibe transcripciones nativas del navegador (`native_transcript`) para evitar re-procesamiento de speech-to-text en el backend.
    2. **Envío (Gemini -> Client)**: Recibe chunks de audio y texto de Gemini en tiempo real y los reenvía al cliente mediante un protocolo JSON personalizado (`{'type': 'audio', ...}`, `{'type': 'turn_complete'}`).
- **Model Waterfall**: Implementa estrategia de fallback (Cascada) en `SubconsciousMind` y `RitualService`. Si un modelo devuelve error 429 (Rate Limit), el sistema intenta automáticamente con el siguiente en la lista configurada (`settings.MODEL_SUBCONSCIOUS`), asegurando continuidad operativa.
- **Memoria y Mente**:
    - **Local Vector Parity**: `LocalSoulRepository` implementa búsqueda semántica utilizando similitud coseno y `embedding_service`, permitiendo RAG real sin dependencias externas pesadas.
    - **RAG (Soul Assembler)**: Inyecta episodios recientes (`MemoryEpisodeNode`) y el último sueño (`DreamNode`) en el prompt del sistema al iniciar sesión.
    - **Ontological Decoupling**: La configuración del sistema y matrices de afinidad se cargan dinámicamente desde `SystemConfigNode` en el grafo, desacoplando datos de código.
    - **Sleep Manager**: Gestiona el ciclo de sueño REM. Persiste la intención de consolidación en Redis (`sleep_intent:*`) y asegura que las memorias se guarden incluso ante reinicios o desconexiones, con un timeout de shutdown de 10s.

### Frontend (frontend/src/)
- **Tecnología**: React, TypeScript, Vite.
- **Captura de Audio**: Utiliza AudioWorklet (`pcm-processor.js`) para procesar audio crudo (PCM 16-bit) directamente en un hilo separado.
- **True Echo Protocol**: `useLiveAPI.ts` implementa `SpeechRecognition` nativo del navegador para capturar lo que el usuario dice y enviarlo como texto, reduciendo latencia y costes.
- **Gestión de Audio (AudioStreamManager)**:
    - **Jitter Buffer Dinámico**: Implementa un buffer elástico (objetivo 60ms). Si la latencia sube (>200ms), acelera la reproducción (1.05x) para alcanzar el tiempo real sin cortes bruscos ("catch-up").
- **Visión (UseVision)**: Hook `useVision` permite capturar frames de cámara o pantalla, con throttling agresivo para no saturar el WebSocket.
- **Estrategia de Conexión**: Implementa una filosofía de "Conexión Indestructible". No se desconecta automáticamente ante errores o eventos `onclose` del socket.

--------------------------------------------------------------------------------

## 2. Historial de Problemas y Correcciones

### ✅ SOLUCIONADO: El Bucle de Retroalimentación de Audio (Feedback Loop)
Anteriormente, en `frontend/src/hooks/useLiveAPI.ts`, existía una conexión errónea que conectaba el micrófono directamente a los altavoces: `source.connect(ctx.destination);`
**Estado Actual**: El problema ha sido corregido. La línea problemática fue eliminada, asegurando que el audio del micrófono solo se envíe al AudioWorklet para su transmisión al backend.

### ✅ SOLUCIONADO: Limitación Unimodal (Visión Implementada)
Originalmente, Kizuna solo transmitía audio.
**Estado Actual**: Se ha implementado el pipeline de visión. El frontend captura frames (JPEG comprimido) y el backend (`audio_session.py`) los enruta a la sesión multimodal de Gemini, permitiendo a la IA "ver" y comentar sobre el entorno.

### ✅ SOLUCIONADO: Memoria Epistémica Híbrida (Local Vector Parity)
Originalmente una simulación simple.
**Estado Actual**: Se ha implementado `LocalSoulRepository` con soporte completo para vectores (embeddings) y búsqueda por similitud de coseno.
- **Implementación Actual**: Grafo JSON + Embeddings locales.
- **Persistencia**: `SleepManager` y `Redis` aseguran la consolidación.

--------------------------------------------------------------------------------

## 3. Arquitectura Propuesta (La Visión Kizuna)
Para lograr el "Motor de Encarnación Universal", la arquitectura debe evolucionar hacia un sistema multimodal con memoria persistente distribuida.

### A. Flujo de Audio Full-Duplex (✅ IMPLEMENTADO)
El sistema actual cumple con el objetivo de latencia total (boca-a-oído) de 400ms-600ms.
1. **Frontend (Microphone)**: Microphone -> AudioContext -> AudioWorklet -> WebSocket.
2. **Backend (Routing)**: WebSocket -> Buffer (100ms) -> Gemini Live Session.
3. **Frontend (Speaker)**: WebSocket -> Decode Base64 -> Jitter Buffer (Dynamic) -> AudioContext.destination.

### B. Sistema de Memoria Epistémica (Deep Memory) - (✅ IMPLEMENTADO - FASE LOCAL)
La infraestructura para que Kizuna recuerde hechos está activa con capacidades vectoriales:
1. **RAG Contextual**: `SoulAssembler` recupera episodios recientes y sueños pasados usando búsqueda semántica.
2. **Mente Subconsciente**: `SubconsciousMind` analiza en segundo plano usando un "Waterfall" de modelos para robustez.
3. **Bio-Feedback**: Ingesta de señales biológicas (BPM) para modular la respuesta emocional en tiempo real.

### C. Percepción Multimodal (Visión) (✅ IMPLEMENTADO)
Para que Kizuna "vea":
1. **Captura de Video**: El frontend captura frames (cámara o pantalla).
2. **Envío por WebSocket**: Mensajes JSON `{ "type": "image", ... }`.
3. **Integración Backend**: `session.send(input={"data": image_bytes, "mime_type": "image/jpeg"})`.

### D. Conexión "Indestructible" (✅ IMPLEMENTADO)
La lógica actual asegura que la conexión nunca se cierra por iniciativa del servidor, salvo error fatal irrecuperable. La IA espera pacientemente en silencio.
