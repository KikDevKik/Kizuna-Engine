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
* **El Fallo:** Creamos un "tiempo de gracia" de 500ms (`_user_priority_window`). Cada vez que envías un paquete de audio, el temporizador se reinicia. 
* **La Realidad:** Tu micrófono no envía audio solo cuando hablas; envía "ruido de fondo" o "silencio digital" continuamente. Como el backend recibe paquetes constantemente, el sistema cree que **siempre estás hablando**. El agente intenta "pujar" por el micrófono, falla, activa el `turn_aborted = True` y descarta su respuesta entera. **El agente se está auto-censurando porque cree que nunca te callas.**

### 🐛 Problema 2: El "TaskGroup Zombie" (Silenciamiento de Errores)
* **Dónde:** `audio_session.py` (línea 448 aprox).
* **El Fallo:** En el bucle de recibir de Gemini, si ocurre un error genérico, pusimos un `break` en lugar de un `raise`.
* **La Realidad:** Si Gemini tiene un micro-corte o falla, el bucle de "hablar" del agente se cierra, pero no avisa al `TaskGroup`. El resultado es una **Sesión Zombie**: tú puedes seguir hablando (Upstream funciona), la base de datos sigue guardando, pero el agente está lógicamente "muerto" en esa conexión. No hay error en consola porque le dijimos que muriera en silencio.

### 🐛 Problema 3: Contención de Bloqueos en SQLite (Cuello de Botella)
* **Dónde:** `local_graph.py` (Nuevo repositorio SQLite).
* **El Fallo:** Cada vez que el agente drena su Batería Social, guarda una Memoria o actualiza la Fricción, abre un nuevo `AsyncSessionLocal`. 
* **La Realidad:** Con la Subconsciencia y la Reflexión operando en tiempo real, estamos bombardeando el archivo `.db` con múltiples conexiones simultáneas. SQLite no maneja bien escrituras concurrentes pesadas (se bloquea). Esto puede paralizar el hilo de eventos de FastAPI, haciendo que el audio "tartamudee" o se congele.

---

## 4. PROPUESTAS DE SOLUCIÓN (EL PLAN DE BATALLA)

Utilizaremos este mapa para atacar un problema a la vez, comprobando la estabilidad tras cada ataque.

### FASE 1: Destruir el Deadlock Acústico (Prioridad Máxima)
**Solución:** 
1. **Filtro de Ruido en el Backend:** En `audio_session.py`, no llamar a `auction_service.interrupt()` por cada paquete de *bytes* vacío. Solo llamar a la interrupción si un VAD (Voice Activity Detector) real (como WebRTC VAD o un umbral de volumen) detecta que hay *voz*, no solo estática.
2. **Alternativa Rápida:** Si el frontend ya tiene VAD (que solo envía audio cuando hablas), entonces el error es que la "Puja del Agente" es de 1.0, pero no le dimos un mecanismo para ganar si el usuario habla muy poco. Debemos relajar el `turn_aborted` para que **pause** y guarde el audio en un buffer en lugar de tirar toda la respuesta de la IA a la basura.

### FASE 2: Resucitar a los Zombies
**Solución:**
En `receive_from_gemini`, quitar el `break` en el bloque `except Exception`. Debemos permitir que el error se lance (`raise e`) para que el `TaskGroup` colapse limpiamente, cierre el WebSocket y obligue al frontend a reconectar, curando el estado zombie.

### FASE 3: Blindar SQLite (WAL Mode)
**Solución:**
En `core/database.py`, asegurar que SQLite se conecte usando el modo **WAL (Write-Ahead Logging)**. Esto permite leer y escribir al mismo tiempo sin bloquear toda la base de datos, vital para un sistema de IA multi-agente en tiempo real.

---
*Fin del Documento.*
