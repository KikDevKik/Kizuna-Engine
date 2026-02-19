import React, { type ReactNode, useEffect } from 'react';
import { motion, useSpring, useMotionValue, useTransform } from 'framer-motion';
import '../KizunaHUD.css';

interface LayoutProps {
  children: ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  // Motion Values for cursor tracking
  const rawMouseX = useMotionValue(typeof window !== "undefined" ? window.innerWidth / 2 : 0);
  const rawMouseY = useMotionValue(typeof window !== "undefined" ? window.innerHeight / 2 : 0);

  // Spring Physics for "Dark Water" resistance
  const springConfig = { damping: 50, stiffness: 40, mass: 1.2 };
  const smoothMouseX = useSpring(rawMouseX, springConfig);
  const smoothMouseY = useSpring(rawMouseY, springConfig);

  // Parallax Transforms
  // Background moves slightly with cursor (distance)
  const bgX = useTransform(smoothMouseX, [0, window.innerWidth], [15, -15]);
  const bgY = useTransform(smoothMouseY, [0, window.innerHeight], [15, -15]);

  // Foreground moves opposite to cursor (proximity)
  const fgX = useTransform(smoothMouseX, [0, window.innerWidth], [-20, 20]);
  const fgY = useTransform(smoothMouseY, [0, window.innerHeight], [-20, 20]);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      rawMouseX.set(e.clientX);
      rawMouseY.set(e.clientY);
    };

    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, [rawMouseX, rawMouseY]);

  return (
    <div className="kizuna-engine-viewport">
      {/* LAYER -10: ABYSSAL BACKGROUND */}
      <motion.div
        className="layer-abyssal-background"
        style={{ x: bgX, y: bgY }}
      >
        <div className="water-caustics-shader" />
      </motion.div>

      {/* LAYER 0: CONTENT CONTAINER */}
      <motion.div
        className="layer-interactive-foreground"
        style={{ x: fgX, y: fgY, width: '100%', height: '100%', position: 'relative', zIndex: 10 }}
      >
        {children}
      </motion.div>

      {/* DECORATIVE HUD ELEMENTS (Static or minimal movement) */}
      <div style={{ position: 'absolute', top: '20px', left: '20px', pointerEvents: 'none', zIndex: 20 }}>
        <div className="font-technical" style={{ fontSize: '0.8rem', opacity: 0.7 }}>
          SYS.V4.0 // ABYSSAL_DIVE
        </div>
      </div>
    </div>
  );
};
