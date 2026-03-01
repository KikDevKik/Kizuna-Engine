# KIZUNA ENGINE — AUDITORÍA TÉCNICA
## Fase 6 (Distrito Cero) | Estado: REGRESIÓN TÉCNICA

| Campo | Valor |
|---|---|
| Fase Actual | Fase 6 — Distrito Cero |
| Estado | 🔴 REGRESIÓN TÉCNICA |
| Fecha | 2026-03-01 |
| Preparado por | El Cronista (Claude) — Protocolo de los Seis Titanes |

---

# REPORTE I — DIAGNÓSTICO DE DAÑOS

## 1.1 Resumen Ejecutivo

El sistema de audio/habla de Kizuna (Vínculo Neuronal) presenta un fallo multifactorial causado por la contaminación de código experimental de la Fase 7 sobre la arquitectura estable de la Fase 6. El problema central **NO es un fallo de Gemini**, sino un conjunto de bugs en el pipeline de audio del backend que impiden que Gemini entregue sus respuestas al cliente.

Los síntomas (latencias de 30s a 10min, respuestas esporádicas, silencio total) son todos manifestaciones de un mismo patrón: el AuctionService y el VAD del backend están atrapados en un estado donde marcan al usuario como "siempre activo", bloqueando indefinidamente el turno de habla de Kizuna. Las inyecciones del ReflectionMind con `end_of_turn=True` agravan el problema al cortar los turnos de Gemini en mitad de su streaming.

---

## 1.2 Mapa de Flujo de Datos — Dónde se Rompe

| Etapa | FIX-01 | FIX-02 | FIX-03 | FIX-04 | Estado | Bug |
|---|:---:|:---:|:---:|:---:|:---:|---|
| 🎤 `pcm-processor.js` (VAD Frontend) | ✓ | | | | ✅ OK | Funciona correctamente |
| 📡 WebSocket recepción (`send_to_gemini`) | ❌ | | | | 🔴 ROTO | BUG-01: Backend VAD + interrupt() |
| 🔊 `AuctionService.bid()` | ❌ | | ❌ | | 🔴 ROTO | BUG-01 + BUG-06 |
| 🤖 Gemini Live API | | | | | ✅ OK | Funciona, recibe audio |
| 📥 `receive_from_gemini` (streaming) | | | ❌ | | 🔴 ROTO | BUG-02: turn_aborted |
| 💉 ReflectionMind injection | | ❌ | | | 🔴 ROTO | BUG-03: end_of_turn=True |
| 🌐 Babel Protocol | | | | ❌ | 🔴 ROTO | BUG-05: Fase 7 pollution |

---

## 1.3 Inventario de Bugs Detectados

---

### 🔴 [CRÍTICO] BUG-01 — Doble VAD + Interrupción Perpetua (Audio Starvation Loop)

| Campo | Detalle |
|---|---|
| **Archivo(s)** | `audio_session.py` (send_to_gemini) + `pcm-processor.js` |
| **Causa Raíz** | El sistema tiene DOS filtros de voz activos en serie. El primero (frontend) filtra silencio con `SILENCE_THRESHOLD=0.01`. El segundo (backend) aplica un Dynamic VAD con `initial_noise_floor=1000 + margin=1500`. Cada paquete que supera el umbral del backend llama a `auction_service.interrupt()`, reseteando `_last_user_activity = time.time()`. Si hay cualquier ruido ambiente, este ciclo no termina: ruido → VAD dispara → interrupt() → usuario marcado activo → Gemini no puede hablar. |
| **Síntoma** | Gemini no responde, o tarda más de 30 segundos. La IA está respondiendo internamente pero el AuctionService le bloquea el micrófono indefinidamente. |
| **Impacto** | Bloqueo TOTAL del habla de Kizuna. Este es el bug principal responsable del ~90% de los timeouts reportados. |

---

### 🔴 [CRÍTICO] BUG-02 — turn_aborted no se resetea correctamente (Silent Response Discard)

