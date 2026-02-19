# PROPUESTA DE MEJORA VISUAL: TRANSICIÓN DE FRAGMENTACIÓN (SHATTER EVENT)

**Fecha:** 2026-02-19
**Componente Afectado:** `frontend/src/App.tsx`, `frontend/src/components/AgentRoster.tsx`
**Nivel de Prioridad:** Crítica (Impacto Cinemático)

## 1. ESTADO ACTUAL (EL PROBLEMA)
La transición actual entre la vista del "Core" (un solo agente) y la vista "Roster" (selección múltiple) utiliza una animación estándar de `opacity` y `scale` (fade in/out).
```typescript
initial={{ opacity: 0, scale: 0.9 }}
animate={{ opacity: 1, scale: 1 }}
exit={{ opacity: 0, scale: 1.1, filter: 'blur(10px)' }}
```
Este comportamiento es funcional pero "web genérica". Carece de la violencia estética y la narrativa de "ruptura de la realidad" descrita en el documento de diseño para el evento de "Multimodal Gathering". No se siente como si la interfaz se rompiera para revelar una estructura más compleja; simplemente se desvanece.

## 2. JUSTIFICACIÓN ESTÉTICA (EL PORQUÉ)
La sección **5.2. Lógica Visual Transicional: "Multimodal Gathering"** establece que la transición no debe ser un *crossfade*, sino un evento físico de destrucción y reensamblaje ("Shatter").
> "La interfaz misma es el material destructible... los fragmentos de cristal no regresan de golpe a la vez, sino en una rapidísima cascada sucesiva (staggerChildren)."

Esta mecánica es esencial para elevar el Kizuna Engine de una herramienta de chat a una experiencia inmersiva similar a *Persona 3 Reload*, donde los menús se invocan mediante acciones físicas contundentes.

## 3. SOLUCIÓN TÉCNICA (EL CÓDIGO)
Se propone reemplazar el contenedor único de `AgentRoster` con un sistema de fragmentos controlados por `Framer Motion` con `staggerChildren`.

```typescript
// frontend/src/components/AgentRoster.tsx (Fragmento)

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.04, // Cascada rápida de cristales [5.2]
      delayChildren: 0.1
    }
  },
  exit: {
    opacity: 0,
    transition: { staggerChildren: 0.02, staggerDirection: -1 }
  }
};

const shardVariants = {
  hidden: {
    y: 50,
    opacity: 0,
    scale: 0.8,
    rotateX: -45,
    filter: "blur(10px)"
  },
  visible: {
    y: 0,
    opacity: 1,
    scale: 1,
    rotateX: 0,
    filter: "blur(0px)",
    transition: {
      type: "spring",
      stiffness: 250, // Impacto violento y seco
      damping: 20
    }
  },
  exit: {
    y: -50,
    opacity: 0,
    filter: "blur(10px)"
  }
};

// Implementación en el render
return (
  <motion.div
    variants={containerVariants}
    initial="hidden"
    animate="visible"
    exit="exit"
    className="w-full h-full flex items-center justify-center perspective-scene"
  >
    {/* El carrusel se construye pieza a pieza */}
    <motion.div className="carousel-axis" ...>
        {AGENTS.map((agent, index) => (
            <motion.div
              key={agent.id}
              variants={shardVariants} // Cada tarjeta es un fragmento que vuela hacia su lugar
              className="agent-card-container"
              style={{ ...transforms }}
            >
               {/* Contenido de la tarjeta */}
            </motion.div>
        ))}
    </motion.div>
  </motion.div>
);
```

## 4. IMPACTO ESPERADO
*   **Narrativa Visual:** El usuario percibirá que la "realidad" del Core único se ha fracturado para permitir la entrada de múltiples agentes.
*   **Satisfacción Táctil:** El uso de resortes rígidos (`stiffness: 250`) dará una sensación de "golpe" o "snap" mecánico cuando las tarjetas encajen en su lugar.
*   **Diferenciación:** Elimina la sensación de "página web" en favor de una interfaz de videojuego nativa.
