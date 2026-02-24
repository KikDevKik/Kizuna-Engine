# Roadmap de Implementación: Kizuna Engine

Este documento detalla los pasos secuenciales para transformar la implementación actual en el "Motor de Encarnación Universal".

--------------------------------------------------------------------------------

## Fase 1: Estabilización Inmediata [✅ COMPLETADO]
**Objetivo**: Corregir errores críticos y asegurar la base.
- [x] Reparar Feedback Loop de Audio (Frontend).
- [x] Verificar Configuración de Latencia (Backend).
- [x] Prueba de Estrés "Indestructible".

## Fase 2: Percepción Multimodal [✅ COMPLETADO]
**Objetivo**: Permitir que Kizuna "vea" el mundo.
- [x] Implementar Captura de Video (`useVision`).
- [x] Enviar Frames por WebSocket.
- [x] Procesar Imágenes en Backend (Gemini).

## Fase 3: Memoria Epistémica y Mente [✅ COMPLETADO]
**Objetivo**: Persistencia y análisis emocional.
- [x] Grafo Local (`LocalSoulRepository`).
- [x] Inyección de Contexto (`SoulAssembler`).
- [x] Mente Subconsciente y Bio-Feedback (`SubconsciousMind`).

## Fase 4: Refinamiento del "Alma" [✅ COMPLETADO]
**Objetivo**: Ecosistema procedural.
- [x] Ensamblador de Almas y Plantillas.
- [x] Centro de Comando y Forja de Almas (`AgentRoster`).
- [x] Ciclo de Sueño REM (`SleepManager`).

--------------------------------------------------------------------------------

## Fase 5: Simulación Autónoma (El Gran Salto) [EN PROCESO]
**Objetivo**: Transformar el sistema de un "Chatbot Reactivo" a una "Simulación Viva" que persiste y evoluciona incluso cuando el usuario no está presente.

### 1. [CHIEF ARCHITECT] Saltos Temporales Offline (Time-Skips) [✅ COMPLETADO]
- **Estado**: Completado.
- **Descripción**: Simular el paso del tiempo cuando el usuario regresa tras una ausencia larga.
- **Implementación**:
    - `TimeSkipService` calcula `delta_time` y genera `CollectiveEventNode` estocásticos.
    - Se inyecta contexto de fondo en el prompt del sistema al reconectar.

### 2. [ANTHROPOLOGIST] Límites y Dinámicas entre Agentes [✅ COMPLETADO]
- **Estado**: Completado.
- **Descripción**: Permitir que múltiples agentes interactúen entre sí sin intervención directa del usuario.
- **Implementación**:
    - `Social Battery` implementada en `AgentNode` con decaimiento por turno y recarga offline.
    - Decaimiento emocional (Ebbinghaus) aplicado a `ResonanceEdge`.

### 3. [CHIEF ARCHITECT] Intercambio de Datos JSON-LD [PRIORIDAD ALTA]
- **Estado**: Pendiente.
- **Descripción**: Estandarizar la exportación/importación de grafos de memoria para integración con MyWorld.
- **Acción**:
    - Implementar esquema JSON-LD para `AgentNode` y `MemoryEpisodeNode`.
    - Permitir portabilidad de "Almas" entre instancias.

--------------------------------------------------------------------------------

## Fase 6: Infraestructura y Escala (Horizonte)
**Objetivo**: Migración a nube y optimización masiva.

### 1. [CLOUD] Migración a Spanner
- **Acción**: Reemplazar `LocalSoulRepository` con `SpannerSoulRepository` para producción.

### 2. [CLOUD] Despliegue de Redis Distribuido
- **Acción**: Activar caché distribuida en entorno de producción (GCP Memorystore).
