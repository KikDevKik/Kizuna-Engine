import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Eye, Activity, Camera, Monitor, EyeOff } from 'lucide-react';
import { useVision, type VisionMode } from '../hooks/useVision';
import '../KizunaHUD.css';

interface VisionPanelProps {
  connected: boolean;
  sendImage: (base64: string) => void;
  addSystemAudio: (track: MediaStreamTrack) => void;
  removeSystemAudio: () => void;
}

// Optimization: Prevent re-renders when parent re-renders (e.g. audio loop) but props are stable.
export const VisionPanel = React.memo<VisionPanelProps>(({ connected, sendImage, addSystemAudio, removeSystemAudio }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [visionMode, setVisionMode] = useState<VisionMode>('off');
  const [pulse, setPulse] = useState(false);

  // Vision Hook with Reset Callback (Argus Phase 6)
  const { videoRef, captureFrame, isReady, audioTrack } = useVision(visionMode, () => setVisionMode('off'));

  // Effect: Connect System Audio when available
  useEffect(() => {
    if (audioTrack && connected) {
        addSystemAudio(audioTrack);
    } else {
        removeSystemAudio();
    }

    return () => {
        removeSystemAudio();
    };
  }, [audioTrack, connected, addSystemAudio, removeSystemAudio]);

  // Force vision off if disconnected
  useEffect(() => {
    if (!connected) {
        setVisionMode('off');
    }
  }, [connected]);

  // Visual Heartbeat Loop
  useEffect(() => {
    if (!connected || !isReady || visionMode === 'off') return;

    // Argus: Muestreo Inteligente (2.5s heartbeat)
    const interval = setInterval(async () => {
      const frame = await captureFrame();
      if (frame) {
        sendImage(frame);
        // Visual Feedback (Pulse)
        setPulse(true);
        setTimeout(() => setPulse(false), 200);
      }
    }, 2500);

    return () => clearInterval(interval);
  }, [connected, isReady, visionMode, captureFrame, sendImage]);

  return (
    <div className="fixed top-24 right-4 z-40 flex flex-col items-end pointer-events-auto">
      {/* Toggle Button with Status Indication */}
      <motion.button
        onClick={() => setIsOpen(!isOpen)}
        className={`w-12 h-12 flex items-center justify-center border rounded-bl-xl backdrop-blur-md transition-colors duration-300 ${
          pulse
            ? 'bg-electric-blue/30 border-electric-blue text-white'
            : (visionMode !== 'off' ? 'bg-vintage-navy/60 border-electric-blue text-electric-blue' : 'bg-vintage-navy/40 border-electric-blue/50 text-electric-blue/50')
        }`}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.95 }}
      >
        {pulse ? <Activity size={20} /> : <Eye size={20} />}
      </motion.button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, x: 50, scale: 0.9 }}
            animate={{ opacity: 1, x: 0, scale: 1 }}
            exit={{ opacity: 0, x: 50, scale: 0.9 }}
            className="mt-4 w-80 h-64 bg-abyssal-black/90 border border-electric-blue/30 backdrop-blur-lg rounded-bl-3xl overflow-hidden shadow-lg shadow-vintage-navy/20 flex flex-col"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-2 border-b border-electric-blue/20 bg-abyssal-black/40">
               <span className="font-technical text-xs tracking-widest text-electric-blue/80">
                   OPTICAL SENSOR // {visionMode === 'off' ? 'STANDBY' : visionMode.toUpperCase()}
               </span>
               <div className="flex gap-2">
                 <div className={`w-2 h-2 rounded-full transition-all duration-300 ${
                     pulse ? 'bg-electric-blue scale-150 shadow-[0_0_10px_#00d1ff]' : (visionMode !== 'off' && isReady ? 'bg-emerald-500' : 'bg-alert-red')
                 }`} />
               </div>
            </div>

            {/* Viewport */}
            <div className="relative flex-1 bg-black overflow-hidden flex items-center justify-center">
               <video
                  ref={videoRef}
                  className={`w-full h-full object-cover opacity-90 ${visionMode === 'off' ? 'hidden' : ''}`}
                  autoPlay
                  playsInline
                  muted
               />

               {(visionMode === 'off' || !connected) && (
                   <div className="absolute inset-0 flex items-center justify-center text-vintage-navy font-monumental text-2xl opacity-20 tracking-wider">
                       {!connected ? 'NO LINK' : 'SENSOR OFF'}
                   </div>
               )}

               {/* Loading State */}
               {visionMode !== 'off' && !isReady && connected && (
                   <div className="absolute inset-0 flex items-center justify-center">
                       <div className="w-8 h-8 border-2 border-electric-blue/30 border-t-electric-blue rounded-full animate-spin" />
                   </div>
               )}

               {/* Scan Lines Overlay */}
               <div className="absolute inset-0 bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.25)_50%),linear-gradient(90deg,rgba(255,0,0,0.06),rgba(0,255,0,0.02),rgba(0,0,255,0.06))] bg-[length:100%_4px,3px_100%] pointer-events-none" />

               {/* Flash Feedback */}
               <AnimatePresence>
                   {pulse && (
                       <motion.div
                           initial={{ opacity: 0 }}
                           animate={{ opacity: 0.2 }}
                           exit={{ opacity: 0 }}
                           className="absolute inset-0 bg-electric-blue mix-blend-hard-light pointer-events-none"
                       />
                   )}
               </AnimatePresence>
            </div>

            {/* Control Footer */}
            <div className="flex justify-around items-center p-3 bg-abyssal-black/60 border-t border-electric-blue/20 backdrop-blur-md">
                <VisionButton
                    active={visionMode === 'camera'}
                    onClick={() => setVisionMode('camera')}
                    icon={<Camera size={18} />}
                    label="CAMERA"
                    disabled={!connected}
                />
                <VisionButton
                    active={visionMode === 'screen'}
                    onClick={() => setVisionMode('screen')}
                    icon={<Monitor size={18} />}
                    label="SCREEN"
                    disabled={!connected}
                />
                <VisionButton
                    active={visionMode === 'off'}
                    onClick={() => setVisionMode('off')}
                    icon={<EyeOff size={18} />}
                    label="DISABLE"
                    disabled={!connected && visionMode === 'off'}
                    isDestructive
                />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
});

// Helper Component for Buttons
const VisionButton = ({ active, onClick, icon, label, disabled, isDestructive = false }: any) => (
    <motion.button
        onClick={onClick}
        disabled={disabled}
        whileHover={!disabled ? { scale: 1.05 } : {}}
        whileTap={!disabled ? { scale: 0.95 } : {}}
        className={`flex flex-col items-center justify-center gap-1 w-20 py-2 rounded-lg border transition-all duration-300 ${
            disabled
                ? 'opacity-30 border-transparent text-gray-500 cursor-not-allowed'
                : active
                    ? 'bg-electric-blue/20 border-electric-blue text-electric-blue shadow-[0_0_10px_rgba(0,209,255,0.2)]'
                    : 'bg-transparent border-electric-blue/10 text-gray-400 hover:border-electric-blue/40 hover:text-electric-blue/80'
        } ${isDestructive && active ? 'bg-red-900/20 border-red-500/50 text-red-400' : ''}`}
    >
        {icon}
        <span className="text-[9px] font-technical tracking-widest">{label}</span>
    </motion.button>
);
