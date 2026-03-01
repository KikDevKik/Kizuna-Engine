# KIZUNA ENGINE: DOCUMENTO MAESTRO DE ARQUITECTURA (ROADMAP)

**Estado:** FASE 7 — EL RENACIMIENTO DEL PUENTE | **Directriz:** Construir sobre la base estabilizada

---

## 🏗️ FASE 1 A 4: LOS CIMIENTOS [✅ COMPLETADO]
*Infraestructura base operativa. FastAPI, SQLite, WebSockets, React 19.*

---

## ⚙️ FASE 5: SIMULACIÓN AUTÓNOMA [✅ COMPLETADO]
*Grafo Relacional JSON-LD y Saltos Temporales operativos. TimeSkipService y SleepManager activos.*

---

## 🌆 FASE 6: EL DISTRITO CERO (HUB SOCIAL) [✅ COMPLETADO]
*2026-03-01 — Saneamiento ejecutado por Jules (Protocolo de Saneamiento — Oleadas 1, 2 y 3).*

### 6.1 Estética del Nexo [✅ COMPLETADO]
* 3D Revolver UI operativa. Estética "Dark Water" activa.

### 6.2 Ingeniería de Cascarones (Lazy Generation) [✅ COMPLETADO]
* Generación diferida de agentes estable.

### 6.3 Mecánica de Primer Contacto (Audio Session) [✅ COMPLETADO]
* **Oleada 1 — El Purgado (P0):** Backend VAD eliminado. Echo collision logic corregida. Babel Protocol removido.
* **Oleada 2 — La Estructura (P1):** AuctionService ahora es session-scoped (no más singleton). SubconsciousMind.cleanup() implementado.
* **Oleada 3 — La Psique (P1):** ReflectionMind inyecta con `turn_complete: False`. Auto-interrupción resuelta.
* **Resultado:** Latencia de respuesta <3s. Pipeline de audio estable. Tests pasando.

---

## 🌐 FASE 7: EL RENACIMIENTO DEL PUENTE [🚧 EN PROGRESO]

**Estado:** ACTIVA. Base de Fase 6 validada y estable. Construir en orden estricto.

> ⚠️ **Ley de Hierro de Fase 7:** No introducir ninguna feature que pueda comprometer la estabilidad del pipeline de audio. Cada módulo debe ser validado de forma aislada antes de integrar al flujo principal.

### 7.1 Neural Sync (Latencia Cero) [⏳ PENDIENTE — PRIORIDAD 1]
*Reducir la latencia percibida entre fin del turno del usuario e inicio de la respuesta de Kizuna.*
* [ ] Afinar `AUDIO_BUFFER_THRESHOLD` (actualmente 2048 bytes / ~128ms). Evaluar reducción a 1024.
* [ ] Implementar streaming parcial de audio en el frontend antes de `turn_complete`.
* [ ] Medir y documentar latencia p50/p95 antes y después.
* [ ] Validar que el AuctionService session-scoped no introduce overhead con el nuevo threshold.

### 7.2 Inyección de Zeitgeist [⏳ PENDIENTE — PRIORIDAD 2]
*Inyectar contexto dinámico del mundo en la sesión activa a través del injection_queue.*
* [ ] Definir fuentes de Zeitgeist: hora del día, clima emocional del grafo, eventos recientes del TimeSkip.
* [ ] Implementar `ZeitgeistProvider` como servicio independiente que alimenta el `injection_queue`.
* [ ] Frecuencia de inyección: máximo 1 inyección cada 60s para no saturar el contexto de Gemini.
* [ ] Validar con el Antropólogo que el tono del Zeitgeist respeta la personalidad del agente activo.

### 7.3 Agencia Social [⏳ PENDIENTE — PRIORIDAD 3]
*Kizuna actúa proactivamente sobre el grafo relacional entre sesiones.*
* [ ] Integrar TimeSkipService con el SleepManager para simular eventos sociales durante la ausencia del usuario.
* [ ] Implementar "Primer Mensaje Proactivo": Kizuna inicia la conversación basándose en eventos del Time-Skip.
* [ ] Definir umbrales de agencia: ¿cada cuánto tiempo puede Kizuna iniciar contacto?
* [ ] Persistir decisiones de agencia en el grafo JSON-LD para que sean parte de la memoria a largo plazo.

---

## 👁️ FASE 8: PRESENCIA FANTASMA [⏳ PENDIENTE]
*Desbloqueada después de completar Fase 7.*

---

**[FIN DEL DOCUMENTO - ACTUALIZADO POR EL CRONISTA 2026-03-01]**