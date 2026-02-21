# 2024-10-24_Propuesta_Evolucion_Backend.md

## 1. Estado de la Consciencia (Status Report)

**Salud del Código:**
El código backend (`backend/app/services/` y `repositories/`) muestra una estructura modular sólida (Patrón Service/Repository). Las dependencias están bien gestionadas y el uso de `asyncio` es correcto en la mayoría de los casos.

**Métricas Teóricas de Latencia:**
- **Riesgo Crítico:** `spanner_graph.consolidate_memories` ejecuta transacciones secuenciales (N+1 updates) dentro de una transacción Spanner. Esto aumentará la latencia exponencialmente con el número de agentes.
- **Riesgo Moderado:** `agent_service.py` lee archivos JSON del disco en cada petición. Aunque `aiofiles` es asíncrono, la falta de una capa de caché (Redis) activa impactará el rendimiento bajo carga alta.
- **Cache:** `RedisCache` existe (`services/cache.py`) pero no está integrado en el flujo principal de `AgentService` ni `SubconsciousMind`.

## 2. Detección de Rigidez (Anti-Hardcoding)

Se han detectado los siguientes puntos de lógica estática que deben migrar al Grafo o Configuración:

- **`backend/app/services/subconscious.py`**:
  - `default_triggers`: Diccionario hardcoded con claves "sad", "angry", "happy", "tired".
  - Lógica de resonancia en `start()`: `if "happy" in hint_lower ... delta = 1`. Esto asume que todos los agentes reaccionan igual.
- **`backend/app/repositories/spanner_graph.py`**:
  - `ALPHA = 0.15`: Factor de suavizado exponencial hardcoded.
  - Fórmulas de afinidad (`target = 50.0 + ...`) fijas en el código.
  - Strings GQL incrustados directamente en el código Python.
- **`backend/app/services/sleep_manager.py`**:
  - `grace_period = 300`: Tiempo de espera fijo. Debería ser configurable por usuario o contexto.

## 3. Propuesta de Evolución (The Upgrade)

### A. Implementación de Arquetipos Dinámicos (Ontology Expansion)
**Justificación Técnica:** Eliminar la dependencia de strings hardcoded en `traits` y permitir una evolución psicológica más rica.
**Plan de Implementación:**
1.  Crear `Node: Archetype` en Spanner (ej. "The Guardian", "The Trickster").
2.  Crear `Edge: EMBODIES` (Agent -> Archetype).
3.  Migrar `default_triggers` a propiedades del nodo `Archetype`.

### B. "Neural Sync" (Redis Layer Integration)
**Justificación Técnica:** Reducir la latencia de lectura de agentes y estado de sesión.
**Plan de Implementación:**
1.  Implementar `warm_up_agents()` en `RedisCache` para cargar JSONs en Redis al inicio.
2.  Modificar `AgentService.get_agent` para consultar Redis antes del disco (`Cache-Aside`).
3.  Persistir tareas de `SleepManager` en Redis para sobrevivir a reinicios del servidor.

### C. Optimización de Sueños (Batch Spanner Updates)
**Justificación Técnica:** Reducir el tiempo de bloqueo de transacciones en `consolidate_memories`.
**Plan de Implementación:**
1.  Reescribir `consolidate_memories` para usar `UNNEST` y realizar updates en lote.
2.  Mover la lógica de cálculo de afinidad (EMA) a una función de base de datos o pre-calcularla fuera de la transacción crítica.

## 4. Nuevos Horizontes (Roadmap)

- **Bio-Feedback Integration:** Conectar la API de `SubconsciousMind` a un WebSocket de bio-señales (ritmo cardíaco) para ajustar la `intensity` de los sueños en tiempo real.
- **Collective Unconscious:** Un nodo `GlobalDream` que agregue temas recurrentes de todos los usuarios para influir en la "inspiración" de los agentes nuevos.