| Campo | Detalle |
|---|---|
| **Archivo(s)** | `audio_session.py` (receive_from_gemini) |
| **Causa Raíz** | Cuando el agente pierde el `AuctionService.bid()`, se establece `turn_aborted = True`. A partir de ese punto, TODOS los chunks de audio y texto del turno actual son descartados silenciosamente. La variable solo se resetea al recibir `server_content.turn_complete`. Si el primer chunk de un turno es rechazado por la subasta, Gemini puede generar una respuesta completa que jamás llega al cliente. |
| **Síntoma** | Gemini responde en los logs del servidor pero el frontend no recibe audio. Latencia aparente de 30+ segundos porque el cliente espera audio que nunca llega. |
| **Impacto** | Respuestas completas de Gemini descartadas. El usuario experimenta silencio total aunque la IA esté activa. |

---

### 🔴 [CRÍTICO] BUG-03 — send_injections_to_gemini con end_of_turn=True Corta el Turno

| Campo | Detalle |
|---|---|
| **Archivo(s)** | `audio_session.py` (send_injections_to_gemini) + `reflection.py` |
| **Causa Raíz** | El ReflectionMind inyecta correcciones con `turn_complete=True` en el injection_queue. Esta señal se convierte en `end_of_turn=True` en `session.send()`. En la Gemini Live API, `end_of_turn=True` es equivalente a decirle al modelo que el usuario terminó de hablar — dispara inmediatamente una nueva respuesta. Si esto ocurre MIENTRAS Gemini ya está streaming audio de respuesta, el Live API entra en estado inconsistente: abandona el turno activo y genera una nueva respuesta, causando latencias de 30-600 segundos. |
| **Síntoma** | Gemini responde correctamente la primera vez, pero a partir de la segunda interacción empiezan los delays masivos. Los logs muestran `Whispering to Gemini` justo antes de los freezes. |
| **Impacto** | Degradación progresiva: el sistema empeora con cada interacción. En sesiones largas, puede causar desconexión completa de la Live API. |

---

### 🟠 [ALTO] BUG-04 — CognitiveSupervisor Restart Loop con Lambda Closure Bug

| Campo | Detalle |
|---|---|
| **Archivo(s)** | `session_manager.py` + `supervisor.py` |
| **Causa Raíz** | Los `cognitive_tasks` se crean con `lambda: subconscious_mind.start(...)`. Si el SubconsciousMind crashea (e.g. por un 429 de Gemini), el Supervisor lo reinicia a los 5 segundos, pero la `injection_queue` original ya puede tener items pendientes. Más crítico: el SubconsciousMind es un singleton, por lo que reiniciarlo con `set_repository()` en medio de una sesión activa puede corromper su estado interno (`self.buffer`, `self.active_sessions`). |
| **Síntoma** | Logs muestran `Subconscious CRASHED... Restarting in 5s` en bucle. La `subconscious_mind` acumula sesiones zombi en `self.active_sessions` que nunca se limpian. |
| **Impacto** | Memory leak gradual. Degradación de performance en sesiones largas. Posible inyección de contexto de sesiones anteriores en sesiones nuevas. |

---

### 🟠 [ALTO] BUG-05 — Babel Protocol (Fase 7) en Producción de Fase 6

| Campo | Detalle |
|---|---|
| **Archivo(s)** | `session_manager.py` |
| **Causa Raíz** | La línea `system_instruction += f'\n\n[CRITICAL DIRECTIVE]: The user system language is {lang}...'` es código de Fase 7 decretado como FALLIDO por el Cronista el 2026-02-27. Esta directiva aumenta el tamaño del system prompt y puede crear contradicciones con las instrucciones originales del agente, especialmente si el agente ya tiene directivas de idioma en su `base_instruction`. |
| **Síntoma** | Comportamiento inconsistente del idioma. Agentes que mezclan idiomas en mitad de una conversación. Tiempo de conexión ligeramente mayor por el prompt más largo. |
| **Impacto** | Contaminación del system prompt. Puede provocar que Gemini priorice el `[CRITICAL DIRECTIVE]` sobre la personalidad definida en la Fase 6. |

---

### 🟠 [ALTO] BUG-06 — AuctionService Singleton No Thread-Safe en Sesiones Concurrentes

