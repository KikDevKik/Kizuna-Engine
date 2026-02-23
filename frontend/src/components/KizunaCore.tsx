import React, { useRef, useEffect } from 'react';
import '../KizunaHUD.css';

interface KizunaCoreProps {
  volumeRef: React.MutableRefObject<number>;
  isListening: boolean;
  isAiSpeaking: boolean;
  status: string;
}

export const KizunaCore: React.FC<KizunaCoreProps> = ({ volumeRef, isAiSpeaking, status }) => {
  const coreRef = useRef<HTMLDivElement>(null);
  const userSpeakingRef = useRef(false);

  // --- Optimization: Track props via refs to avoid restarting animation loop ---
  const isAiSpeakingRef = useRef(isAiSpeaking);
  const statusRef = useRef(status);

  useEffect(() => {
    isAiSpeakingRef.current = isAiSpeaking;
  }, [isAiSpeaking]);

  useEffect(() => {
    statusRef.current = status;
  }, [status]);
  // -----------------------------------------------------------------------------

  // Optimized Animation Loop (VAD + Visuals)
  useEffect(() => {
    let animationFrameId: number;
    let silenceCounter = 0;
    const SILENCE_THRESHOLD = 10; // Frames

    const animate = () => {
      if (coreRef.current) {
        const vol = volumeRef.current;
        // Use refs for current values inside the loop
        const currentIsAiSpeaking = isAiSpeakingRef.current;
        const currentStatus = statusRef.current;

        // 1. VAD Logic (Update internal state without re-render)
        let isUserSpeaking = userSpeakingRef.current;
        if (vol > 0.02) {
          if (!isUserSpeaking) {
             userSpeakingRef.current = true;
             isUserSpeaking = true;
          }
          silenceCounter = 0;
        } else {
          silenceCounter++;
          if (silenceCounter > SILENCE_THRESHOLD) {
             if (isUserSpeaking) {
                userSpeakingRef.current = false;
                isUserSpeaking = false;
             }
          }
        }

        // 2. Determine Visual State
        let visualState = 'idle';
        if (currentStatus === 'connected') {
          if (currentIsAiSpeaking) {
            visualState = 'speaking'; // Volumetric Expansion
          } else if (isUserSpeaking) {
            visualState = 'listening'; // Crystalline Aggression
          } else {
            visualState = 'idle'; // Liquid Breathing
          }
        } else {
          visualState = 'idle';
        }

        // Direct DOM Update to avoid React render cycle
        if (coreRef.current.dataset.state !== visualState) {
          coreRef.current.dataset.state = visualState;
        }

        // 3. Animation / Scale Logic
        let scale = 1.0;
        if (currentIsAiSpeaking) {
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
  }, [volumeRef]); // Loop is now stable and doesn't restart on prop changes

  return (
    <div className="kizuna-core-container">
      {/* The Core - Initial state set via props/default, updated via RAF */}
      <div
        ref={coreRef}
        className="ai-core-indicator"
      >
        {/* Inner Glint */}
        <div className="absolute top-1/4 left-1/4 w-2 h-2 bg-white/50 rounded-full blur-[1px]" />
      </div>
    </div>
  );
};
