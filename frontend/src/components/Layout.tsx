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
      {/* GLOBAL ATMOSPHERIC OVERLAY (Vignette & Scanlines) */}
      <div className="global-overlay-vignette" />
      <div className="global-overlay-scanlines" />

      {/* ESTRATO -10: FONDO ABISAL */}
      <motion.div
        className="layer-abyssal-background"
        style={{ x: backgroundX, y: backgroundY }}
      >
        <div className="water-caustics-shader" />
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
