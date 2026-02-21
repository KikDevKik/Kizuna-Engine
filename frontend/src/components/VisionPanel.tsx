import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Eye, Activity } from 'lucide-react';
import { useVision } from '../hooks/useVision';
import '../KizunaHUD.css';

interface VisionPanelProps {
  connected: boolean;
  sendImage: (base64: string) => void;
}

export const VisionPanel: React.FC<VisionPanelProps> = ({ connected, sendImage }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [pulse, setPulse] = useState(false);

  // Activate camera when connected (Argus Philosophy: Always Seeing)
  const { videoRef, captureFrame, isCameraReady } = useVision(connected);

  // Visual Heartbeat Loop
  useEffect(() => {
    if (!connected || !isCameraReady) return;

    // Argus: Muestreo Inteligente (2s heartbeat)
    const interval = setInterval(async () => {
      const frame = await captureFrame();
      if (frame) {
        sendImage(frame);
        // Visual Feedback (Pulse)
        setPulse(true);
        setTimeout(() => setPulse(false), 200);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [connected, isCameraReady, captureFrame, sendImage]);

  return (
    <div className="fixed top-24 right-4 z-40 flex flex-col items-end pointer-events-auto">
      {/* Toggle Button with Status Indication */}
      <motion.button
        onClick={() => setIsOpen(!isOpen)}
        className={`w-12 h-12 flex items-center justify-center border rounded-bl-xl backdrop-blur-md transition-colors duration-300 ${
          pulse
            ? 'bg-electric-blue/30 border-electric-blue text-white'
            : 'bg-vintage-navy/40 border-electric-blue/50 text-electric-blue'
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
            className="mt-4 w-80 h-48 bg-abyssal-black/80 border border-electric-blue/30 backdrop-blur-lg rounded-bl-3xl overflow-hidden shadow-lg shadow-vintage-navy/20 flex flex-col"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-2 border-b border-electric-blue/20 bg-abyssal-black/40">
               <span className="font-technical text-xs tracking-widest text-electric-blue/80">
                   OPTICAL SENSOR // {connected ? 'ONLINE' : 'OFFLINE'}
               </span>
               <div className="flex gap-2">
                 <div className={`w-2 h-2 rounded-full transition-all duration-300 ${
                     pulse ? 'bg-electric-blue scale-150 shadow-[0_0_10px_#00d1ff]' : (connected ? 'bg-emerald-500' : 'bg-alert-red')
                 }`} />
               </div>
            </div>

            {/* Viewport */}
            <div className="relative flex-1 bg-black overflow-hidden flex items-center justify-center">
               <video
                  ref={videoRef}
                  className={`w-full h-full object-cover opacity-90 ${!connected ? 'hidden' : ''}`}
                  autoPlay
                  playsInline
                  muted
               />

               {!connected && (
                   <div className="absolute inset-0 flex items-center justify-center text-vintage-navy font-monumental text-4xl opacity-20">
                       NO SIGNAL
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
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
