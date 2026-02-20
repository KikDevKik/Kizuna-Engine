import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, AlertTriangle } from 'lucide-react';
import '../KizunaHUD.css';

interface DeleteAgentModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  agentName: string;
}

export const DeleteAgentModal: React.FC<DeleteAgentModalProps> = ({ isOpen, onClose, onConfirm, agentName }) => {
  const [inputValue, setInputValue] = useState('');

  // Reset input when modal opens
  useEffect(() => {
    if (isOpen) {
      setInputValue('');
    }
  }, [isOpen]);

  const isMatch = inputValue === agentName;

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* BACKDROP */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50"
          />

          {/* MODAL */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            className="fixed inset-0 flex items-center justify-center z-50 pointer-events-none"
          >
            <div className="bg-slate-900/90 border border-red-500/30 p-8 rounded-lg w-[500px] pointer-events-auto relative overflow-hidden shadow-[0_0_50px_rgba(255,0,0,0.1)]">

              {/* Decorative Header Line */}
              <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-red-500/50 to-transparent" />

              <button
                onClick={onClose}
                className="absolute top-4 right-4 text-slate-500 hover:text-white transition-colors"
              >
                <X size={24} />
              </button>

              <div className="flex flex-col gap-6 items-center text-center">
                <div className="p-4 bg-red-500/10 rounded-full border border-red-500/20">
                  <AlertTriangle className="text-red-500 w-12 h-12" />
                </div>

                <div>
                  <h2 className="font-monumental text-2xl text-red-100 tracking-wider mb-2">TERMINATE SOUL?</h2>
                  <p className="font-technical text-slate-400 text-sm">
                    This action is irreversible. The agent's memory core and identity file will be permanently erased.
                  </p>
                </div>

                <div className="w-full bg-black/40 p-4 border border-slate-700/50 rounded text-left">
                  <label className="block font-technical text-xs text-slate-500 mb-2 uppercase">
                    Type <span className="text-white font-bold">{agentName}</span> to confirm
                  </label>
                  <input
                    type="text"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    className="w-full bg-transparent border-b border-slate-600 focus:border-red-500 outline-none text-white font-mono py-2 transition-colors"
                    placeholder="ENTER AGENT NAME"
                    autoFocus
                  />
                </div>

                <div className="flex gap-4 w-full mt-2">
                  <button
                    onClick={onClose}
                    className="flex-1 py-3 px-4 border border-slate-600 text-slate-400 font-technical text-sm hover:bg-slate-800 transition-colors uppercase tracking-widest"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={onConfirm}
                    disabled={!isMatch}
                    className={`flex-1 py-3 px-4 font-technical text-sm uppercase tracking-widest transition-all duration-300 ${
                      isMatch
                        ? 'bg-red-500/20 border border-red-500 text-red-100 hover:bg-red-500 hover:text-white shadow-[0_0_20px_rgba(220,38,38,0.4)]'
                        : 'bg-slate-800/50 border border-slate-700 text-slate-600 cursor-not-allowed'
                    }`}
                  >
                    Terminate
                  </button>
                </div>
              </div>

            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};
