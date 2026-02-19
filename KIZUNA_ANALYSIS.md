# Kizuna Engine: Análisis de Arquitectura y Visión

Este documento analiza el estado actual de Kizuna Engine, identifica problemas críticos en la implementación y propone la arquitectura ideal para cumplir con la visión de "Motor de Encarnación Universal".

## 1. Arquitectura Actual (Estado Actual)

La arquitectura actual está diseñada como un sistema de streaming de audio full-duplex utilizando WebSockets para conectar un frontend React con un backend FastAPI que orquesta la API de Gemini Live.

### Backend (`backend/app/`)
*   **Tecnología:** Python, FastAPI, Uvicorn, `google-genai` SDK.
*   **Flujo de Datos:**
    1.  **Recepción (Client -> Gemini):** Recibe audio PCM (16kHz, 16-bit, mono) a través de WebSocket.
    2.  **Buffering:** Implementa un buffer inteligente de ~100ms (3200 bytes) antes de enviar a Gemini. Esto es crucial para balancear latencia y carga de red, evitando saturar la API con paquetes diminutos.
    3.  **Envío (Gemini -> Client):** Recibe chunks de audio y texto de Gemini en tiempo real y los reenvía al cliente mediante un protocolo JSON personalizado (`{'type': 'audio', ...}`, `{'type': 'turn_complete'}`).
*   **Gestión de Conexión:** Utiliza `asyncio.TaskGroup` para manejar tareas de envío y recepción simultáneamente, asegurando que la desconexión en un sentido cierre limpiamente ambos lados.
*   **Modelo:** Configurado para usar `gemini-2.5-flash-native-audio-preview-12-2025`.

### Frontend (`frontend/src/`)
*   **Tecnología:** React, TypeScript, Vite.
*   **Captura de Audio:** Utiliza `AudioWorklet` (`pcm-processor.js`) para procesar audio crudo (PCM 16-bit) directamente en un hilo separado, evitando bloqueos en la UI.
*   **Gestión de Estado:** El hook `useLiveAPI` mantiene referencias persistentes (`useRef`) a los contextos de audio y sockets para evitar reconexiones innecesarias durante re-renderizados de React.
*   **Estrategia de Conexión:** Implementa una filosofía de "Conexión Indestructible". No se desconecta automáticamente ante errores o eventos `onclose` del socket, permitiendo reconexiones o manejo manual para preservar la "presencia" de la IA.

---

## 2. Problemas Críticos y Observaciones

A pesar de una base sólida, se han identificado problemas que comprometen directamente la experiencia de "inmersión" y "presencia".

### 🔴 BUG CRÍTICO: El Bucle de Retroalimentación de Audio (Feedback Loop)
En `frontend/src/hooks/useLiveAPI.ts`, existe una conexión errónea que destruye la experiencia de usuario:

```typescript
// ERROR: Esto conecta el micrófono directamente a los altavoces
source.connect(ctx.destination);
```

**Impacto:**
1.  **Eco:** El usuario se escucha a sí mismo con latencia.
2.  **Feedback Infinito:** Si se usan altavoces, el audio del micrófono sale por los altavoces, reingresa al micrófono y crea un pitido agudo insoportable.
3.  **Ruptura de la Ilusión:** Kizuna no debería ser un espejo de voz; debería ser una entidad separada.

**Solución Inmediata:** Eliminar esta línea. El audio del micrófono solo debe ir al `Worklet` (para envío) y NO a `destination`.

### 🟠 Limitación: Ausencia de Memoria Epistémica
Actualmente, la "personalidad" de Kizuna reside únicamente en una instrucción de sistema simple ("Eres Kizuna...").
*   **Problema:** Si la sesión se reinicia, Kizuna olvida todo. No hay persistencia de hechos sobre el usuario (ej. nombre de mascotas, preferencias).
*   **Impacto:** Rompe la ilusión de una relación continua ("Isekai Inverso"). Se siente como un "NPC genérico" en lugar de un compañero único.

### 🟡 Limitación: Unimodalidad (Solo Audio)
La implementación actual solo transmite audio.
*   **Visión:** Kizuna debe "ver" el entorno para comentar sobre él (ropa, desorden, clima).
*   **Estado:** El código de WebSocket y el procesador de Gemini están preparados para texto y audio, pero no hay flujo de video implementado desde el cliente.

---

## 3. Arquitectura Propuesta (La Visión Kizuna)

Para lograr el "Motor de Encarnación Universal", la arquitectura debe evolucionar hacia un sistema multimodal con memoria persistente.

### A. Flujo de Audio Full-Duplex (Corregido)
El objetivo es una latencia total (boca-a-oído) de 400ms-600ms.

1.  **Frontend (Microphone):** `Microphone` -> `AudioContext` -> `AudioWorklet` -> `WebSocket`. **(SIN conexión a `destination`)**.
2.  **Backend (Routing):** `WebSocket` -> `Buffer (100ms)` -> `Gemini Live Session`.
3.  **Frontend (Speaker):** `WebSocket` -> `Decode Base64` -> `AudioBufferSource` -> `AudioContext.destination`.

*Nota:* La capacidad de interrupción (Barge-in) ya es posible gracias a la arquitectura full-duplex actual. Cuando el usuario habla, Gemini recibe el audio y detiene su generación actual automáticamente si se configura correctamente.

### B. Sistema de Memoria Epistémica (Deep Memory)
Para que Kizuna recuerde "tienes un gato llamado Luna" entre sesiones:

1.  **Base de Datos Vectorial (RAG):** Implementar una base de datos (como Pinecone, Weaviate o incluso un JSON local para empezar) que almacene "hechos" extraídos de conversaciones anteriores.
2.  **Inyección de Contexto:** Al iniciar una sesión (`GeminiLiveService.connect`), consultar la base de datos por hechos relevantes e inyectarlos en el `system_instruction` o como un mensaje inicial invisible ("Recuerda: El usuario tiene un gato llamado Luna").
3.  **Extracción de Memorias:** Un proceso secundario (o un prompt específico al final de la sesión) que analice la conversación y extraiga nuevos hechos para guardarlos.

### C. Percepción Multimodal (Visión)
Para que Kizuna "vea":

1.  **Captura de Video:** El frontend debe capturar frames de video (ej. 1 frame cada 1-2 segundos) usando un `Canvas` oculto y `canvas.toDataURL()`.
2.  **Envío por WebSocket:** Enviar estos frames como mensajes JSON (`{ type: "image", data: "base64..." }`) por el mismo WebSocket existente.
3.  **Integración Backend:** El backend debe recibir estos mensajes y enviarlos a la sesión de Gemini Live usando `session.send(input={"data": image_bytes, "mime_type": "image/jpeg"})`.

### D. Conexión "Indestructible"
Mantener y reforzar la lógica actual donde la conexión **nunca** se cierra por iniciativa del servidor, salvo error fatal irrecuperable. La IA debe esperar pacientemente en silencio (como una persona en la habitación) hasta que el usuario decida interactuar o cerrar la "invocación".
