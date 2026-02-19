# PROPUESTA DE MEJORA VISUAL: MICRO-INTERACCIÓN GLITCH EN BOTÓN DE INICIO
**Fecha:** 2024-05-23
**Componente Afectado:** `frontend/src/App.tsx` (Botón "INITIATE LINK")
**Nivel de Prioridad:** Media

## 1. ESTADO ACTUAL (EL PROBLEMA)
Actualmente, el botón principal "INITIATE LINK" tiene un efecto de hover estándar (cambio de color de fondo y borde). Aunque cumple con la paleta de colores, carece de la "inestabilidad digital" propia de la estética *Dark Water* y *Persona*. Se siente demasiado estable para ser un enlace neuronal.

## 2. JUSTIFICACIÓN ESTÉTICA (EL PORQUÉ)
Según la sección 5.1 del GDD ("Micro-interacciones y Reactividad"), el sistema debe comunicar "intención cibernética" y "violencia electromagnética". Un simple cambio de color es insuficiente. Necesitamos que el botón parezca "luchar" por mantener la conexión, con un efecto de desplazamiento RGB o *glitch* al pasar el cursor, similar a los menús de combate de P3R.

## 3. SOLUCIÓN TÉCNICA (EL CÓDIGO)
Se sugiere añadir una clase utilitaria `.glitch-hover` en `KizunaHUD.css` y aplicarla al botón.

**En `frontend/src/KizunaHUD.css`:**

```css
/* Efecto Glitch RGB */
@keyframes glitch-skew {
  0% { transform: skew(0deg); }
  20% { transform: skew(-2deg); }
  40% { transform: skew(2deg); }
  60% { transform: skew(-1deg); }
  80% { transform: skew(1deg); }
  100% { transform: skew(0deg); }
}

.btn-glitch:hover {
  animation: glitch-skew 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94) both infinite;
  box-shadow:
    2px 0 rgba(255,0,0,0.5),
    -2px 0 rgba(0,255,255,0.5);
}

.btn-glitch:hover::before {
  content: attr(data-text);
  position: absolute;
  left: -2px;
  text-shadow: 1px 0 red;
  background: var(--color-abyssal-black);
  overflow: hidden;
  clip-path: polygon(0 0, 100% 0, 100% 35%, 0 35%);
  animation: glitch-anim-1 2s infinite linear alternate-reverse;
}
```

**En `frontend/src/App.tsx`:**
Añadir `data-text="INITIATE LINK"` y la clase `btn-glitch`.

## 4. IMPACTO ESPERADO
- **Feedback Táctil:** El usuario sentirá que el sistema está "vivo" y reacciona físicamente a su presencia.
- **Coherencia Narrativa:** Refuerza la idea de que estamos operando una máquina compleja e inestable, no una web app corporativa.
