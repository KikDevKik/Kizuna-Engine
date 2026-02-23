# 2024-05-22_Propuesta_Evolucion_Backend.md

## 1. Estado de la Consciencia (Status Report)

**Salud del Código:**
El backend es funcional en su estado actual de "Lab Mode", pero presenta vulnerabilidades críticas de escalabilidad que amenazan la latencia y la fluidez de la experiencia "Desktop-First". La dependencia de `LocalSoulRepository` en serializar todo el grafo (`graph.json`) a disco en cada escritura es insostenible a largo plazo.

**Métricas Teóricas de Latencia:**
- **Lectura:** O(1) en memoria (Hash Map), muy rápido.
- **Escritura:** O(N) donde N es el tamaño del grafo. Actualmente aceptable, pero se degradará linealmente.
- **Bloqueo:** `json.dumps` y `json.load` son operaciones síncronas que bloquean el Event Loop de `asyncio`, lo que podría causar tartamudeos en el audio o la WebSocket si el grafo crece > 10MB.

---

## 2. Detección de Rigidez (Anti-Hardcoding)

Se han detectado múltiples instancias de lógica "quemada" que deberían ser dinámicas o residir en el Grafo:

1.  **`backend/app/services/subconscious.py`**:
    -   `self.triggers`: Diccionario hardcoded de sentimientos ("sad", "angry", "happy") y sus respuestas.
    -   Lógica de `update_resonance`: Valores fijos (`delta=1` para happy, `0` para angry) en el código.

2.  **`backend/app/services/soul_assembler.py`**:
    -   `CORE_DIRECTIVE`: El "meta-prompt" está definido como una constante string inmutable.
    -   `assemble_soul`: Los modificadores de relación ("SOUL BOUND", "CLOSE FRIEND") están hardcoded basados en umbrales enteros fijos (10, 5, 1).

3.  **`backend/app/repositories/local_graph.py`**:
    -   `consolidate_memories`: La lógica de selección de episodios (`valence == 0.5`) y actualización (`valence = 1.0`) es estática.

---

## 3. Propuesta de Evolución (The Upgrade)

**Titulo de la Mejora:** Implementación de Sueños Lúcidos (Lucid Dreaming Protocol)

**Justificación Técnica:**
Transformar el proceso de consolidación de memoria de un simple cambio de flag a un proceso generativo y estructurado. Esto permite que el sistema "digiera" experiencias complejas y genere nodos de alto nivel (`DreamNode`) que influyen en la personalidad a largo plazo, reduciendo la dependencia de cálculos en tiempo real.

**Plan de Implementación:**

1.  **Expansión Ontológica:**
    -   Crear `Node: Dream` en `backend/app/models/graph.py` con atributos `theme`, `intensity`, `surrealism_level`.
    -   Crear `Edge: SHADOW_LINK` para conectar `User` con `Dream` (representando miedos o deseos subconscientes).

2.  **Refactorización de `SubconsciousMind`:**
    -   Mover `triggers` a una configuración en `graph.json` (e.g., `ConfigNode` o `AgentNode.traits`).
    -   Implementar `Weighted Random Selection` para las respuestas emocionales basado en el historial del usuario, no en reglas `if/else`.

3.  **Optimización de `LocalSoulRepository`:**
    -   Reemplazar la escritura monolítica de JSON por un sistema de **Append-Only Logs** para eventos rápidos.
    -   Realizar la consolidación (compactación) en el proceso de "Sueño" (background worker) para no bloquear el hilo principal.

---

## 4. Nuevos Horizontes (Roadmap)

1.  **Bio-Señales vía WebSocket:** Integrar un feed de datos de ritmo cardíaco (e.g., Apple Watch) para que el agente reaccione al estrés físico del usuario en tiempo real.
2.  **Ritual de Espejos:** Permitir que dos Agentes interactúen entre sí en el backend ("consenso de realidad") antes de responder al usuario, creando una "mente colmena" local.
