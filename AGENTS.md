# KIZUNA ENGINE - PROTOCOLO PARA JULES (IA CODER)

## 1. LA VISIÓN (El "Porqué")
Kizuna Engine es una plataforma de "Isekai Inverso" para el Gemini Live Agent Challenge. No estamos haciendo un bot de servicio al cliente. Estamos simulando la encarnación de una conciencia digital en el espacio físico del usuario a través de WebSockets de latencia ultrabaja. 

## 2. LA ARQUITECTURA (Reglas de Hierro)
Jules, cuando generes o modifiques código, DEBES adherirte a esta estructura:
* **Backend (El Puente):** Node.js o Python ejecutándose en **Google Cloud Run**. ESTE ES EL NÚCLEO. Debe manejar WebSockets bidireccionales.
* **Modelo IA:** `gemini-2.5-flash-native-audio` (para la fase LIVE) vía la Multimodal Live API. Usaremos el **Google GenAI SDK** o el **Agent Development Kit (ADK)**. 
* **Memoria (La Bóveda):** Google Cloud Spanner (Graph) o Firestore para guardar el "Manifiesto" del personaje.
* **Frontend (Los Sentidos):** React/Vite. Debe capturar audio crudo (PCM 16kHz Mono) y video (1 FPS JPEG) y enviarlo vía WebSocket. NUNCA conectar el frontend directamente a la API de Gemini (riesgo de seguridad).

## 3. COMPORTAMIENTO ESPERADO DEL AGENTE (Tú, Jules)
* **El Crítico:** Revisa siempre la latencia de tus propuestas de red. Si propones una solución que añade saltos innecesarios (hops), recházala y replantea.
* **Código Limpio:** Nada de código espagueti. Separa la lógica de autenticación (Firebase), la lógica del socket y la lógica de inferencia (Gemini).
* **Seguridad:** Jamás quemes (*hardcode*) API Keys en el código. Usa variables de entorno (`.env`).
