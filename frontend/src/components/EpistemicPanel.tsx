import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { BrainCircuit, X } from 'lucide-react';
import '../KizunaHUD.css';

interface EpistemicPanelProps {
  logs?: string[];
}

export const EpistemicPanel: React.FC<EpistemicPanelProps> = ({ logs = [] }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="fixed bottom-4 right-4 z-40 flex flex-col items-end pointer-events-auto">
      <motion.button
        onClick={() => setIsOpen(!isOpen)}
        className="w-12 h-12 flex items-center justify-center bg-vintage-navy/40 border border-electric-blue/50 text-electric-blue rounded-tl-xl backdrop-blur-md"
        whileHover={{ scale: 1.1, backgroundColor: "rgba(0, 209, 255, 0.2)" }}
        whileTap={{ scale: 0.95 }}
      >
        <BrainCircuit size={20} />
      </motion.button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 50, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 50, scale: 0.9 }}
            className="mb-4 w-96 max-h-96 flex flex-col bg-abyssal-black/80 border border-electric-blue/30 backdrop-blur-lg rounded-tl-3xl overflow-hidden shadow-lg shadow-vintage-navy/20"
          >
            <div className="flex items-center justify-between p-3 border-b border-electric-blue/20 bg-abyssal-black/40">
               <span className="font-technical text-xs tracking-widest text-electric-blue/80">
                 EPISTEMIC MEMORY // SYNCED
               </span>
               <button onClick={() => setIsOpen(false)} className="text-electric-blue/80 hover:text-electric-blue transition-colors">
                  <X size={14} />
               </button>
            </div>

            <div className="flex-1 overflow-y-auto p-4 font-mono text-xs text-electric-blue/80 space-y-2 scrollbar-thin scrollbar-thumb-vintage-navy scrollbar-track-transparent">
               {logs.length === 0 ? (
                 <div className="text-center opacity-40 py-8 italic font-narrative">
                    No active memory vectors...
                 </div>
               ) : (
                 logs.map((log, i) => (
                   <div key={i} className="border-l-2 border-vintage-navy pl-2 opacity-80 hover:opacity-100 transition-opacity">
                      <span className="text-electric-blue/60 mr-2">[{new Date().toLocaleTimeString()}]</span>
                      {log}
                   </div>
                 ))
               )}
            </div>

            {/* SCAN LINES */}
            <div className="absolute inset-0 bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.25)_50%),linear-gradient(90deg,rgba(255,0,0,0.06),rgba(0,255,0,0.02),rgba(0,0,255,0.06))] bg-[length:100%_4px,3px_100%] pointer-events-none" />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
