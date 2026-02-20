# PROPUESTA DE MEJORA VISUAL: REFINAMIENTO DE REACTIVIDAD DEL KIZUNA CORE
**Fecha:** 2026-02-20
**Componente Afectado:** frontend/src/components/KizunaCore.tsx
**Nivel de Prioridad:** Alta

## 1. ESTADO ACTUAL (EL PROBLEMA)
La lógica actual en `KizunaCore.tsx` fuerza el estado visual "Listening" siempre que el sistema está conectado y la IA no está hablando. Esto sobrescribe el estado "Idle" (respiración líquida), resultando en que el núcleo se mantiene en su forma geométrica afilada (cristal) incluso cuando hay silencio absoluto.

```tsx
// Lógica Actual (Problemática)
if (status === 'connected') {
    if (isAiSpeaking) {
      visualState = 'speaking';
    } else {
      visualState = 'listening'; // <--- Sobrescribe "idle" incluso si no hay voz de usuario
    }
}
```

Esto diluye el impacto visual del evento de "Sincronización Cuántica" (cuando el usuario realmente habla) y hace que la interfaz se sienta estática y menos orgánica.

## 2. JUSTIFICACIÓN ESTÉTICA (EL PORQUÉ)
La Sección 5.1 del documento de diseño establece una clara distinción fenomenológica:
*   **Idle (Letargo Abisal):** "Forma orgánica ('blob') ... redondez ovalada fluctuante".
*   **Listening (Sincronización Cuántica):** "En el instante en que el micrófono captura sonido ... el Core se petrifica y cristaliza en un polígono afilado".

La transición entre lo orgánico (reposo) y lo cristalino (actividad) es crucial para la narrativa de que el sistema "despierta" ante la voz humana. Mantenerlo siempre cristalizado elimina esta narrativa.

## 3. SOLUCIÓN TÉCNICA (EL CÓDIGO)
Modificar la lógica de determinación de estado para respetar la señal de VAD (Voice Activity Detection) o `isListening` real.

```tsx
// Nueva Lógica Propuesta
let visualState = 'idle';

if (status === 'connected') {
  if (isAiSpeaking) {
    visualState = 'speaking'; // Expansión volumétrica
  } else if (isListening) {
    // isListening debe ser true SOLO cuando el usuario está hablando (VAD activo)
    visualState = 'listening'; // Cristalización agresiva (polígono)
  } else {
    visualState = 'idle'; // Respiración líquida (blob) durante el silencio conectado
  }
} else {
  visualState = 'idle';
}
```

Asegurar que la propiedad `transition` en CSS permita un cambio abrupto (`steps(2, end)`) para la entrada al estado listening, pero suave para el retorno a idle.

## 4. IMPACTO ESPERADO
1.  **Feedback Claro:** El usuario sabrá instantáneamente si el sistema lo está "escuchando" activamente o solo esperando.
2.  **Narrativa Visual:** La "vida" del Core se sentirá más reactiva y biológica, oscilando entre estados de flujo y estados de computación rígida.
