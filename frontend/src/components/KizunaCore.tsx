import React, { useRef, useEffect } from 'react';
import '../KizunaHUD.css';

interface KizunaCoreProps {
  volumeRef: React.MutableRefObject<number>;
  isListening: boolean;
  isAiSpeaking: boolean;
  status: string;
}

export const KizunaCore: React.FC<KizunaCoreProps> = ({ volumeRef, isListening: _ignoredIsListening, isAiSpeaking, status }) => {
  const coreRef = useRef<HTMLDivElement>(null);
  const [isUserSpeaking, setIsUserSpeaking] = React.useState(false);

  // VAD Simulation (Volume Threshold)
  useEffect(() => {
    let animationFrameId: number;
    // Debounce state changes slightly to prevent flickering
    let silenceCounter = 0;
    const SILENCE_THRESHOLD = 10; // Frames

    const checkVolume = () => {
      const vol = volumeRef.current;
      // Threshold 0.02 chosen empirically for background noise filtering
      if (vol > 0.02) {
        setIsUserSpeaking(true);
        silenceCounter = 0;
      } else {
        silenceCounter++;
        if (silenceCounter > SILENCE_THRESHOLD) {
          setIsUserSpeaking(false);
        }
      }
      animationFrameId = requestAnimationFrame(checkVolume);
    };
    checkVolume();
    return () => cancelAnimationFrame(animationFrameId);
  }, [volumeRef]);

  // LEY 4: EL NÚCLEO REACTIVO (Optimized Animation Loop)
  useEffect(() => {
    let animationFrameId: number;

    const animate = () => {
      if (coreRef.current) {
        const vol = volumeRef.current;
        let scale = 1.0;

        if (isAiSpeaking) {
           // AI Speaking: heavy pulsing
           scale = 1.0 + (vol * 0.8);
        } else if (isUserSpeaking) {
           // User Speaking: sharp reaction
           scale = 1.0 + (vol * 0.4);
        } else {
           // Idle: subtle breathing
           scale = 1.0 + (vol * 0.1);
        }

        scale = Math.min(Math.max(scale, 0.8), 2.5);
        coreRef.current.style.setProperty('--vol-scale', scale.toFixed(3));
      }
      animationFrameId = requestAnimationFrame(animate);
    };

    animate();

    return () => cancelAnimationFrame(animationFrameId);
  }, [volumeRef, isAiSpeaking, isUserSpeaking]);

  // Determine visual state for CSS
  let visualState = 'idle';
  if (status === 'connected') {
    if (isAiSpeaking) {
      visualState = 'speaking'; // Volumetric Expansion
    } else if (isUserSpeaking) {
      visualState = 'listening'; // Crystalline Aggression (Only when VAD active)
    } else {
      visualState = 'idle'; // Liquid Breathing (Silence)
    }
  } else {
    visualState = 'idle';
  }

  return (
    <div className="kizuna-core-container">
      {/* Outer Rings (Decorative) */}
      <div className="absolute inset-0 border border-electric-blue/20 rounded-full scale-150 animate-pulse" />
      <div className="absolute inset-0 border border-electric-blue/10 rounded-full scale-125" />

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
        <div className="font-monumental text-xl tracking-tighter text-electric-blue">
           {visualState.toUpperCase()}
        </div>
      </div>
    </div>
  );
};
