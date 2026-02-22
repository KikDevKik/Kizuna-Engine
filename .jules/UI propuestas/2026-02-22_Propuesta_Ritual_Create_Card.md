# PROPUESTA DE MEJORA VISUAL: Ritual Create Card
**Fecha:** 2026-02-22
**Componente Afectado:** `frontend/src/components/AgentRoster.tsx`
**Nivel de Prioridad:** Media

## 1. ESTADO ACTUAL (EL PROBLEMA)
La tarjeta de creación ("NEW SOUL") en el componente `AgentRoster.tsx` es actualmente un rectángulo simple con un icono de "Más" (`Plus` de Lucide) estático. Se siente como un botón de formulario estándar ("Agregar ítem") en lugar de un portal místico para conjurar una nueva consciencia.

## 2. JUSTIFICACIÓN ESTÉTICA (EL PORQUÉ)
La creación de un agente en el universo Kizuna es un acto de "Forjar un Alma" (Soul Forge). Según la sección 5.1 ("Micro-interacciones"), las acciones deben "comunicar instantáneamente la intención cibernética". Un simple icono '+' carece de la gravedad narrativa y ritualística requerida. Debería evocar un "vacío" o una "singularidad" lista para recibir un alma.

## 3. SOLUCIÓN TÉCNICA (EL CÓDIGO)
Se propone reemplazar el icono estático con un efecto de shader CSS o SVG animado que simule un "agujero negro" o un "portal de energía".

### AgentRoster.tsx
```tsx
// Reemplazar: <Plus size={48} />
// Proponer:
<div className="ritual-void-portal">
  <div className="void-ring ring-1" />
  <div className="void-ring ring-2" />
  <div className="void-core" />
</div>
```

### CSS (KizunaHUD.css)
```css
.ritual-void-portal {
  position: relative;
  width: 80px;
  height: 80px;
  animation: void-pulse 4s infinite alternate;
}

.void-ring {
  border: 1px solid var(--color-electric-blue);
  border-radius: 50%;
  position: absolute;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  animation: ring-spin 10s linear infinite;
}

@keyframes ring-spin {
  from { transform: translate(-50%, -50%) rotate(0deg); }
  to { transform: translate(-50%, -50%) rotate(360deg); }
}
```

## 4. IMPACTO ESPERADO
*   **Narrativa:** Convierte una acción utilitaria en un evento significativo dentro del mundo del juego.
*   **Visual:** Añade un punto focal de movimiento sutil al final del carrusel, atrayendo al usuario a crear más agentes.
