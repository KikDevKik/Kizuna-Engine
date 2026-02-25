# Kizuna Engine: Análisis de Arquitectura y Visión

Este documento analiza el estado actual de Kizuna Engine, identifica problemas críticos en la implementación y describe la arquitectura de la "Simulación de Realidad Multi-Agente".

## 1. Arquitectura Actual (Estado Actual)
La arquitectura actual es un sistema de simulación autónoma respaldado por un Grafo de Conocimiento Temporal (GraphRAG), operando sobre un stream multimodal full-duplex y un Event Loop asíncrono blindado.

### Backend (backend/app/)
- **Tecnología**: Python, FastAPI, Uvicorn, google-genai SDK.
- **Orquestación de Sesión**: La lógica WebSocket es gestionada por `SessionManager`, utilizando `asyncio.TaskGroup` para gestionar simultáneamente:
    - `audio_session.send_to_gemini`: Streaming de audio upstream.
    - `audio_session.receive_from_gemini`: Streaming downstream.
    - `subconscious_mind.start`: Análisis paralelo de sentimientos y dinámica social.
- **Estabilidad (The Bastion)**:
    - **Asyncio Shield**: `SleepManager` protege la escritura de memorias (`repository.save_episode`) con `asyncio.shield()`, asegurando integridad de datos ante desconexiones.
    - **Deadlock Prevention**: `LocalSoulRepository` utiliza un patrón de "Unsafe Methods" (`_get_resonance_unsafe`) y "Split-Lock Strategies" para evitar bloqueos recursivos.
- **Flujo de Datos**:
    1. **Recepción Multimodal (Client -> Gemini)**:
       - **Audio**: Recibe audio PCM (16kHz, 16-bit, mono) con buffering de ~100ms.
       - **Visión**: Recibe frames JPEG base64 (max 480px, calidad 0.5) para análisis visual.
       - **Bio-Feedback**: Endpoint `/api/bio/submit` ingesta BPM para modular hints del sistema.
       - **True Echo Protocol**: Recibe transcripciones nativas del navegador para optimizar latency.
    2. **Envío (Gemini -> Client)**: Recibe chunks de audio y texto de Gemini en tiempo real.
- **Memoria y Mente (The Soul Architect)**:
    - **Local Vector Parity**: Búsqueda semántica (Cosine Similarity) sin dependencias externas.
    - **RAG (Soul Assembler)**: Inyecta episodios, eventos de mundo y sueños en el prompt.
    - **Semantic Bridge**: `SubconsciousMind` inyecta "Flashbacks" (`SYSTEM_HINT`) basados en contexto.

### Frontend (frontend/src/) - The Forgemaster
- **Tecnología**: React, TypeScript, Vite.
- **Dark Water Aesthetic**: Estética estricta (Neon/Vintage Navy) sin fondos blancos.
- **Gestión de Audio**: AudioWorklet para procesamiento PCM y Jitter Buffer dinámico.
- **Visión (UseVision)**: Throttling de 2000ms para captura de frames.
- **Conexión Indestructible**: Lógica de reconexión silenciosa ("Silent Grace").

--------------------------------------------------------------------------------

## 2. Historial de Problemas y Correcciones
*   ✅ **Feedback Loop de Audio**: Eliminado `source.connect(ctx.destination)`.
*   ✅ **Visión**: Implementada con throttling y compresión JPEG.
*   ✅ **Memoria Vectorial**: Implementada en `LocalSoulRepository`.

--------------------------------------------------------------------------------

## 3. Arquitectura Base (Implementada)
El sistema ha alcanzado el estado de "Motor de Encarnación Universal".
1.  **Full-Duplex Audio**: Latencia < 600ms.
2.  **Deep Memory**: RAG Contextual y Mente Subconsciente activos.
3.  **Percepción Multimodal**: El sistema "ve" y "escucha".

--------------------------------------------------------------------------------

## 4. La Nueva Realidad: Simulación Multi-Agente (Temporal Knowledge Graph)
El sistema ha evolucionado de un chatbot a una **Simulación de Realidad Autónoma**.

### A. Temporal Knowledge Graph (El Cerebro)
La estructura de datos es un Grafo Temporal (`backend/app/models/graph.py`):
- **Nodos**: `UserNode`, `AgentNode` (con Social Battery), `MemoryEpisodeNode`, `CollectiveEventNode`.
- **Esquema JSON-LD**: Implementado en todos los nodos (`JSONLDMixin`) para futura portabilidad (API pendiente).

### B. Ciclo de Vida Autónomo & Simulación Offline (✅ IMPLEMENTADO)
- **Vigilia**: Interacción en tiempo real (`Forgemaster`).
- **Reflexión**: Gestión de "Batería Social" y decaimiento de rasgos (`Anthropologist`).
- **Time-Skips (Saltos Temporales)**: El `TimeSkipService` simula eventos de fondo (`CollectiveEventNode`) y recarga baterías cuando el usuario no está.
- **Sueño**: Consolidación de memorias y generación de sueños (`DreamNode`).

### C. Infraestructura de los 6 Titanes
La arquitectura se rige estrictamente por los 6 Titanes (ver `AGENTS.md`):
1.  **The Forgemaster 🦾** (Frontend/IO)
2.  **The Chief Architect 🏗️** (Graph/Time/Ontology)
3.  **The Anthropologist 🌍** (Social/Traits)
4.  **The Soul Architect 🕸️** (RAG/Dreams)
5.  **The Bastion 🛡️** (Stability/Security)
6.  **The Chronicler 📜** (Docs/Lore)
