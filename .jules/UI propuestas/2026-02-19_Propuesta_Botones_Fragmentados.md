# PROPUESTA DE MEJORA VISUAL: BOTONES DE AGRESIÓN GEOMÉTRICA (FRAGMENTO CRÍTICO)

**Fecha:** 2026-02-19
**Componente Afectado:** `frontend/src/App.tsx`, `frontend/src/KizunaHUD.css`
**Nivel de Prioridad:** Media/Alta

## 1. ESTADO ACTUAL (EL PROBLEMA)
El botón principal de conexión ("INITIATE LINK" / "TERMINATE") en `App.tsx` utiliza una transformación `skew` simple para lograr un aspecto inclinado.
```jsx
className="... px-10 py-4 font-monumental ... skew-x-[-10deg]"
```
Si bien cumple con la regla básica de evitar ortogonalidad pura, sigue siendo un cuadrilátero predecible. Carece de la fragmentación irregular ("Dark Water Shards") y los cortes agresivos que definen la estética de *Persona 3 Reload* y *Wuthering Waves*, donde los elementos interactivos parecen pedazos de cristal roto o metal cortado.

## 2. JUSTIFICACIÓN ESTÉTICA (EL PORQUÉ)
La sección **2.2. Arquitectura de clip-path y Generación de Fragmentos de Vidrio** establece que los paneles de alerta o acción crítica deben usar un polígono de "Fragmento Crítico":
> `polygon(0% 20%, 20% 0%, 100% 0%, 100% 80%, 80% 100%, 0% 100%)`
> "Un rectángulo profundamente fragmentado en las esquinas opuestas. Sugiere un pedazo de cristal pesado y contundente".

Además, para que este recorte sea legible sobre el fondo oscuro, se requiere la técnica de "Borde Poligonal Iluminado" (Wrapper + Inner Content) descrita en la sección **2.2.1**.

## 3. SOLUCIÓN TÉCNICA (EL CÓDIGO)
Se propone crear un componente reutilizable `KizunaButton` o clases CSS que implementen la estructura de doble capa para lograr bordes brillantes en formas irregulares.

**CSS (KizunaHUD.css):**
```css
/* Wrapper para el borde brillante */
.kizuna-shard-btn-wrapper {
  position: relative;
  display: inline-block;
  padding: 2px; /* Grosor del borde */
  background: var(--color-electric-blue); /* Color del borde */
  clip-path: polygon(0% 20%, 10% 0%, 100% 0%, 100% 80%, 90% 100%, 0% 100%);
  transition: all 0.3s cubic-bezier(0.25, 1, 0.5, 1);
  filter: drop-shadow(0 0 5px rgba(0, 209, 255, 0.4));
}

.kizuna-shard-btn-wrapper:hover {
  filter: drop-shadow(0 0 15px rgba(0, 209, 255, 0.8));
  transform: scale(1.05);
}

/* Interior oscuro del botón */
.kizuna-shard-btn-inner {
  background: rgba(5, 8, 15, 0.95); /* Negro Abisal */
  color: var(--color-electric-blue);
  font-family: 'Roboto Condensed', sans-serif;
  font-weight: 700;
  letter-spacing: 0.1em;
  padding: 12px 32px;
  clip-path: polygon(0% 20%, 10% 0%, 100% 0%, 100% 80%, 90% 100%, 0% 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  width: 100%;
  height: 100%;
}

.kizuna-shard-btn-wrapper:active .kizuna-shard-btn-inner {
  background: var(--color-electric-blue);
  color: #000;
}
```

**React Implementation (App.tsx):**
```jsx
<button onClick={handleToggleConnection} className="kizuna-shard-btn-wrapper">
  <span className="kizuna-shard-btn-inner">
     {connected ? 'TERMINATE_LINK' : 'INITIATE_LINK'}
  </span>
</button>
```

## 4. IMPACTO ESPERADO
*   **Agresión Visual:** El botón dejará de ser un rectángulo pasivo para convertirse en una "herramienta" cortante.
*   **Feedback Táctil:** El cambio de color invertido en `:active` y el `drop-shadow` intenso en `:hover` darán una respuesta inmediata y satisfactoria.
*   **Coherencia:** Unifica los controles con la estética fragmentada del resto de la interfaz.