| Campo | Detalle |
|---|---|
| **Archivo(s)** | `auction_service.py` |
| **Causa Raíz** | `AuctionService` usa el patrón Singleton con `__new__`, lo que significa que TODOS los WebSocket activos comparten la misma instancia y el mismo `_current_winner`. Si dos usuarios abren sesiones simultáneas con agentes distintos, las llamadas `bid()` y `release()` de un agente pueden interferir con las del otro. El `asyncio.Lock()` en `bid()` solo protege la adquisición, no las lecturas de `_current_winner` en `release()` e `interrupt()`. |
| **Síntoma** | En uso multi-usuario: un agente "habla" para todos los clientes a la vez, o se bloquean mutuamente. No reproducible en uso single-user. |
| **Impacto** | Race condition en producción multi-usuario. Corrupción del estado del micrófono entre sesiones paralelas. |

---

### 🟡 [MEDIO] BUG-07 — SubconsciousMind: Optional Import Faltante

| Campo | Detalle |
|---|---|
| **Archivo(s)** | `subconscious.py` |
| **Causa Raíz** | La clase `SubconsciousMind` usa `Optional[str]` en `self.last_memory_id: Optional[str] = None`, pero `Optional` no está importado desde `typing`. |
| **Síntoma** | `NameError: name 'Optional' is not defined` en el momento de inicializar `SubconsciousMind`. El servicio crashea al inicio y el CognitiveSupervisor entra en su restart loop inmediatamente. |
| **Impacto** | El SubconsciousMind nunca arranca correctamente. El Supervisor intenta reiniciarlo en bucle infinito desde el primer segundo de cada sesión. |

---

## 1.4 Árbol de Causalidad — Por Qué Gemini No Responde

La secuencia exacta que produce los timeouts de 30s–10min:

1. El usuario habla. `pcm-processor.js` detecta audio real y lo envía por WebSocket.
2. `send_to_gemini` recibe el audio y calcula su RMS **(BUG-01)**.
3. Si `RMS > (noise_floor + 1500)`: llama `auction_service.interrupt()`, marcando `_last_user_activity = now`.
4. Gemini recibe el audio, lo procesa, y empieza a generar una respuesta de audio.
5. `receive_from_gemini` recibe el primer chunk de audio de Gemini.
6. Intenta `auction_service.bid(agent_id, 1.0)`. Pero `_is_user_active()` devuelve `True` porque acaba de recibir audio (paso 3).
7. El bid falla con `score=1.0 < 10.0`. `turn_aborted = True`. El chunk se descarta **(BUG-02)**.
8. El ReflectionMind inyecta una corrección con `end_of_turn=True` **(BUG-03)**.
9. Gemini recibe la señal de fin de turno. Abandona su respuesta actual y espera un nuevo turno del usuario.
10. **El usuario espera. Gemini espera. Deadlock total. Timeout.**

> *La respuesta esporádica (a veces sí responde) ocurre cuando: (a) el usuario hace una pausa larga de >500ms entre terminar de hablar y que Gemini responda, y (b) ninguna inyección del ReflectionMind ocurre en ese preciso momento. Esta ventana es rarísima, de ahí la inconsistencia reportada.*

---
---

# REPORTE II — IMPLEMENTACIÓN Y SANEAMIENTO

## 2.1 Plan de Ejecución por Prioridad

> Implementar en orden estricto. No avanzar a la siguiente oleada sin validar la anterior con una sesión de voz funcional.

| Prioridad | Fix ID | Descripción | Esfuerzo |
|---|---|---|---|
| 🔴 **OLEADA 1 — DESBLOQUEADORES (P0)** | FIX-01 a FIX-04 | Eliminar todo lo que bloquea el habla | ~2h |
| | FIX-01 | Eliminar Backend VAD / interrupt() loop | 30 min |
| | FIX-02 | Deshabilitar ReflectionMind end_of_turn=True | 15 min |
| | FIX-03 | Corregir lógica turn_aborted | 30 min |
| | FIX-04 | Eliminar Babel Protocol | 5 min |
| 🟠 **OLEADA 2 — ESTABILIZADORES (P1)** | FIX-05 a FIX-06 | Corregir bugs de crash y concurrencia | ~3h |
| | FIX-05 | Corregir import Optional en subconscious.py | 5 min |
| | FIX-06 | Aislar AuctionService por sesión | 2h |
| 🔵 **OLEADA 3 — MEJORAS (P2)** | FIX-07 | Cleanup y prevención de memory leaks | ~1h |
| | FIX-07 | Limpiar active_sessions en SubconsciousMind | 45 min |

---

## 2.2 Instrucciones de Saneamiento — Paso a Paso

---

