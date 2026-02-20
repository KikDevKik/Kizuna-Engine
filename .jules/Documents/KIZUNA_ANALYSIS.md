# Kizuna Engine: Análisis de Arquitectura y Visión

Este documento analiza el estado actual de Kizuna Engine, identifica problemas críticos en la implementación y propone la arquitectura ideal para cumplir con la visión de "Motor de Encarnación Universal".

## 1. Arquitectura Actual (Estado Actual)
La arquitectura actual está diseñada como un sistema de streaming de audio full-duplex utilizando WebSockets para conectar un frontend React con un backend FastAPI que orquesta la API de Gemini Live.

### Backend (backend/app/)
- **Tecnología**: Python, FastAPI, Uvicorn, google-genai SDK.
- **Flujo de Datos**:
    1. **Recepción (Client -> Gemini)**: Recibe audio PCM (16kHz, 16-bit, mono) a través de WebSocket.
    2. **Buffering**: Implementa un buffer inteligente de ~100ms (3200 bytes) antes de enviar a Gemini. Esto es crucial para balancear latencia y carga de red, evitando saturar la API con paquetes diminutos.
    3. **Envío (Gemini -> Client)**: Recibe chunks de audio y texto de Gemini en tiempo real y los reenvía al cliente mediante un protocolo JSON personalizado (`{'type': 'audio', ...}`, `{'type': 'turn_complete'}`).
- **Gestión de Conexión**: Utiliza `asyncio.TaskGroup` para manejar tareas de envío y recepción simultáneamente, asegurando que la desconexión en un sentido cierre limpiamente ambos lados.
- **Modelo**: Configurado para usar `gemini-2.5-flash-native-audio-preview-12-2025`.
- **Memoria y Mente**: Implementación Híbrida Local (`LocalSoulRepository`) activa. Simula la estructura de grafos de Google Cloud Spanner utilizando JSON local para persistencia de episodios, hechos y resonancia emocional.

### Frontend (frontend/src/)
- **Tecnología**: React, TypeScript, Vite.
- **Captura de Audio**: Utiliza AudioWorklet (`pcm-processor.js`) para procesar audio crudo (PCM 16-bit) directamente en un hilo separado, evitando bloqueos en la UI.
- **Gestión de Estado**: El hook `useLiveAPI` mantiene referencias persistentes (`useRef`) a los contextos de audio y sockets para evitar reconexiones innecesarias durante re-renderizados de React.
- **Estrategia de Conexión**: Implementa una filosofía de "Conexión Indestructible". No se desconecta automáticamente ante errores o eventos `onclose` del socket, permitiendo reconexiones o manejo manual para preservar la "presencia" de la IA.

--------------------------------------------------------------------------------

## 2. Historial de Problemas y Correcciones

### ✅ SOLUCIONADO: El Bucle de Retroalimentación de Audio (Feedback Loop)
Anteriormente, en `frontend/src/hooks/useLiveAPI.ts`, existía una conexión errónea que conectaba el micrófono directamente a los altavoces: `source.connect(ctx.destination);`
**Estado Actual**: El problema ha sido corregido. La línea problemática fue eliminada, asegurando que el audio del micrófono solo se envíe al AudioWorklet para su transmisión al backend, evitando el eco y el feedback infinito.

### 🟡 Estado de Transición: Memoria Epistémica Híbrida (Local/Nube)
Originalmente, Kizuna carecía de memoria a largo plazo. Actualmente, se ha implementado una solución **semi-aplicada** que sienta las bases para el futuro RAG en la nube.
- **Implementación Actual**: Se utiliza `LocalSoulRepository` (basado en JSON) para simular la estructura de datos de un Grafo de Conocimiento (Usuarios, Agentes, Episodios, Hechos, Resonancia).
- **Mente Subconsciente**: El servicio `SubconsciousMind` opera en segundo plano analizando transcripciones para detectar emociones y generar "insights" que se guardan localmente.
- **Estrategia**: El sistema funciona 100% local para desarrollo ágil, pero la arquitectura (`SoulRepository` interface) está diseñada para cambiar a **Google Cloud Spanner** sin modificar la lógica de negocio cuando el proyecto entre en fase de producción.
- **Impacto**: Kizuna ya puede "recordar" interacciones pasadas y ajustar su personalidad dinámicamente (`SoulAssembler`) basado en la afinidad acumulada localmente.

### 🟡 Limitación: Unimodalidad (Solo Audio)
La implementación actual solo transmite audio.
- **Visión**: Kizuna debe "ver" el entorno para comentar sobre él (ropa, desorden, clima).
- **Estado**: El código de WebSocket y el procesador de Gemini están preparados para texto y audio, pero no hay flujo de video implementado desde el cliente.

--------------------------------------------------------------------------------

## 3. Arquitectura Propuesta (La Visión Kizuna)
Para lograr el "Motor de Encarnación Universal", la arquitectura debe evolucionar hacia un sistema multimodal con memoria persistente distribuida.

### A. Flujo de Audio Full-Duplex (✅ IMPLEMENTADO)
El sistema actual cumple con el objetivo de latencia total (boca-a-oído) de 400ms-600ms.
1. **Frontend (Microphone)**: Microphone -> AudioContext -> AudioWorklet -> WebSocket. (SIN conexión a destination).
2. **Backend (Routing)**: WebSocket -> Buffer (100ms) -> Gemini Live Session.
3. **Frontend (Speaker)**: WebSocket -> Decode Base64 -> AudioBufferSource -> AudioContext.destination.
*Nota: La capacidad de interrupción (Barge-in) es posible gracias a la arquitectura full-duplex.*

### B. Sistema de Memoria Epistémica (Deep Memory) - (🔄 SEMI-APLICADO)
La infraestructura para que Kizuna recuerde hechos está activa en modo Local:
1. **Base de Datos Vectorial (RAG)**: Actualmente implementada como `LocalSoulRepository` (JSON). Esta estructura espejo permite validar el modelo de datos (Grafo) antes de la migración final a Google Cloud Spanner.
2. **Inyección de Contexto**: Al iniciar una sesión, `SoulAssembler` consulta el repositorio local para construir un `system_instruction` único basado en la `Resonance` (afinidad) y los hechos recordados.
3. **Mente Subconsciente**: Un proceso secundario (`SubconsciousMind`) analiza la conversación en tiempo real (simulado localmente) para extraer nuevos hechos y emociones, guardándolos en el JSON local para futuras sesiones.

### C. Percepción Multimodal (Visión)
Para que Kizuna "vea":
1. **Captura de Video**: El frontend debe capturar frames de video (ej. 1 frame cada 1-2 segundos) usando un Canvas oculto y `canvas.toDataURL()`.
2. **Envío por WebSocket**: Enviar estos frames como mensajes JSON (`{ type: "image", data: "base64..." }`) por el mismo WebSocket existente.
3. **Integración Backend**: El backend debe recibir estos mensajes y enviarlos a la sesión de Gemini Live usando `session.send(input={"data": image_bytes, "mime_type": "image/jpeg"})`.

### D. Conexión "Indestructible" (✅ IMPLEMENTADO)
La lógica actual asegura que la conexión nunca se cierra por iniciativa del servidor, salvo error fatal irrecuperable. La IA espera pacientemente en silencio (como una persona en la habitación) hasta que el usuario decida interactuar o cerrar la "invocación".
