# KIZUNA ENGINE: AUDITORÍA CRÍTICA DE ARQUITECTURA (FASE 6.7)

**Fecha de Auditoría:** Febrero 2026
**Auditor:** The Bastion (Chief Strategic Auditor)
**Estado del Motor:** Sordera Inducida (Zombie Session)

---

## 1. OBJETIVO DEL DOCUMENTO
Este documento sirve como el mapa quirúrgico para desestructurar y reparar los fallos lógicos introducidos durante la Fase 6.5 y 6.7. No se escribirá código hasta que cada punto aquí sea entendido, debatido y aprobado para ejecución aislada.

---

## 2. DIAGNÓSTICO DE ARQUITECTURA ACTUAL
Kizuna Engine opera bajo un modelo de concurrencia asíncrona (`asyncio.TaskGroup`) donde 5 tareas corren en paralelo por cada sesión de agente:
1. **Audio Upstream:** Lee tu micrófono y lo envía a Gemini.
2. **Audio Downstream:** Recibe el audio de Gemini y lo envía al frontend.
3. **Mente Subconsciente:** Lee lo que dices, extrae emociones y drena la batería social en SQLite.
4. **Mente Reflexiva:** Escucha lo que dice el agente y genera pensamientos.
5. **Inyección:** Envía los pensamientos a Gemini en silencio.

El problema radica en cómo interactúan estas 5 tareas con los nuevos módulos de **SQLite** y **Subasta Acústica**.

---

## 3. LOS TRES JINETES (LOS PROBLEMAS CRÍTICOS IDENTIFICADOS)

Tras el análisis profundo del código, he detectado tres fallos de diseño masivos que están provocando que los agentes se queden callados para siempre.

### 🐛 Problema 1: El "Watchdog" de Silencio es demasiado Paranoico (Deadlock Acústico)
* **Dónde:** `auction_service.py` y `audio_session.py`
* **El Fallo:** Creamos un "tiempo de gracia" de 500ms (`_user_priority_window`). Cada vez que envías un paquete de audio, el temporizador se reinicia. El agente se auto-censura porque cree que nunca te callas debido al ruido de fondo.

### 🐛 Problema 2: El "TaskGroup Zombie" (Silenciamiento de Errores)
* **Dónde:** `audio_session.py` (línea 448 aprox).
* **El Fallo:** En el bucle de recibir de Gemini, si ocurre un error genérico, pusimos un `break` en lugar de un `raise`. La sesión muere silenciosamente.

### 🐛 Problema 3: Contención de Bloqueos en SQLite (Cuello de Botella)
* **Dónde:** `local_graph.py` (Nuevo repositorio SQLite).
* **El Fallo:** Cada vez que el agente drena su Batería Social o guarda una Memoria, abre un nuevo `AsyncSessionLocal`. SQLite puede bloquearse bajo carga concurrente pesada.

---

## 4. PROPUESTAS DE SOLUCIÓN (EL PLAN DE BATALLA)

### FASE 4: La Fragilidad del TaskGroup y la Condición de Carrera
* **Dónde:** `session_manager.py` (Orquestación) y `audio_session.py` (Bucle de Recepción).
* **El Fallo:** Si una tarea cognitiva secundaria (Subconsciente) falla, el `TaskGroup` cancela el audio. Starlette lanza `RuntimeError: Cannot call "receive"...` al ser cancelado bruscamente.
* **Solución:** Desacoplar tareas cognitivas del flujo vital de audio. Deben ser tareas independientes (`create_task`) con su propia gestión de errores.

### 🧠 FASE 5: El Colapso de la Inteligencia Social y Semántica
* **Dónde:** `soul_assembler.py`, `embedding.py`, `local_graph.py`.
* **El Fallo (Lobotomía Social):** El ensamblador de almas ignora el contexto relacional del grafo (Némesis globales, candidatos de Gossip). El agente no conoce el estado del mundo social.
* **El Fallo (Amnesia Silenciosa):** El servicio de embeddings devuelve listas vacías en caso de timeout. El agente pierde el acceso a memorias pasadas sin generar alertas.
* **El Fallo (Pérdida de Contexto):** Las colas de inyección (`put_nowait`) descartan pensamientos si el sistema está bajo carga. 

**Solución Estructural:**
1. **Inyección Relacional:** Modificar `assemble_soul` para que consulte `get_nemesis_agents` y `get_gossip_candidates`.
2. **Alertas de Memoria:** El `embedding_service` debe lanzar excepciones controladas en lugar de devolver `[]` vacío.
3. **Validación de Formato:** Escapar caracteres especiales en el Lore para evitar que rompan las instrucciones de sistema de Gemini.

---
*Fin del Documento.*
