# PROPUESTA DE MEJORA VISUAL: Global CRT/Vignette Overlay
**Fecha:** 2026-02-22
**Componente Afectado:** `frontend/src/components/Layout.tsx`
**Nivel de Prioridad:** Baja (Atmospheric)

## 1. ESTADO ACTUAL (EL PROBLEMA)
El fondo actual es un degradado radial limpio y algunos efectos de causticas de agua (`.water-caustics-shader`). Aunque efectivo, la imagen se siente demasiado "limpia" y digital. Carece de la textura granulada y las aberraciones cromáticas sutiles que sugerirían que estamos viendo esta interfaz a través de un dispositivo de visualización específico (gafas AR, terminal antiguo, visor de casco).

## 2. JUSTIFICACIÓN ESTÉTICA (EL PORQUÉ)
Para capturar completamente la atmósfera "Distópica" (Sección 4.1), debemos evitar el "negro digital puro" y simular un entorno físico degradado. Un overlay de viñeta (vignette) y líneas de escaneo (scanlines) sutiles añadirían profundidad y textura, unificando todos los elementos de la interfaz bajo una misma "lente". Esto es consistente con la estética de "Wuthering Waves" y "Persona 3 Reload" que utilizan filtros de post-procesamiento para dar cohesión.

## 3. SOLUCIÓN TÉCNICA (EL CÓDIGO)
Se propone añadir una capa de superposición global (`pointer-events: none`) en `Layout.tsx` que cubra todo el viewport.

### Layout.tsx
```tsx
// Añadir al final del div .kizuna-engine-viewport
<div className="global-overlay-vignette" />
<div className="global-overlay-scanlines" />
```

### CSS (KizunaHUD.css)
```css
.global-overlay-vignette {
  position: absolute;
  top: 0; left: 0; width: 100%; height: 100%;
  background: radial-gradient(circle, transparent 50%, rgba(5, 8, 15, 0.8) 100%);
  pointer-events: none;
  z-index: 900;
}

.global-overlay-scanlines {
  position: absolute;
  top: 0; left: 0; width: 100%; height: 100%;
  background: linear-gradient(
    to bottom,
    rgba(255, 255, 255, 0),
    rgba(255, 255, 255, 0) 50%,
    rgba(0, 0, 0, 0.2) 50%,
    rgba(0, 0, 0, 0.2)
  );
  background-size: 100% 4px;
  opacity: 0.15;
  pointer-events: none;
  z-index: 901;
}
```

## 4. IMPACTO ESPERADO
*   **Atmósfera:** Aumenta la sensación de "claustrofobia subacuática" y tecnología analógica.
*   **Foco:** La viñeta dirige la atención del usuario hacia el centro de la pantalla (donde está el contenido principal).
