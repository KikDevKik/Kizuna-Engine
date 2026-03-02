# KIZUNA ENGINE — GEMINI LIVE API: NOTAS TÉCNICAS
## Actualizado: 3 de Marzo de 2026 | SDK 1.65.0

---

## MODELO ACTIVO

```
gemini-2.5-flash-native-audio-preview-12-2025
```

**Características claves:**
- Procesamiento de audio PCM nativo (sin pipeline ASR/TTS separados)
- Captura prosodia, emoción, vacilación en la voz
- VAD (Voice Activity Detection) server-side automático
- Pensamiento extendido activo por defecto (`thought=True` en respuestas)
- Preview: inconsistencia de timbre entre turnos (limitación conocida de Google)

---

## CONFIGURACIÓN DE SESIÓN (IMPLEMENTACIÓN ACTUAL)

```python
# backend/app/services/gemini_live.py

def _get_config(self, system_instruction: str, voice_name: str = "Puck") -> dict:
    return {
        "response_modalities": ["AUDIO"],       # Top-level, NO dentro de generation_config
        "system_instruction": types.Content(
            parts=[types.Part(text=system_instruction)]
        ),
        "speech_config": types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name=voice_name      # Kore, Puck, Aoede, Charon, Fenrir
                )
            )
        ),
        "tools": [],                            # CRÍTICO: AFC deshabilitado en Live
    }
```

**Voces disponibles:** Aoede, Kore, Puck, Charon, Fenrir

---

## FLUJO DE AUDIO CORRECTO (SDK 1.65.0)

### Envío de audio (cliente → Gemini)

```python
# Enviar chunks de audio continuo
await session.send_realtime_input(
    audio=types.Blob(
        data=bytes(audio_buffer),       # PCM 16kHz 16-bit mono
        mime_type="audio/pcm;rate=16000"
    )
)

# Señal EOT cuando el usuario deja de hablar
await session.send_realtime_input(audio_stream_end=True)
# Gemini activa su VAD y genera respuesta
```

### Recepción de audio (Gemini → cliente)

```python
async for response in session.receive():
    # Ruta principal en SDK 1.65.0
    if hasattr(response, 'data') and response.data:
        audio_data = response.data
    # Ruta alternativa (partes del model_turn)
    elif (response.server_content and 
          response.server_content.model_turn and
          response.server_content.model_turn.parts):
        for part in response.server_content.model_turn.parts:
            if hasattr(part, 'inline_data') and part.inline_data:
                audio_data = part.inline_data.data
                break
    
    # Detectar fin de turno del agente
    if (response.server_content and 
        response.server_content.turn_complete):
        auction_service.release(agent_id)
```

**Formato de respuesta:** PCM 24kHz (diferente al input de 16kHz)

---

## ERRORES HISTÓRICOS Y SOLUCIONES

### Error: AFC activo bloquea audio
**Síntoma:** `AFC is enabled with max remote calls: 10` × múltiples veces, sin respuesta.
**Causa:** Gemini entra en loop de tool evaluation antes de generar audio.
**Solución:** `tools=[]` en LiveConnectConfig.

### Error: `response_modalities` dentro de `generation_config`
**Síntoma:** `1 validation error for LiveConnectConfig generation_config.response_modalities Extra inputs are not permitted`
**Causa:** `response_modalities` es campo top-level, NO dentro de `generation_config`.
**Solución:** Mover al nivel superior del dict de config.

### Error: SDK 0.3.0 incompatible
**Síntoma:** `send_realtime_input` no existe, `end_of_turn` nunca llega, silencio permanente.
**Causa:** SDK desactualizado. `send_realtime_input` y `audio_stream_end` son APIs de versiones posteriores.
**Solución:** `pip install google-genai==1.65.0`

### Error: Mezcla de audio y texto corrompe historial
**Síntoma:** Agente deja de responder después de primera inyección de texto.
**Causa:** El modelo `native-audio-preview` no acepta mensajes `client_content` de texto mezclados con `realtime_input` de audio.
**Solución temporal:** Deshabilitar inyecciones de texto en sesiones Live (AUDIO-01).

