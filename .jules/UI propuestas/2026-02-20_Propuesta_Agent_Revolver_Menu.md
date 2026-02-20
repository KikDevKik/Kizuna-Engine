# PROPUESTA DE MEJORA VISUAL: REVOLUCIÓN DEL SELECTOR DE AGENTES (REVOLVER CYLINDER)
**Fecha:** 2026-02-20
**Componente Afectado:** frontend/src/components/AgentRoster.tsx
**Nivel de Prioridad:** Alta

## 1. ESTADO ACTUAL (EL PROBLEMA)
El componente `AgentRoster.tsx` implementa un carrusel pseudo-3D lineal. Las tarjetas se desplazan horizontalmente (`x` translation) y giran ligeramente (`rotateY`), pero la disposición fundamental es una fila recta apilada. Esto carece de la profundidad envolvente y la "agresión geométrica" de un verdadero menú circular, sintiéndose más como un "cover flow" genérico que como un mecanismo de selección táctica.

Además, la lógica actual de `getCardStyle` mezcla la posición (layout) con la animación de entrada, resultando en un código difícil de mantener y extender para efectos más complejos como la órbita.

## 2. JUSTIFICACIÓN ESTÉTICA (EL PORQUÉ)
Según la Sección 7 del "Documento de Diseño UI Abisal Kizuna P3R", el selector de agentes debe "abandonar las listas desplegables o cuadrículas convencionales y rinda homenaje directo a los icónicos menús de comandos de combate circulares... también conocidos como menú de cilindro de revólver".

La especificación (Sección 7.1) exige explícitamente una arquitectura donde "los elementos no se sitúan mediante flexbox... sino que orbitan al personaje central en un lienzo de profundidad espacial" utilizando `rotateY` desde un eje central y `translateZ` para el radio, no `translateX`. Esto crea una sensación de "inercia y peligro táctico" (Sección 7.2) fundamental para la inmersión en el "Mar de las Almas".

## 3. SOLUCIÓN TÉCNICA (EL CÓDIGO)
Reemplazar la lógica de cálculo lineal por una trigonométrica basada en el índice angular.

```tsx
// Nueva lógica de renderizado para AgentRoster (Concepto)

const radius = 400; // Radio del cilindro
const theta = 360 / agents.length; // Ángulo por agente

// En el render del mapa de agentes:
{agents.map((agent, index) => {
  const angle = index * theta;
  // La rotación del contenedor padre 'cylinder-carousel-axis' se encarga de girar el carrusel.
  // Cada tarjeta tiene una posición fija en el cilindro:
  const cardStyle = {
    transform: `rotateY(${angle}deg) translateZ(${radius}px)`,
    // Agresión geométrica: inclinación base de -15deg, excepto el activo (-2deg)
    rotateZ: activeIndex === index ? "-2deg" : "-15deg",
    opacity: activeIndex === index ? 1 : 0.4
  };

  return (
    <motion.div style={cardStyle} ... >
      {/* Contenido con Clip-Path agresivo */}
    </motion.div>
  );
})}
```

El contenedor padre debe tener `transformStyle: "preserve-3d"` y rotar inversamente al índice activo (`rotateY: activeIndex * -theta`) para traer la tarjeta seleccionada al frente (Z=0).

## 4. IMPACTO ESPERADO
1.  **Inmersión Táctica:** El usuario sentirá que está manipulando un mecanismo físico (el cilindro de un revólver) en lugar de scrollear una lista.
2.  **Fidelidad Visual:** Alineación perfecta con la estética "Persona 3 Reload" y "Wuthering Waves" descrita en el manifiesto.
3.  **Dinamismo:** La transición rotacional aporta una energía cinética ("snap" mecánico) superior al deslizamiento lineal.
