# Roadmap de Implementación: Kizuna Engine

Este documento detalla los pasos secuenciales para transformar la implementación actual en el "Motor de Encarnación Universal".

--------------------------------------------------------------------------------

## Fase 1: Estabilización Inmediata [COMPLETADO]
**Objetivo**: Corregir errores críticos que rompen la inmersión y asegurar una base sólida para la comunicación bidireccional.

### 1. [FRONTEND] Reparar Feedback Loop de Audio (✅ Hecho)
- **Acción**: Editar `frontend/src/hooks/useLiveAPI.ts`.
- **Detalle**: Eliminar la línea `source.connect(ctx.destination)` en la configuración del micrófono.
- **Estado**: Solucionado.

### 2. [BACKEND] Verificar Configuración de Latencia (✅ Hecho)
- **Acción**: Confirmar que el buffer de audio en `backend/app/main.py` se mantenga en ~100ms (3200 bytes).
- **Estado**: Verificado.

### 3. [GENERAL] Prueba de Estrés de Conexión "Indestructible" (✅ Hecho)
- **Acción**: Simular silencios largos (minutos) y ruidos repentinos.
- **Estado**: Implementado.

--------------------------------------------------------------------------------

## Fase 2: Percepción Multimodal (La Vista de Kizuna) [COMPLETADO]
**Objetivo**: Permitir que Kizuna "vea" el mundo del usuario para comentar sobre su entorno (ropa, habitación, clima).

### 1. [FRONTEND] Implementar Captura de Video (✅ Hecho)
- **Acción**: Añadir un elemento `<video>` oculto y un `<canvas>` en el componente principal.
- **Lógica**: Hook `useVision` captura frames de cámara o pantalla.
- **Formato**: JPEG base64 (max 480px) con throttling para eficiencia.

### 2. [FRONTEND] Enviar Frames por WebSocket (✅ Hecho)
- **Acción**: Modificar el bucle de envío en `useLiveAPI.ts` / `useVision.ts`.
- **Protocolo**: Enviar mensajes JSON: `{ "type": "image", "data": "base64_string..." }`.

### 3. [BACKEND] Procesar Imágenes (✅ Hecho)
- **Acción**: Actualizar `backend/app/services/audio_session.py`.
- **Lógica**: Detectar mensajes de imagen y enrutarlos a la sesión Gemini con `mime_type: image/jpeg`.

--------------------------------------------------------------------------------

## Fase 3: Memoria Epistémica y "Mente" (Híbrido Local/Nube) [COMPLETADO]
**Objetivo**: Implementar persistencia de memoria y análisis emocional en modo local (JSON Graph) como preparación para la infraestructura Cloud Spanner.

### 1. [BACKEND] Implementar Grafo Local (✅ Hecho)
- **Acción**: Implementación de `LocalSoulRepository`.
- **Detalle**: Estructura de grafos completa (Usuarios, Agentes, Hechos, Resonancia, Episodios) persistida en JSON local.

### 2. [BACKEND] Inyección de Contexto Dinámico (✅ Hecho)
- **Acción**: Implementación de `SoulAssembler`.
- **Lógica**: Construcción dinámica del system prompt basado en afinidad y episodios recientes.

### 3. [BACKEND] Mente Subconsciente y Bio-Feedback (✅ Hecho)
- **Acción**: Implementación de `SubconsciousMind`.
- **Lógica**:
    - **Análisis**: Proceso en segundo plano para detectar emociones y generar "Insights".
    - **Model Waterfall**: Estrategia de fallback automática ante errores 429.
    - **Bio-Feedback**: Ingesta de señales BPM para modular la respuesta del sistema.

--------------------------------------------------------------------------------

## Fase 4: Refinamiento del "Alma" (Arquitectura de Almas Dinámicas) [COMPLETADO]
**Objetivo**: Eliminar el hardcodeo de personalidades e implementar un ecosistema procedural.

### 1. [BACKEND] Ensamblador de Almas y Plantillas (✅ Hecho)
- **Acción**: Eliminar el system_instruction estático.
- **Lógica**: Motor de Identidad = [ADN Base] + [Modificador de Afinidad] + [Memoria Epistémica].
- **Estado**: `SoulAssembler` completamente operativo.

### 2. [FRONTEND] Centro de Comando y Forja de Almas (✅ Hecho)
- **Acción**: Construir el ecosistema visual de selección y creación.
- **Componentes**: `AgentRoster` (Carrusel) y `SoulForge` (Modal de creación).
- **Estética**: Implementación total del diseño "Dark Water".

### 3. [BACKEND] Ciclo de Sueño REM (✅ Hecho)
- **Acción**: Implementar `SleepManager` para consolidación de memoria.
- **Lógica**: Debounce pattern para guardar recuerdos al desconectar.
- **Persistencia**: Uso de Redis (`sleep_intent`) para asegurar integridad de datos entre reinicios.

--------------------------------------------------------------------------------

## Fase 5: Ascensión a la Nube (En Foco Actual)
**Objetivo**: Migrar la infraestructura local validada a Google Cloud Platform para producción masiva.

### 1. [CLOUD] Migración a Spanner (Pendiente)
- **Acción**: Reemplazar `LocalSoulRepository` con `SpannerSoulRepository`.
- **Estrategia**: La interfaz `SoulRepository` abstrae la implementación subyacente.

### 2. [CLOUD] Despliegue de Redis (Pendiente)
- **Acción**: Activar caché distribuida en entorno de producción (GCP Memorystore).

--------------------------------------------------------------------------------

## Fase 6: Refinamiento y Memoria Profunda (✅ COMPLETADO)
**Objetivo**: Convertir el prototipo en un motor de producción robusto y con memoria semántica real.

### 1. [BACKEND] Refactorización de Sesión (✅ Hecho)
- **Acción**: Migrar la lógica de WebSocket inline en `main.py` a una clase dedicada `SessionManager`.
- **Beneficio**: Mejor testabilidad y modularidad del ciclo de vida de la conexión.

### 2. [BACKEND] RAG con Embeddings (Local Vector Parity) (✅ Hecho)
- **Acción**: Implementar búsqueda vectorial real en `LocalSoulRepository` usando `embedding.py` y similitud coseno.
- **Beneficio**: Reemplazar la búsqueda por palabras clave en `get_relevant_facts` con búsqueda semántica.

### 3. [BACKEND] Desacople Ontológico (✅ Hecho)
- **Acción**: Implementar `SystemConfigNode` en el grafo para almacenar configuración y directivas.
- **Beneficio**: Permite ajustar el comportamiento del sistema sin tocar código.

### 4. [FRONTEND] True Echo Protocol (✅ Hecho)
- **Acción**: Implementar `SpeechRecognition` nativo en `useLiveAPI.ts`.
- **Beneficio**: Reduce latencia de transcripción y mejora precisión al usar el modelo del dispositivo.

### 5. [FRONTEND] Optimización de Audio (Pendiente)
- **Acción**: Refinar el algoritmo de Jitter Buffer en `AudioStreamManager.ts` para manejar mejor redes inestables (packet loss concealment).
