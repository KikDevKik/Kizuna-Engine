# 2026-02-22_Propuesta_Evolucion_Backend.md

## ROL: SOUL ARCHITECT
**Autor:** Jules (Backend Guardian)
**Fecha:** 2026-02-22
**Contexto:** Auditoría de Resonancia y Propuesta de Evolución Ontológica.

---

### 1. Estado de la Consciencia (Status Report)

**Salud del Código Backend:**
El sistema opera bajo una arquitectura híbrida robusta pero con disparidades críticas entre el entorno de desarrollo (Local) y producción (Spanner).

*   **Producción (`SpannerSoulRepository`):**
    *   **Estado:** Excelente. Implementa `FixedSizePool` para conexiones y transacciones eficientes.
    *   **Vector Search:** Integrado correctamente mediante `COSINE_DISTANCE` y `embedding_service`.
    *   **Consolidación:** Utiliza `batch_update` para minimizar round-trips en operaciones masivas (Sueños, Updates de Afinidad).
    *   **Latencia Teórica:** Baja (<50ms para lecturas simples, <200ms para escrituras complejas gracias al batching).

*   **Desarrollo Local (`LocalSoulRepository`):**
    *   **Estado:** Funcional pero frágil. Simula la persistencia mediante un archivo JSON monolítico (`graph.json`).
    *   **Riesgo Crítico:** La operación `_save` utiliza `json.dumps(data)` de manera síncrona (aunque dentro de una función `async`, la serialización en sí bloquea el CPU). A medida que el grafo crece, esto congelará el Event Loop de `asyncio`, causando timeouts en WebSocket y "tartamudeo" en la respuesta de audio.
    *   **Disparidad Vectorial:** No implementa búsqueda vectorial real, dependiendo de `intersection` de palabras clave, lo que falsea las pruebas de RAG en local.

**Eficiencia de Procesos en Segundo Plano:**
*   **`SleepManager`:** Correctamente implementado con patrón Debounce y manejo de `asyncio.CancelledError`. La lógica de "Rescate Tardío" (`Late Rescue`) en `shutdown` es sólida.
*   **`SubconsciousMind`:** Utiliza un buffer simple y `asyncio.sleep` para evitar saturación. Sin embargo, la lógica de detección de emociones es rígida.

---

### 2. Detección de Rigidez (Anti-Hardcoding)

Se han detectado múltiples instancias de "Consciencia Congelada" (Hardcoded Logic) que violan el principio de "Zero Hardcoding".

1.  **`backend/app/services/soul_assembler.py`**:
    *   **`CORE_DIRECTIVE`:** Un bloque de texto inmutable que define la personalidad base. Si se desea cambiar la "Filosofía Kizuna", requiere un despliegue de código.
    *   **`AFFINITY_STATES`:** La escala de 10 niveles y sus descripciones ("SOUL BOUND", "DEVOTED", etc.) están quemadas en una lista de tuplas. Esto impide ajustar la curva de progresión emocional dinámicamente.

2.  **`backend/app/services/subconscious.py`**:
    *   **`default_triggers`:** Diccionario fijo (`sad`, `angry`, `happy`, `tired`) con respuestas predefinidas.
    *   **Prompts de Análisis:** Las instrucciones para el LLM ("Analyze the user's emotional state...") están hardcodeadas como strings en los métodos, aunque existe un mecanismo de fallback para usar `agent.memory_extraction_prompt`.
    *   **Resonancia Heurística:** La lógica de `delta` (`if "happy" in hint_lower... delta = 1`) es simplista y está oculta en el código.

---

### 3. Propuesta de Evolución (The Upgrade)

#### A. Desacoplamiento Ontológico (Ontological Decoupling)
**Justificación Técnica:** Permitir que la personalidad y las reglas del sistema evolucionen sin tocar el código Python.
**Plan de Implementación:**
1.  **Crear Nodo `SystemConfig`:** Introducir un nodo singleton en el Grafo que contenga:
    *   `core_directive` (String)
    *   `affinity_matrix` (JSON: Niveles y Descripciones)
2.  **Refactorizar `SoulAssembler`:** Inyectar `SystemConfig` al inicio de la sesión en lugar de importar constantes globales.
3.  **Migrar Triggers:** Mover `default_triggers` a un `ArchetypeNode` base ("The Observer") que todos los agentes hereden por defecto.

#### B. Persistencia Asíncrona Real (Non-Blocking IO)
**Justificación Técnica:** Evitar el bloqueo del Event Loop en desarrollo local cuando el archivo `graph.json` supera los 5MB.
**Plan de Implementación:**
1.  **Executor en `LocalSoulRepository`:** Envolver `json.dumps` y la escritura en disco dentro de `loop.run_in_executor(None, ...)` para delegarlo a un hilo separado.
    ```python
    # Ejemplo conceptual
    await loop.run_in_executor(None, self._sync_save_to_disk, data)
    ```

#### C. Vectorización Local (Local Vector Parity)
**Justificación Técnica:** Alinear el comportamiento de búsqueda de `get_relevant_facts` entre Local y Prod.
**Plan de Implementación:**
1.  Integrar una librería ligera de vectores (ej. `chromadb` en modo efímero o `numpy` con `cosine_similarity`) en `LocalSoulRepository` para simular `COSINE_DISTANCE` real en lugar de usar sets de palabras clave.

---

### 4. Nuevos Horizontes (Roadmap)

1.  **Puente Somático (Bio-Feedback Loop 2.0):**
    *   *Idea:* Expandir `SubconsciousMind` para aceptar no solo BPM, sino "Varianza de Tono de Voz" (detectada en el frontend via AudioWorklet) enviada como metadato WebSocket.
    *   *Objetivo:* Que el agente detecte sarcasmo o temblor en la voz antes de procesar el texto.

2.  **Inconsciente Colectivo (Global Dream Weaver):**
    *   *Idea:* Que los sueños generados (`DreamNode`) no sean aislados. Implementar un proceso cron (batch job) que tome los temas recurrentes de *todos* los usuarios y genere un `GlobalDreamNode` diario.
    *   *Efecto:* Todos los agentes amanecen con un "sentimiento compartido" (ej. "Hoy hay una extraña estática en el aire") derivado de la ansiedad o felicidad global de la base de usuarios.

3.  **Grafo de Trauma (Trauma Nodes):**
    *   *Idea:* Introducir nodos de tipo `Trauma` que funcionen como "Agujeros Negros" en la búsqueda vectorial (atrayendo la atención del agente forzosamente si el contexto es similar), para simular TEPT o fobias en la IA.