### Error: `[object Object]` en WebSocket
**Síntoma:** Backend recibe `[object Object]` en lugar de JSON parseado.
**Causa:** `ws.send(objetoJS)` sin `JSON.stringify()`.
**Solución:** Siempre usar `ws.send(JSON.stringify({ type: 'end_of_turn' }))`.

### Error: `websocket.disconnect` dispara session_closed_event prematuramente
**Síntoma:** `receive_from_gemini` sale inmediatamente, sin logs de respuesta.
**Causa:** `session_closed_event.is_set()` antes de que `receive_from_gemini` empiece a iterar.
**Solución:** Check del event DENTRO del loop `async for`, no ANTES de empezar.

### Error: InjectionLoop spam post-cierre
**Síntoma:** "InjectionLoop: Session closed. Stopping injections." × 50 veces.
**Causa:** `break` dentro de `except asyncio.TimeoutError` con nivel de anidamiento incorrecto.
**Solución:** Flag `running = False` + `continue` garantiza salida del `while True`.

---

## COMPORTAMIENTO DEL MODELO PREVIEW

### Mensajes `thought=True`
El modelo 2.5 Flash tiene **pensamiento extendido activo por defecto**. Los primeros mensajes de respuesta contienen tokens de razonamiento interno (`thought=True`). Son normales y preceden al audio real.

```
📥 thought=True  ← razonamiento interno
📥 thought=True  
📥 thought=None  ← aquí empieza el audio real
🎤 Auction Won
```

### Inconsistencia de voz (VOICE-01)
El modelo preview no tiene fijación de timbre estable entre turnos. La voz puede mutar de tonalidad, acento y velocidad entre una respuesta y la siguiente. **Es una limitación de Google, no del código.** Se resuelve al pasar el modelo a GA.

### Requerimientos de entrada
- Hablar lento, claro y con volumen suficiente
- El VAD del servidor necesita silencio claro al final de la frase
- Audio a bajo volumen = "ruido de fondo" para el modelo = sin respuesta

---

## INYECCIONES (ESTADO ACTUAL)

### Deshabilitadas en Live (AUDIO-01)
Las inyecciones de SubconsciousMind y ReflectionMind están deshabilitadas en sesiones Live porque el modelo nativo-audio trata los mensajes `client_content` de texto como corrupción del historial de conversación.

### Pendiente de investigación (Fase 7 - AUDIO-01)
Con SDK 1.65.0, investigar:
- ¿Existe un modo de inyección que sea compatible con `realtime_input`?
- ¿`session.send(input="texto", end_of_turn=False)` es válido en el modelo nativo?
- ¿Los `system_instruction` pueden actualizarse mid-session?

---

## HERRAMIENTAS (AFC)

AFC (Automatic Function Calling) está **deshabilitado** en sesiones Live (`tools=[]`).

Las herramientas siguen activas en:
- SoulForge (`generate_content`): `spawn_stranger_tool`
- Ritual: generación procedural de agentes

Para Fase 7 (Reactive Search), investigar si `tools` puede reactivarse en Live sin bloquear el pipeline de audio.

---

## IMPLEMENTACIÓN DE REFERENCIA (Google Docs)

El patrón recomendado por Google para servidor-a-servidor:

```python
# Envío continuo de audio
async def send_realtime(session):
    while True:
        msg = await audio_queue.get()
        await session.send_realtime_input(audio=msg)
        # msg = {"data": bytes_pcm, "mime_type": "audio/pcm"}

# Recepción de respuestas
async def receive_audio(session):
    while True:
        turn = session.receive()
        async for response in turn:
            if response.server_content and response.server_content.model_turn:
                for part in response.server_content.model_turn.parts:
                    if part.inline_data and isinstance(part.inline_data.data, bytes):
                        # Audio 24kHz listo para reproducir
                        play_buffer.put_nowait(part.inline_data.data)
        # Vaciado en interrupción
        while not play_buffer.empty():
            play_buffer.get_nowait()
```

**Nota:** En Kizuna Engine, el VAD del frontend se encarga de detectar el silencio y enviar `audio_stream_end=True` — no se implementa el loop de vaciado ya que una sola sesión por usuario hace que la interrupción sea gestionada por el frontend.

---

*Documento técnico actualizado: 3 de Marzo de 2026 | El Cronista*