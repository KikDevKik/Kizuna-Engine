# Roadmap de Implementación: Kizuna Engine

Este documento detalla los pasos secuenciales para transformar la implementación actual en el "Motor de Encarnación Universal".

--------------------------------------------------------------------------------

## Fase 1: Estabilización Inmediata [COMPLETADO]
**Objetivo**: Corregir errores críticos que rompen la inmersión y asegurar una base sólida para la comunicación bidireccional.

### 1. [FRONTEND] Reparar Feedback Loop de Audio (✅ Hecho)
- **Acción**: Editar `frontend/src/hooks/useLiveAPI.ts`.
- **Detalle**: Eliminar la línea `source.connect(ctx.destination)` en la configuración del micrófono.
- **Estado**: Solucionado. El audio del micrófono ya no se mezcla con la salida.

### 2. [BACKEND] Verificar Configuración de Latencia (✅ Hecho)
- **Acción**: Confirmar que el buffer de audio en `backend/app/main.py` se mantenga en ~100ms (3200 bytes).
- **Estado**: Verificado. `AUDIO_BUFFER_THRESHOLD` está configurado en 3200 bytes en `backend/app/services/audio_session.py`.

### 3. [GENERAL] Prueba de Estrés de Conexión "Indestructible" (✅ Hecho)
- **Acción**: Simular silencios largos (minutos) y ruidos repentinos.
- **Estado**: Implementado. El frontend `useLiveAPI` tiene lógica explícita para ignorar cierres automáticos y mantener objetos persistentes.

--------------------------------------------------------------------------------

## Fase 2: Percepción Multimodal (La Vista de Kizuna)
**Objetivo**: Permitir que Kizuna "vea" el mundo del usuario para comentar sobre su entorno (ropa, habitación, clima).

### 1. [FRONTEND] Implementar Captura de Video
- **Acción**: Añadir un elemento `<video>` oculto y un `<canvas>` en el componente principal.
- **Lógica**: Capturar un frame de la webcam cada 1-2 segundos.
- **Formato**: Convertir el frame a JPEG base64 de baja resolución (para no saturar el ancho de banda).

### 2. [FRONTEND] Enviar Frames por WebSocket
- **Acción**: Modificar el bucle de envío en `useLiveAPI.ts`.
- **Protocolo**: Enviar mensajes JSON: `{ "type": "image", "data": "base64_string..." }`.

### 3. [BACKEND] Procesar Imágenes
- **Acción**: Actualizar `backend/app/main.py` (`send_to_gemini`).
- **Lógica**: Detectar mensajes tipo image, decodificar si es necesario (o enviar directo si la SDK lo permite) y enviar a la sesión de Gemini con `mime_type: image/jpeg`.

--------------------------------------------------------------------------------

## Fase 3: Memoria Epistémica (La Mente de Kizuna)
**Objetivo**: Crear una persistencia de datos que permita a Kizuna recordar hechos entre sesiones.

### 1. [BACKEND] Implementar Almacén de Memoria Simple
- **Acción**: Crear un archivo `backend/app/services/memory_store.py`.
- **Inicio**: Usar un archivo JSON local (`memory.json`) como base de datos simple.
- **Estructura**: `{ "user_id": { "facts": ["Tiene un gato llamado Luna", "Le gusta el café amargo"] } }`.

### 2. [BACKEND] Inyección de Contexto al Inicio
- **Acción**: Modificar `GeminiLiveService.connect` en `backend/app/services/gemini_live.py`.
- **Lógica**: Leer `memory.json` antes de iniciar la sesión. Añadir los hechos al `system_instruction` o enviar un mensaje inicial oculto al modelo.

### 3. [BACKEND] Extracción y Guardado de Nuevas Memorias
- **Estrategia**:
    - **Opción A (Síncrona)**: Pedir a Gemini que extraiga hechos al final de la sesión (complicado si la conexión se corta).
    - **Opción B (Paralela)**: Usar una segunda llamada ligera a Gemini Flash con el historial de texto reciente para extraer hechos clave en segundo plano cada X turnos.

--------------------------------------------------------------------------------

## Fase 4: Refinamiento del "Alma" (Soul Tuning)
**Objetivo**: Ajustar la personalidad para que deje de ser un "Asistente" y sea un "Compañero".

### 1. [BACKEND] Ajuste de System Prompt
- **Acción**: Reescribir `system_instruction` en `gemini_live.py`.
- **Directivas**:
    - "No eres un asistente de IA. Eres Kizuna."
    - "No ofrezcas ayuda proactivamente a menos que sea natural."
    - "Usa un tono casual, empático y curioso."
    - "Si ves algo interesante en la cámara, coméntalo."

### 2. [FRONTEND] Interfaz Inmersiva
- **Acción**: Limpiar la UI. Eliminar botones de "Desconectar" visibles o consolas de debug.
- **Estética**: La pantalla debe ser una ventana al "mundo" de Kizuna (o minimalista), no un panel de control.
