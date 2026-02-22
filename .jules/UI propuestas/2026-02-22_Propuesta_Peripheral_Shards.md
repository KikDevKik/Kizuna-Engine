# PROPUESTA DE MEJORA VISUAL: Shardification of Peripheral Panels
**Fecha:** 2026-02-22
**Componente Afectado:** `frontend/src/components/VisionPanel.tsx`, `frontend/src/components/EpistemicPanel.tsx`
**Nivel de Prioridad:** Alta

## 1. ESTADO ACTUAL (EL PROBLEMA)
Actualmente, los paneles periféricos utilizan clases de utilidad de Tailwind como `rounded-bl-xl` y `rounded-tl-3xl` para sus bordes. Esto resulta en esquinas redondeadas suaves y ortogonales que son características de interfaces "amigables" o de consumo masivo (Material Design, iOS). Carecen de la "agresión geométrica" y la sensación de "cristal fracturado" que define la estética "Dark Water".

## 2. JUSTIFICACIÓN ESTÉTICA (EL PORQUÉ)
El "Documento de Diseño UI Abisal" (Sección 2.2) establece explícitamente que "ningún panel principal debe tener cuatro esquinas de 90 grados" y debe presentar "cortes oblicuos, muescas tecnológicas y asimetrías extremas". El uso de `border-radius` contradice directamente la directiva de "Fragmentación Visual" y rompe la inmersión en un entorno hostil y subacuático.

## 3. SOLUCIÓN TÉCNICA (EL CÓDIGO)
Se propone reemplazar las clases `rounded-*` con propiedades `clip-path` personalizadas definidas en `KizunaHUD.css` o directamente en línea.

### VisionPanel.tsx
```tsx
// Reemplazar: rounded-bl-3xl
// Proponer:
<motion.div
  className="..."
  style={{ clipPath: "polygon(10% 0, 100% 0, 100% 100%, 0 100%, 0 10%)" }} // Corte en esquina superior izquierda
>
```

### EpistemicPanel.tsx
```tsx
// Reemplazar: rounded-tl-3xl
// Proponer:
<motion.div
  className="..."
  style={{ clipPath: "polygon(0 0, 100% 0, 100% 90%, 90% 100%, 0 100%)" }} // Corte en esquina inferior derecha
>
```

Además, se debe agregar un `wrapper` con `background: var(--color-electric-blue)` y un `padding: 1px` para simular el borde brillante, ya que `clip-path` recorta los bordes CSS estándar (Sección 2.2.1).

## 4. IMPACTO ESPERADO
*   **Inmersión:** La interfaz se sentirá más "peligrosa" y tecnológica.
*   **Coherencia:** Los paneles laterales coincidirán visualmente con los botones y el roster de agentes.
*   **Narrativa:** Refuerza la idea de que la interfaz es un "cristal roto" a través del cual observamos el Abismo.
