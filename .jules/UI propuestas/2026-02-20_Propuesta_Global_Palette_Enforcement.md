# PROPUESTA DE MEJORA VISUAL: IMPERIO DE LA PALETA GLOBAL (ABYSSAL COLOR SCHEME)
**Fecha:** 2026-02-20
**Componente Afectado:** Global (tailwind.config.js, frontend/src/KizunaHUD.css, todos los componentes)
**Nivel de Prioridad:** Crítica (Fundacional)

## 1. ESTADO ACTUAL (EL PROBLEMA)
El código base actual utiliza una mezcla de variables CSS personalizadas (`var(--color-electric-blue)`) y clases de utilidad de Tailwind (`bg-cyan-500`, `text-cyan-400`, `border-slate-700`).

Esta discrepancia crea un ruido visual sutil pero destructivo. El cian estándar de Tailwind (#06b6d4) es más "corporativo" y menos vibrante que el Electric Blue (#00D1FF) definido en el diseño. El gris pizarra (#334155) carece del matiz azul profundo del "Vintage Navy" (#112D54).

## 2. JUSTIFICACIÓN ESTÉTICA (EL PORQUÉ)
La Sección 4 del documento de diseño ("Teoría del Color Abyssal") es innegociable: "El resultado es un ecosistema oscuro donde la oscuridad absoluta (#000000) se prohíbe... reemplazándose con azules y grises marinos insondables".

Usar colores genéricos rompe la ilusión de estar sumergido en el "Mar de las Almas". La coherencia cromática es lo que separa una app web de un "motor de juego".

## 3. SOLUCIÓN TÉCNICA (EL CÓDIGO)
Extender la configuración de Tailwind (`tailwind.config.js` si existe, o crearlo) para mapear las variables CSS del HUD a nombres de clases utilitarias semánticas.

```javascript
// tailwind.config.js (Propuesta)
module.exports = {
  theme: {
    extend: {
      colors: {
        'electric-blue': 'var(--color-electric-blue)', // #00D1FF
        'vintage-navy': 'var(--color-vintage-navy)',   // #112D54
        'abyssal-black': 'var(--color-abyssal-black)', // #05080F
        'translucent-cyan': 'var(--color-translucent-cyan)',
        'alert-red': 'var(--color-alert-red)',
      }
    }
  }
}
```

Luego, auditar y reemplazar todas las instancias de `cyan-400`, `slate-900`, etc., por `text-electric-blue`, `bg-abyssal-black`, etc.

## 4. IMPACTO ESPERADO
1.  **Uniformidad Absoluta:** Todos los elementos, desde bordes hasta textos, compartirán el mismo ADN cromático.
2.  **Vibración Correcta:** El Electric Blue real "fracturará el plano de la interfaz" con la intensidad requerida.
3.  **Mantenibilidad:** Cambiar el tema en `KizunaHUD.css` propagará el cambio a toda la aplicación instantáneamente.
