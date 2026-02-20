# PROPUESTA DE MEJORA VISUAL: AGRESIÓN GEOMÉTRICA EN NAVEGACIÓN (SHARD NAV)
**Fecha:** 2026-02-20
**Componente Afectado:** frontend/src/App.tsx (Header Navigation Buttons)
**Nivel de Prioridad:** Media

## 1. ESTADO ACTUAL (EL PROBLEMA)
La barra de navegación principal (Header) en `App.tsx` utiliza botones simples con `skew-x-[-10deg]` y bordes regulares. Aunque cumplen con la regla básica de no ser rectángulos ortogonales, carecen de la complejidad visual de los "shards" (fragmentos de vidrio) que definen el resto de la interfaz (como en `AgentRoster` o los botones de acción).

Se ven demasiado "web estándar con un transform CSS" en lugar de componentes de UI integrados en el motor gráfico.

## 2. JUSTIFICACIÓN ESTÉTICA (EL PORQUÉ)
La Sección 2.2 ("Arquitectura de clip-path y Generación de Fragmentos de Vidrio") estipula que "ningún panel principal debe tener cuatro esquinas de 90 grados" y debe recordar a "pedazos de cristal fracturado".

El Header es el elemento más persistente de la UI. Si sus controles son débiles geométricamente, debilita toda la ilusión. Los botones deben tener "cortes oblicuos, muescas tecnológicas y asimetrías extremas".

## 3. SOLUCIÓN TÉCNICA (EL CÓDIGO)
Reemplazar los botones `<button className="... skew-x ...">` por variantes de la clase `.kizuna-shard-btn-wrapper` (definida en `KizunaHUD.css`), posiblemente con una variante más delgada para la navegación superior.

```tsx
// Nuevo Botón de Navegación (Concepto)
<button
  onClick={() => setViewMode('core')}
  className={`kizuna-shard-nav-btn ${viewMode === 'core' ? 'active' : ''}`}
>
  <div className="shard-content">
    CORE VIEW
  </div>
</button>
```

Y en CSS, aplicar un `clip-path` específico para navegación (quizás un trapezoide invertido o un hexágono alargado):
```css
.kizuna-shard-nav-btn {
  clip-path: polygon(10% 0%, 100% 0%, 90% 100%, 0% 100%);
  /* ... estilos de borde brillante ... */
}
```

## 4. IMPACTO ESPERADO
1.  **Coherencia Visual:** La navegación se sentirá parte del mismo "chasis" metálico/cristalino que el resto de la app.
2.  **Jerarquía Clara:** Los botones con formas agresivas invitan más a la interacción que simples textos inclinados.