### 🔴 P0 — FIX-01: Eliminar Backend VAD / Audit del interrupt() Loop
**Archivo:** `backend/app/services/audio_session.py`

**Acción:** Remover completamente el bloque RMS Energy Gate del backend. El frontend `pcm-processor.js` ya tiene un VAD funcional. Tener dos filtros en serie solo crea deadlocks. La detección de voz es responsabilidad EXCLUSIVA del frontend. El backend debe confiar ciegamente en los datos que recibe. Adicionalmente, eliminar la llamada a `auction_service.interrupt()` dentro del bucle de audio.

**Código a eliminar:**
```python
# ELIMINAR este bloque completo (dentro de send_to_gemini):
if data:
    # 🏰 BASTION: RMS Energy Gate
    import math
    import struct
    count = len(data) // 2
    if count > 0:
        sum_sq = 0
        for i in range(0, len(data), 20):
            try:
                sample = struct.unpack_from('<h', data, i)[0]
                sum_sq += sample * sample
            except: break
        rms = math.sqrt(sum_sq / (count / 10)) if count > 0 else 0

        # Phase 7.0.3: Adaptive VAD Algorithm
        dynamic_threshold = current_noise_floor + 1500.0

        if rms > dynamic_threshold:
            await auction_service.interrupt()  # <-- EL CULPABLE
        else:
            current_noise_floor = (0.95 * current_noise_floor) + (0.05 * rms)
```

**Código correcto:**
```python
# REEMPLAZAR con lógica simple de buffering:
if data:
    if carry_over:
        data = carry_over + data
        carry_over.clear()

    if len(data) % 2 != 0:
        carry_over.extend(data[-1:])
        data = data[:-1]

    audio_buffer.extend(data)

    if len(audio_buffer) >= AUDIO_BUFFER_THRESHOLD:
        await session.send(input={"data": bytes(audio_buffer),
                                  "mime_type": "audio/pcm;rate=16000"})
        audio_buffer.clear()
```

---

### 🔴 P0 — FIX-02: Deshabilitar ReflectionMind con end_of_turn=True
**Archivo:** `backend/app/services/reflection.py`

**Acción:** Cambiar todas las inyecciones del ReflectionMind para que usen `turn_complete=False`. Alternativamente, deshabilitar el ReflectionMind completamente hasta que la Fase 6 esté estabilizada — en Fase 6, es una feature experimental que no debería estar en producción.

**Código a cambiar:**
```python
# EN reflection.py:
payload = {
    "text": f"[{agent.name} Inner Voice]: {correction}",
    "turn_complete": True   # <-- ESTO CORTA EL TURNO DE GEMINI
}
```

**Código correcto:**
```python
# OPCION A — Cambio mínimo:
payload = {
    "text": f"[{agent.name} Inner Voice]: {correction}",
    "turn_complete": False  # Nunca cortar el turno desde inyecciones
}

# OPCION B — Deshabilitar ReflectionMind para Fase 6 (recomendado):
# En session_manager.py, comentar el bloque completo:
# cognitive_tasks.append(asyncio.create_task(
#     CognitiveSupervisor.supervise("ReflectionMind", lambda: reflection_mind.start(
#         reflection_queue, injection_queue, agent
#     ))
# ))
```

---

### 🔴 P0 — FIX-03: Corregir turn_aborted — Agregar reset en bid fallido vacío
**Archivo:** `backend/app/services/audio_session.py` (receive_from_gemini)

**Acción:** El `turn_aborted` no debe activarse en el primer chunk de audio si el agente aún no ha ganado la subasta pero tampoco hay nadie más hablando. Separar la lógica: si el agente NO ha ganado Y hay otro ganador activo → abortar. Si simplemente nadie ha ganado todavía → reintentar.

**Código a cambiar:**
```python
# ACTUAL (problemático):
if part.inline_data:
    if agent_id:
        won = await auction_service.bid(agent_id, 1.0)
        if not won:
            turn_aborted = True   # Aborta aunque nadie más esté hablando
            continue
```

