ws.onerror = (error) => {
        console.error('WebSocket error (onerror event)', error);
        setStatus('error');
      };

      // ---------------- REEMPLAZA TODO EL BLOQUE ONMESSAGE POR ESTO ----------------
      ws.onmessage = async (event) => {
        try {
          // 1. EL GUARD CLAUSE: ¿Materia densa (Binario) o Instrucción táctica (String)?
          if (event.data instanceof ArrayBuffer) {
            // --- BINARY AUDIO FLOW (Kizuna Engine Optimized) ---
            setIsAiSpeaking(true);

            // Vista directa en memoria, sin el peso del Base64
            const int16Data = new Int16Array(event.data);
            const float32Data = new Float32Array(int16Data.length);

            // Normalización matemática directa
            for (let i = 0; i < int16Data.length; i++) {
                float32Data[i] = int16Data[i] / 32768.0;
            }

            // Inyección al AudioContext
            const buffer = createAudioBuffer(ctx, float32Data);
            const source = ctx.createBufferSource();
            source.buffer = buffer;
            source.connect(ctx.destination);

            const currentTime = ctx.currentTime;
            const startTime = Math.max(currentTime, nextStartTimeRef.current);
            source.start(startTime);
            nextStartTimeRef.current = startTime + buffer.duration;
            
            // ¡Baton Pass! Retorno temprano. Si es audio, no intentamos parsear JSON.
            return; 
          }

          // 2. TEXT / CONTROL FLOW (Si el motor llega aquí, event.data es un string JSON)
          if (typeof event.data === 'string') {
            const message = JSON.parse(event.data) as ServerMessage;

            if (message.type === 'text') {
                setLastAiMessage(message.data);
            } else if (message.type === 'turn_complete') {
              console.log("Turn complete signal received.");
              setIsAiSpeaking(false);
            }
          }
        } catch (e) {
          console.error("Error processing message", e);
        }
      };
      // ---------------- FIN DEL BLOQUE ONMESSAGE ----------------

      // 4. Get User Media
      const stream = await navigator.mediaDevices.getUserMedia({