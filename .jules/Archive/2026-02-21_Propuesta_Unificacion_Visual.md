# PROPUESTA DE MEJORA VISUAL: UNIFICACIÓN DE ESTÉTICA DARK WATER
**Fecha:** 2026-02-21
**Componente Afectado:** `frontend/src/components/SystemLogs.tsx`, `frontend/src/components/AgentRoster.tsx`, `frontend/src/components/JulesSanctuary.tsx`
**Nivel de Prioridad:** Alta

## 1. ESTADO ACTUAL (EL PROBLEMA)
Actualmente, existen desviaciones significativas del estándar "Dark Water" en componentes clave:
*   **SystemLogs.tsx**: Utiliza clases de utilidad de Tailwind (`text-cyan-800`, `opacity-60`) que resultan en un texto demasiado tenue y genérico. La fuente `font-mono` carece de la personalidad técnica de `Teko` o `Roboto Condensed`.
*   **AgentRoster.tsx**: El botón de "Crear Nuevo Agente" utiliza un borde discontinuo circular (`rounded-full`), lo cual es una forma demasiado orgánica y "amigable" para la estética agresiva de Kizuna. Los avatares de fallback son rectángulos simples sin tratamiento de bordes. Los botones de navegación, aunque usan el wrapper correcto, tienen una disposición flex estándar que podría ser más dinámica.
*   **JulesSanctuary.tsx**: Define formas complejas mediante `clip-path` en línea (`style={{ clipPath: "polygon(...)" }}`), lo que dificulta la mantenibilidad y reutilización. Los botones de acción (Captura, Sync) son rectángulos estándar con bordes simples, rompiendo la inmersión del "Shard UI".

## 2. JUSTIFICACIÓN ESTÉTICA (EL PORQUÉ)
*   **SystemLogs**: Según la sección 6.1 del Documento de Diseño, la tipografía técnica debe ser `Teko` o `Roboto Condensed` para evocar la densidad de información urbana de Persona. El color debe ser `var(--color-electric-blue)` para garantizar legibilidad contra el fondo abisal.
*   **AgentRoster**: La sección 2.2 estipula que "ningún panel principal debe tener cuatro esquinas de 90 grados". Los avatares y el botón de creación deben reflejar la fragmentación de cristales ("Dark Water Shards").
*   **JulesSanctuary**: La consistencia en los controles es vital. Todos los elementos interactivos deben seguir la geometría agresiva definida en la sección 8 (Botones Shard).

## 3. SOLUCIÓN TÉCNICA (EL CÓDIGO)

### A. Refactorización de SystemLogs.tsx
Reemplazar las clases de Tailwind con variables CSS y tipografía correcta.

```tsx
// Antes
<div className="font-technical text-xs text-cyan-800 tracking-widest mb-1 border-b border-cyan-900/30 w-32">
  SYS.LOG //
</div>

// Propuesta
<div className="font-technical text-sm text-electric-blue tracking-widest mb-1 border-b border-electric-blue/30 w-32 drop-shadow-[0_0_5px_rgba(0,209,255,0.5)]">
  SYS.LOG //
</div>
// Y para los logs individuales, usar font-mono pero con color --color-electric-blue con opacidad variable
```

### B. Geometría de AgentRoster.tsx
Aplicar `clip-path` a los avatares y al contenedor de "Nuevo Agente".

```css
/* Nuevo estilo en KizunaHUD.css */
.shape-shard-avatar {
  clip-path: polygon(10% 0, 100% 0, 100% 90%, 90% 100%, 0 100%, 0 10%);
}

.shape-shard-create {
  clip-path: polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%); /* Hexágono agresivo */
}
```

### C. Estandarización de JulesSanctuary.tsx
Extraer el `clip-path` a una clase CSS y aplicar el estilo de botón Shard.

```css
/* En KizunaHUD.css */
.shape-modal-shard {
  clip-path: polygon(2% 0, 100% 0, 100% 95%, 98% 100%, 0 100%, 0 5%);
}
```

```tsx
// En el componente
<div className="... shape-modal-shard ...">
  ...
  <button className="kizuna-shard-btn-wrapper ...">
    <div className="kizuna-shard-btn-inner">
      <Camera size={16} /> CAPTURE FRAME
    </div>
  </button>
</div>
```

## 4. IMPACTO ESPERADO
*   **Coherencia Visual**: La interfaz se sentirá como un sistema operativo unificado y no como una colección de componentes dispares.
*   **Legibilidad**: El uso de colores de alto contraste y fuentes técnicas mejorará la lectura de logs y estados.
*   **Inmersión**: La eliminación de formas orgánicas (círculos, rectángulos perfectos) reforzará la atmósfera "Dark Water" y tecnológica.
