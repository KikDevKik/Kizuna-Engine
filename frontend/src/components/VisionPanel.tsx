import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Eye } from 'lucide-react';
import '../KizunaHUD.css';

export const VisionPanel: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="fixed top-4 right-4 z-40 flex flex-col items-end pointer-events-auto">
      <motion.button
        onClick={() => setIsOpen(!isOpen)}
        className="w-12 h-12 flex items-center justify-center bg-vintage-navy/40 border border-electric-blue/50 text-electric-blue rounded-bl-xl backdrop-blur-md"
        whileHover={{ scale: 1.1, backgroundColor: "rgba(0, 209, 255, 0.2)" }}
        whileTap={{ scale: 0.95 }}
      >
        <Eye size={20} />
      </motion.button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, x: 50, scale: 0.9 }}
            animate={{ opacity: 1, x: 0, scale: 1 }}
            exit={{ opacity: 0, x: 50, scale: 0.9 }}
            className="mt-4 w-80 h-48 bg-abyssal-black/80 border border-electric-blue/30 backdrop-blur-lg rounded-bl-3xl overflow-hidden shadow-lg shadow-vintage-navy/20"
          >
            <div className="flex items-center justify-between p-2 border-b border-electric-blue/20 bg-abyssal-black/40">
               <span className="font-technical text-xs tracking-widest text-electric-blue/80">OPTICAL SENSOR // OFFLINE</span>
               <div className="flex gap-2">
                 <div className="w-2 h-2 rounded-full bg-alert-red animate-pulse" />
               </div>
            </div>

            <div className="flex items-center justify-center h-full text-vintage-navy font-monumental text-4xl opacity-20">
               NO SIGNAL
            </div>

            {/* SCAN LINES */}
            <div className="absolute inset-0 bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.25)_50%),linear-gradient(90deg,rgba(255,0,0,0.06),rgba(0,255,0,0.02),rgba(0,0,255,0.06))] bg-[length:100%_4px,3px_100%] pointer-events-none" />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
