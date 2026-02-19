import React, { useRef, useEffect } from 'react';
import '../KizunaHUD.css';

interface KizunaCoreProps {
  volumeRef: React.MutableRefObject<number>;
  isListening: boolean;
  isAiSpeaking: boolean;
  status: string;
}

export const KizunaCore: React.FC<KizunaCoreProps> = ({ volumeRef, isListening, isAiSpeaking, status }) => {
  const coreRef = useRef<HTMLDivElement>(null);

  // LEY 4: EL NÚCLEO REACTIVO (Optimized Animation Loop)
  useEffect(() => {
    let animationFrameId: number;

    const animate = () => {
      if (coreRef.current) {
        // Calculate volume scale based on status
        // If speaking, volume drives scale. If listening, volume drives scale (maybe less).
        // If idle, scale is minimal.

        const vol = volumeRef.current; // Assuming 0.0 to 1.0+
        let scale = 1.0;

        if (isAiSpeaking) {
           // AI Speaking: heavy pulsing
           scale = 1.0 + (vol * 0.8);
        } else if (isListening) {
           // User Speaking: sharp reaction
           scale = 1.0 + (vol * 0.4);
        } else {
           // Idle: subtle breathing handled by CSS keyframes mostly, but we can add noise
           scale = 1.0 + (vol * 0.1);
        }

        // Clamp scale to reasonable limits
        scale = Math.min(Math.max(scale, 0.8), 2.5);

        // Update CSS variable directly to avoid React re-renders
        coreRef.current.style.setProperty('--vol-scale', scale.toFixed(3));
      }
      animationFrameId = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      cancelAnimationFrame(animationFrameId);
    };
  }, [volumeRef, isAiSpeaking, isListening]);

  // Determine visual state for CSS
  let visualState = 'idle';
  if (status === 'connected') {
    if (isAiSpeaking) visualState = 'speaking';
    else if (isListening) visualState = 'listening'; // User is speaking or silence
    else visualState = 'idle'; // Fallback
  } else {
    visualState = 'idle';
  }

  // Override "idle" with "listening" if connected and not speaking, as per memory logic
  // Memory says: isListening = connected && !isAiSpeaking
  // But purely visual:
  // - "idle" = slow breathing (maybe waiting for connection or silence)
  // - "listening" = sharp geometric shape (user input)
  // - "speaking" = volumetric expansion (AI output)

  // Refined Logic:
  // If AI is speaking -> "speaking"
  // If Connected & Not AI Speaking -> "listening" (Active state)
  // If Not Connected -> "idle" (Dormant)

  if (status === 'connected') {
    if (isAiSpeaking) {
      visualState = 'speaking';
    } else {
      visualState = 'listening';
    }
  } else {
    visualState = 'idle';
  }

  return (
    <div className="kizuna-core-container">
      {/* Outer Rings (Decorative) */}
      <div className="absolute inset-0 border border-cyan-500/20 rounded-full scale-150 animate-pulse" />
      <div className="absolute inset-0 border border-cyan-500/10 rounded-full scale-125" />

      {/* The Core */}
      <div
        ref={coreRef}
        className="ai-core-indicator"
        data-state={visualState}
      >
        {/* Inner Glint */}
        <div className="absolute top-1/4 left-1/4 w-2 h-2 bg-white/50 rounded-full blur-[1px]" />
      </div>

      {/* Label under core */}
      <div className="absolute -bottom-16 text-center">
        <div className="font-technical text-xs tracking-widest opacity-60">
           STATUS: {status.toUpperCase()}
        </div>
        <div className="font-monumental text-xl tracking-tighter text-cyan-400">
           {visualState.toUpperCase()}
        </div>
      </div>
    </div>
  );
};
