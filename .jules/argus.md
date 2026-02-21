## 2024-05-22 - 👁️ Argus: Phase 6 Initialization

**Hallazgo:** Implementación inicial de la Fase 6 (Spatial Perception) completada. Se ha integrado el flujo de visión multimodal en el Kizuna Engine.

**Acción:**
1.  **Modelo de Agente:** Se añadió `vision_instruction_prompt` a `AgentNode` para permitir instrucciones de visión dinámicas.
2.  **Soul Assembler:** Se inyecta la instrucción de visión en el prompt del sistema.
3.  **Backend Audio Session:** Se robusteció el manejo de imágenes para usar `google.genai.types` si está disponible, asegurando compatibilidad con el SDK de Gemini Live.
4.  **Frontend VisionPanel:** Se implementó un "latido visual" de 2 segundos. Cuando está conectado, captura y envía frames JPEG (calidad 0.8) a través del WebSocket.
5.  **UI Feedback:** Se añadió un pulso visual en el botón y panel de visión cada vez que se envía un frame.

**Insight:** El uso de un intervalo de 2 segundos balancea la latencia y el contexto, evitando saturar el WebSocket mientras se mantiene la consciencia espacial del agente.