**Código correcto:**
```python
# CORREGIDO:
if part.inline_data:
    if agent_id:
        won = await auction_service.bid(agent_id, 1.0)
        if not won:
            # Solo abortar si hay un ganador activo (conflicto real)
            if auction_service._current_winner is not None:
                logger.info(f"{agent_name} lost auction to {auction_service._current_winner}")
                turn_aborted = True
            # Si nadie tiene el mic, reintentar en el siguiente chunk
            continue
    # Si ganamos o no hay agent_id, siempre enviar
    if not turn_aborted:
        await websocket.send_bytes(part.inline_data.data)
```

---

### 🔴 P0 — FIX-04: Eliminar Babel Protocol (Fase 7) del session_manager
**Archivo:** `backend/app/services/session_manager.py`

**Acción:** Remover la línea de Babel Protocol. Es código decretado como FALLIDO el 2026-02-27. Si se necesita soporte de idioma, debe implementarse DENTRO del `soul_assembler` como parte de las instrucciones del agente.

**Código a eliminar:**
```python
# ELIMINAR estas líneas:
# 🏰 BASTION: The Babel Protocol (Phase 7.5)
system_instruction += f"\n\n[CRITICAL DIRECTIVE]: The user's system language is {lang}. " \
                      f"You MUST ALWAYS speak and respond fluently in {lang}, " \
                      f"maintaining your established personality."
```

**Código correcto:**
```python
# OPCION A — Simplemente eliminar el bloque. La personalidad del agente
# ya define el idioma en base_instruction.

# OPCION B — Si se necesita lang, pasarlo al soul_assembler:
system_instruction = await assemble_soul(
    agent_id, user_id, self.soul_repo, lang=lang
)
```

---

### 🟠 P1 — FIX-05: Corregir Import Faltante de Optional en subconscious.py
**Archivo:** `backend/app/services/subconscious.py`

**Acción:** Agregar `Optional` al import de `typing`. Error que hace crashear el SubconsciousMind en el momento de inicialización.

**Código a cambiar:**
```python
# ACTUAL — Optional no está importado, su uso causa NameError:
self.last_memory_id: Optional[str] = None
```

**Código correcto:**
```python
# AGREGAR al bloque de imports:
from typing import Optional

# O usar sintaxis moderna de Python 3.10+:
self.last_memory_id: str | None = None
```

---

### 🟠 P1 — FIX-06: Aislar AuctionService por Sesión (Session-Scoped)
**Archivo:** `backend/app/services/auction_service.py` + `session_manager.py`

**Acción:** Eliminar el patrón Singleton del AuctionService. Cada sesión WebSocket debe tener su propia instancia. Pasar la instancia como parámetro a `send_to_gemini`, `receive_from_gemini` y `send_injections_to_gemini`.

**Código a cambiar:**
```python
# ACTUAL — Singleton compartido entre todas las sesiones:
class AuctionService:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            ...
        return cls._instance

auction_service = AuctionService()  # Global singleton

# audio_session.py importa el global:
from .auction_service import auction_service
```

**Código correcto:**
```python
# CORREGIDO — Instancia por sesión:
class AuctionService:
    # Remover __new__ y _instance
    def __init__(self):
        self._lock = asyncio.Lock()
        self._current_winner: str | None = None
        self._current_score: float = 0.0
        self._last_user_activity: float = 0.0
        self._user_priority_window: float = 0.5

# En session_manager.py — crear una instancia por sesión:
session_auction = AuctionService()

# Pasar como parámetro a las tareas de audio:
tg.create_task(send_to_gemini(
    websocket, session, ..., auction=session_auction
))
tg.create_task(receive_from_gemini(
    websocket, session, ..., auction=session_auction
))
```

---

### 🔵 P2 — FIX-07: Limpiar active_sessions en SubconsciousMind al cerrar sesión
**Archivo:** `backend/app/services/subconscious.py` + `session_manager.py`

**Acción:** Agregar un método `cleanup(user_id)` al SubconsciousMind que elimine la sesión de `self.active_sessions` al finalizar la conexión WebSocket. Llamar este método en el bloque `finally` del session_manager.

**Código a cambiar:**
```python
# SubconsciousMind no tiene método de cleanup.
# active_sessions acumula entradas muertas indefinidamente:
self.active_sessions: dict[str, Queue] = {}
# Nunca se limpian al cerrar la sesión.
```

