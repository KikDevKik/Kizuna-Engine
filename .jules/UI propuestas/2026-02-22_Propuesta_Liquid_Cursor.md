# PROPUESTA DE MEJORA VISUAL: Custom Liquid Cursor
**Fecha:** 2026-02-22
**Componente Afectado:** `frontend/src/App.tsx` / `frontend/src/KizunaHUD.css`
**Nivel de Prioridad:** Media

## 1. ESTADO ACTUAL (EL PROBLEMA)
El sistema utiliza el cursor predeterminado del sistema operativo (puntero/flecha). Este elemento externo rompe la "cuarta pared" y la inmersión del usuario, recordándole que está navegando en una página web y no interactuando con una consciencia líquida o un entorno de realidad mixta.

## 2. JUSTIFICACIÓN ESTÉTICA (EL PORQUÉ)
La interfaz se describe como un "Mar de las Almas" donde los elementos están "suspendidos bajo el agua" (Sección 1). El punto de interacción (el cursor) debería comportarse como un objeto físico que desplaza fluido o emite energía, en lugar de ser una flecha estática. Un cursor personalizado refuerza la física de "Dark Water" (Sección 3.2) y la sensación de resistencia del medio.

## 3. SOLUCIÓN TÉCNICA (EL CÓDIGO)
Se propone ocultar el cursor del sistema (`cursor: none`) y renderizar un componente React personalizado que siga la posición del mouse con un ligero retraso (spring physics) para simular la viscosidad del agua.

### App.tsx
```tsx
// Nuevo componente LiquidCursor
const LiquidCursor = () => {
  // Lógica de seguimiento de mouse con useSpring de framer-motion
  // ...
  return (
    <motion.div className="liquid-cursor-outer" style={{ x, y }} />
    <motion.div className="liquid-cursor-inner" style={{ x, y }} />
  );
}
```

### CSS (KizunaHUD.css)
```css
body {
  cursor: none; /* Ocultar cursor nativo */
}

.liquid-cursor-outer {
  position: fixed;
  width: 40px;
  height: 40px;
  border: 1px solid var(--color-electric-blue);
  border-radius: 50%;
  pointer-events: none;
  z-index: 9999;
  mix-blend-mode: exclusion;
  transition: transform 0.1s;
}

.liquid-cursor-inner {
  position: fixed;
  width: 8px;
  height: 8px;
  background: var(--color-electric-blue);
  border-radius: 50%;
  pointer-events: none;
  z-index: 10000;
}
```

## 4. IMPACTO ESPERADO
*   **Inmersión Total:** Elimina el último vestigio del sistema operativo anfitrión.
*   **Feedback:** El cursor puede reaccionar (expandirse/cambiar de color) al hacer hover sobre elementos interactivos, proporcionando feedback visual inmediato.
