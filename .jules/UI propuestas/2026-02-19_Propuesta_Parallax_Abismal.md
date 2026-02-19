# PROPUESTA DE MEJORA VISUAL: ABYSSAL PARALLAX MULTIDIMENSIONAL

**Fecha:** 2026-02-19
**Componente Afectado:** `frontend/src/components/Layout.tsx`
**Nivel de Prioridad:** Alta

## 1. ESTADO ACTUAL (EL PROBLEMA)
El componente `Layout.tsx` actual implementa un sistema de paralaje básico con solo dos capas: `layer-abyssal-background` (Z-Index -10) y `layer-interactive-foreground` (Z-Index 10). Aunque utiliza `framer-motion` y `useSpring`, la implementación carece de la capa intermedia crítica ("HUD Estático / Midground") descrita en la arquitectura del motor. Además, la física del resorte (`damping: 50`) es demasiado "ligera" y no transmite la resistencia densa del agua ("Dark Water") que requiere una masa mayor para simular la inmersión profunda.

## 2. JUSTIFICACIÓN ESTÉTICA (EL PORQUÉ)
Según la sección **3.1. Estratificación del Viewport (Z-Index Architecture)** del "Documento de Diseño UI Abisal", el espacio virtual debe dividirse estrictamente en tres estratos de profundidad para romper la limitación plana del navegador:
1.  **Fondo Abisal (-10):** Movimiento sutil en dirección al cursor (lejanía infinita).
2.  **HUD Estático / Midground (10):** Plano intermedio para retículas y métricas, con movimiento mínimo opuesto.
3.  **Primer Plano / Core (50):** Movimiento pronunciado opuesto al cursor (proximidad).

La ausencia del estrato intermedio aplana la experiencia, eliminando la ilusión de "volumen" necesaria para que el usuario sienta que está *dentro* del motor, y no solo mirándolo.

## 3. SOLUCIÓN TÉCNICA (EL CÓDIGO)
Se propone reestructurar `Layout.tsx` para incluir el tercer estrato y ajustar las físicas del resorte para mayor "peso" hidrodinámico.

```typescript
// frontend/src/components/Layout.tsx
import React, { type ReactNode, useEffect } from 'react';
import { motion, useSpring, useMotionValue, useTransform } from 'framer-motion';
import '../KizunaHUD.css';

interface LayoutProps {
  children: ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const rawMouseX = useMotionValue(typeof window !== "undefined" ? window.innerWidth / 2 : 0);
  const rawMouseY = useMotionValue(typeof window !== "undefined" ? window.innerHeight / 2 : 0);

  // FÍSICA DARK WATER: Mayor masa y damping para resistencia de fluido denso [3.2]
  const springPhysics = { damping: 40, stiffness: 60, mass: 1.5 };
  const smoothMouseX = useSpring(rawMouseX, springPhysics);
  const smoothMouseY = useSpring(rawMouseY, springPhysics);

  // INTERPOLACIÓN DE VECTORES (Parallax 3-Capas)
  // Capa Fondo (-10): Se mueve CON el cursor (lejanía)
  const backgroundX = useTransform(smoothMouseX, [0, window.innerWidth], [-15, 15]);
  const backgroundY = useTransform(smoothMouseY, [0, window.innerHeight], [-15, 15]);

  // Capa Midground (10): HUD Táctico, movimiento sutil opuesto
  const midgroundX = useTransform(smoothMouseX, [0, window.innerWidth], [10, -10]);
  const midgroundY = useTransform(smoothMouseY, [0, window.innerHeight], [10, -10]);

  // Capa Primer Plano (50): Core Interactivo, movimiento rápido opuesto
  const foregroundX = useTransform(smoothMouseX, [0, window.innerWidth], [30, -30]);
  const foregroundY = useTransform(smoothMouseY, [0, window.innerHeight], [30, -30]);

  useEffect(() => {
    const handleMouseMove = (event: MouseEvent) => {
      rawMouseX.set(event.clientX);
      rawMouseY.set(event.clientY);
    };
    window.addEventListener("mousemove", handleMouseMove, { passive: true });
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, [rawMouseX, rawMouseY]);

  return (
    <div className="kizuna-engine-viewport">
      {/* ESTRATO -10: FONDO ABISAL */}
      <motion.div
        className="layer-abyssal-background"
        style={{ x: backgroundX, y: backgroundY }}
      >
        <div className="water-caustics-shader" />
      </motion.div>

      {/* ESTRATO 10: HUD TÁCTICO (NUEVO) */}
      <motion.div
        className="layer-tactical-hud"
        style={{
            x: midgroundX,
            y: midgroundY,
            position: 'absolute',
            inset: 0,
            zIndex: 10,
            pointerEvents: 'none'
        }}
      >
        {/* Elementos decorativos flotantes independientes del Core */}
        <svg className="absolute top-10 right-10 w-24 h-24 opacity-40 animate-spin-slow">
            <circle cx="50" cy="50" r="40" stroke="#00D1FF" strokeWidth="1" fill="none" strokeDasharray="5,5" />
        </svg>
        <div className="absolute bottom-20 left-10 font-technical text-xs text-cyan-700">
            COORD: {smoothMouseX.get().toFixed(0)} : {smoothMouseY.get().toFixed(0)}
        </div>
      </motion.div>

      {/* ESTRATO 50: CORE INTERACTIVO */}
      <motion.div
        className="layer-interactive-foreground"
        style={{
            x: foregroundX,
            y: foregroundY,
            position: 'relative',
            width: '100%',
            height: '100%',
            zIndex: 50
        }}
      >
        {children}
      </motion.div>
    </div>
  );
};
```

## 4. IMPACTO ESPERADO
*   **Profundidad Volumétrica:** La separación visual entre el HUD estático y el Core interactivo generará la sensación de espacio físico 3D.
*   **Sensación de Peso:** El ajuste de `mass: 1.5` en el resorte hará que la interfaz se sienta "sumergida", eliminando la sensación de ligereza web estándar.
*   **Fidelidad Estética:** Cumplimiento directo de la directiva de diseño de Atlus sobre menús flotantes en un "Mar de Almas".