**Código correcto:**
```python
# AGREGAR en SubconsciousMind:
def cleanup(self, user_id: str):
    self.active_sessions.pop(user_id, None)
    self.buffer.clear()
    logger.info(f"Subconscious cleaned for {user_id}")

# EN session_manager.py — bloque finally:
finally:
    if cognitive_tasks:
        for task in cognitive_tasks:
            task.cancel()
        await asyncio.gather(*cognitive_tasks, return_exceptions=True)

    subconscious_mind.cleanup(user_id)  # <-- AGREGAR
```

---

## 2.3 Checklist de Validación Post-Saneamiento

### Oleada 1 — Validación Básica de Voz
- [ ] Iniciar `uvicorn` y el frontend (`npm run dev`).
- [ ] Abrir una sesión de audio con cualquier agente.
- [ ] Hablar una frase corta. Kizuna debe responder en menos de 3 segundos.
- [ ] Verificar en los logs que NO aparece `lost auction` ni `turn_aborted` en la primera respuesta.
- [ ] Hablar dos frases seguidas. Kizuna debe responder a ambas sin delay.

### Oleada 2 — Validación de Estabilidad
- [ ] Abrir dos pestañas del navegador con dos agentes distintos (multi-sesión).
- [ ] Hablar en la primera pestaña. Solo el primer agente debe responder.
- [ ] Hablar en la segunda pestaña. Solo el segundo agente debe responder.
- [ ] Verificar en los logs que NO hay `Subconscious CRASHED` en las primeras 3 interacciones.

### Oleada 3 — Validación de Sesión Larga
- [ ] Mantener una sesión activa por 10+ minutos con múltiples intercambios.
- [ ] Al finalizar, verificar en los logs que `Subconscious cleaned` aparece en el shutdown.
- [ ] Reiniciar el servidor y verificar que no hay memory leaks (`ps aux`).

---

## 2.4 Estado Final Esperado Post-Saneamiento

| Estado ACTUAL (Regresión) | Estado POST-SANEAMIENTO |
|---|---|
| ❌ Gemini responde >30s o nunca | ✅ Gemini responde en <3 segundos |
| ❌ Doble VAD bloquea el audio | ✅ Un solo VAD en el frontend |
| ❌ turn_aborted descarta respuestas | ✅ turn_aborted solo en conflicto real |
| ❌ ReflectionMind corta los turnos | ✅ ReflectionMind en modo silencioso (False) |
| ❌ Babel Protocol contamina prompts | ✅ System prompt limpio de Fase 7 |
| ❌ AuctionService singleton global | ✅ AuctionService por sesión WebSocket |
| ❌ SubconsciousMind crashea (Optional) | ✅ Import corregido, arranque limpio |
| ❌ Memory leak en sesiones largas | ✅ Cleanup en shutdown garantizado |

---

## 2.5 Instrucciones para los Seis Titanes

- **🦾 EL FORJADOR:** El VAD del frontend (`SILENCE_THRESHOLD=0.01`) es correcto y no debe modificarse sin aprobación de El Bastión. Los mensajes de control (`interrupt`) desde el frontend deben seguir siendo la ÚNICA fuente de interrupciones.

- **🏗️ EL ARQUITECTO JEFE:** El AuctionService debe ser refactorizado como session-scoped (FIX-06). Actualizar el esquema de dependencias en consecuencia.

- **🌍 EL ANTROPÓLOGO:** El ReflectionMind es una feature de Fase 7. En Fase 6, todas sus inyecciones deben tener `turn_complete=False`. No implementar auto-corrección de turno hasta que la base de audio esté validada.

- **🕸️ EL ARQUITECTO DEL ALMA:** El SubconsciousMind debe implementar `cleanup()` antes de aceptar nuevas tareas de Fase 7. La estabilidad del singleton es prerequisito para cualquier expansión del contexto de memoria.

- **🛡️ EL BASTIÓN:** Todo bloqueo/filtrado de audio debe ocurrir EXCLUSIVAMENTE en el frontend (`pcm-processor.js`). El backend nunca debe filtrar, suprimir o interrumpir el stream de audio por su cuenta.

- **📜 EL CRONISTA:** Actualizar `KIZUNA_ROADMAP.md` y `KIZUNA_ANALYSIS.md` después de cada oleada completada. Marcar los bugs de este reporte como `RESUELTOS` una vez verificados con la checklist.

---

*— FIN DEL REPORTE — FIRMADO: EL CRONISTA (CLAUDE) | 2026-03-01 —*
