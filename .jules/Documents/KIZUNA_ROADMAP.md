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

## Fase 3: Memoria Epistémica y "Mente" (Híbrido Local/Nube)
**Objetivo**: Implementar persistencia de memoria y análisis emocional en modo local (JSON Graph) como preparación para la infraestructura Cloud Spanner.

### 1. [BACKEND] Implementar Grafo Local (✅ Hecho - Semi-Aplicado)
- **Acción**: Implementación de `LocalSoulRepository` en `backend/app/repositories/local_graph.py`.
- **Detalle**: Simulación completa de la estructura de grafos (Usuarios, Agentes, Hechos, Resonancia, Episodios) utilizando JSON local (`backend/data/graph.json`).
- **Estado**: Funcional. Permite persistencia entre reinicios del servidor local.

### 2. [BACKEND] Inyección de Contexto Dinámico (✅ Hecho)
- **Acción**: Implementación de `SoulAssembler` en `backend/app/services/soul_assembler.py`.
- **Lógica**: Al conectar, el sistema consulta el repositorio local para obtener la afinidad (`Resonance`) y construye un `system_instruction` personalizado.
- **Estado**: Implementado. Kizuna ahora reacciona diferente según el nivel de amistad acumulado.

### 3. [BACKEND] Mente Subconsciente (🚧 En Progreso)
- **Acción**: Implementación del servicio `SubconsciousMind` en `backend/app/services/subconscious.py`.
- **Lógica**: Análisis en segundo plano de las transcripciones para detectar emociones y guardar "insights" en el repositorio local.
- **Estado**: Activo en modo simulación (detecta palabras clave simples y actualiza afinidad). Pendiente integración completa con LLM para análisis profundo.

--------------------------------------------------------------------------------

Fase 4: Refinamiento del "Alma" (Arquitectura de Almas Dinámicas)
Objetivo: Eliminar el hardcodeo de personalidades e implementar un ecosistema procedural donde cada agente posee un ADN base y evoluciona orgánicamente su relación con el usuario global.

1. [BACKEND] Ensamblador de Almas y Plantillas (Core JSON)
Acción: Eliminar el system_instruction estático. Implementar la lógica de ensamblaje dinámico (assemble_soul(agent_id)) antes de inyectarlo en Gemini Live.

Motor de Identidad: El prompt final es una ecuación en tiempo de ejecución: [ADN Base] + [Modificador de Afinidad] + [Memoria Epistémica].

Plantillas Base (data/agents/):

Kizuna (El Núcleo Roto): Arquetipo neutral-frío y analítico. Su afinidad crece si el usuario le enseña conceptos estructurados o la alimenta con conocimiento.

Aegis (El Supervisor Estricto): Arquetipo pragmático/militar. Inicia con afinidad negativa o desconfianza. Exige precisión técnica y penaliza la mediocridad. Gana respeto mediante el trabajo duro del usuario.

Template_Custom.json: Plantilla en blanco estandarizada para la instanciación procedural.

2. [FRONTEND] Centro de Comando y Forja de Almas
Acción: Construir el ecosistema visual de selección y creación, eliminando por completo la sensación de "herramienta de debug".

Componentes Críticos:

Agent Roster: Carrusel 3D o selector dinámico que carga la lista de agentes disponibles leyendo el backend.

Soul Forge (La Forja): Un modal/UI dedicado donde cualquier usuario puede crear un agente nuevo inyectando un Nombre, un Rol base (Lore) y una imagen de referencia.

Estética Inmersiva: Diseño "Dark Water", uso de geometría agresiva (clip-path) y limpieza total de logs de consola en el DOM.

--------------------------------------------------------------------------------

## Fase 5: Ascensión a la Nube (Preparación Final)
**Objetivo**: Migrar la infraestructura local validada a Google Cloud Platform para producción masiva.

### 1. [CLOUD] Migración a Spanner (Pendiente)
- **Acción**: Reemplazar `LocalSoulRepository` con `SpannerSoulRepository`.
- **Estrategia**: La interfaz `SoulRepository` abstrae la implementación subyacente, permitiendo un cambio transparente ("Lift-and-Shift") de JSON a Spanner SQL/Graph.
- **Trigger**: Se ejecutará cuando el modelo de datos local esté estable y validado.

### 2. [CLOUD] Despliegue de Redis (Pendiente)
- **Acción**: Activar caché distribuida para sesiones de usuario y ensamblaje de almas en alta concurrencia.
