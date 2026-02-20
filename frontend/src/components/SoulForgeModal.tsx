import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Cpu, User, FileText } from 'lucide-react';
import '../KizunaHUD.css';

interface SoulForgeModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export const SoulForgeModal: React.FC<SoulForgeModalProps> = ({ isOpen, onClose, onCreated }) => {
  const [name, setName] = useState('');
  const [role, setRole] = useState('');
  const [instruction, setInstruction] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      // Direct fetch to the backend API we just created
      // Assuming backend is on port 8000 (standard FastAPI) or configured proxy
      // Use relative path /api/agents assuming proxy is set up in package.json or vite.config
      // If not, we might need full URL. For now, try /api/agents.

      const response = await fetch('http://localhost:8000/api/agents/', { // Hardcoded for dev, or use env var
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name,
          role,
          base_instruction: instruction,
          traits: {}, // Default empty
          tags: []    // Default empty
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to create agent: ${response.statusText}`);
      }

      const data = await response.json();
      console.log('Agent Created:', data);

      // Reset form
      setName('');
      setRole('');
      setInstruction('');

      onCreated();
      onClose();
    } catch (err: any) {
      console.error(err);
      setError(err.message || 'Unknown error occurred');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm"
          onClick={onClose} // Close on backdrop click
        >
          <motion.div
            initial={{ scale: 0.9, y: 20, opacity: 0 }}
            animate={{ scale: 1, y: 0, opacity: 1 }}
            exit={{ scale: 0.9, y: 20, opacity: 0 }}
            transition={{ type: 'spring', stiffness: 300, damping: 25 }}
            className="relative w-full max-w-2xl mx-4"
            onClick={(e) => e.stopPropagation()} // Prevent close on modal click
          >
            {/* Modal Container with Dark Water Aesthetic */}
            <div
              className="kizuna-liquid-glass p-8 text-white relative overflow-hidden"
              style={{
                clipPath: 'polygon(5% 0, 100% 0, 100% 95%, 95% 100%, 0 100%, 0 5%)',
                border: '1px solid rgba(0, 209, 255, 0.2)'
              }}
            >
              {/* Header */}
              <div className="flex justify-between items-start mb-8 border-b border-white/10 pb-4">
                <div>
                  <h2 className="font-monumental text-3xl tracking-widest text-cyan-400">
                    SOUL FORGE <span className="text-white/30 text-lg align-top">PROTOCOL</span>
                  </h2>
                  <p className="font-technical text-xs text-cyan-200/60 mt-1">
                    DESIGN NEW INTELLIGENCE // ARCHETYPE DEFINITION
                  </p>
                </div>
                <button
                  onClick={onClose}
                  className="text-white/50 hover:text-red-500 transition-colors"
                >
                  <X size={32} />
                </button>
              </div>

              {/* Form */}
              <form onSubmit={handleSubmit} className="space-y-6">

                {/* Name Input */}
                <div className="space-y-2">
                  <label className="font-technical text-cyan-300 text-sm flex items-center gap-2">
                    <User size={14} /> DESIGNATION (NAME)
                  </label>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                    className="w-full bg-black/40 border border-white/10 p-3 text-white font-mono focus:border-cyan-400 focus:outline-none focus:ring-1 focus:ring-cyan-400/50 transition-all"
                    placeholder="e.g. KIZUNA-02"
                    style={{ clipPath: 'polygon(0 0, 100% 0, 100% 85%, 98% 100%, 0 100%)' }}
                  />
                </div>

                {/* Role Input */}
                <div className="space-y-2">
                  <label className="font-technical text-cyan-300 text-sm flex items-center gap-2">
                    <Cpu size={14} /> FUNCTIONAL ROLE
                  </label>
                  <input
                    type="text"
                    value={role}
                    onChange={(e) => setRole(e.target.value)}
                    required
                    className="w-full bg-black/40 border border-white/10 p-3 text-white font-mono focus:border-cyan-400 focus:outline-none focus:ring-1 focus:ring-cyan-400/50 transition-all"
                    placeholder="e.g. TACTICAL SUPPORT"
                    style={{ clipPath: 'polygon(0 0, 100% 0, 100% 85%, 98% 100%, 0 100%)' }}
                  />
                </div>

                {/* Base Instruction Input */}
                <div className="space-y-2">
                  <label className="font-technical text-cyan-300 text-sm flex items-center gap-2">
                    <FileText size={14} /> CORE DIRECTIVE (SYSTEM PROMPT)
                  </label>
                  <textarea
                    value={instruction}
                    onChange={(e) => setInstruction(e.target.value)}
                    required
                    rows={5}
                    className="w-full bg-black/40 border border-white/10 p-3 text-white font-mono focus:border-cyan-400 focus:outline-none focus:ring-1 focus:ring-cyan-400/50 transition-all resize-none"
                    placeholder="Define the soul's behavior, constraints, and personality..."
                    style={{ clipPath: 'polygon(0 0, 100% 0, 100% 95%, 98% 100%, 0 100%)' }}
                  />
                </div>

                {/* Error Message */}
                {error && (
                  <div className="text-red-500 font-mono text-sm bg-red-500/10 p-2 border border-red-500/30">
                    ERROR: {error}
                  </div>
                )}

                {/* Actions */}
                <div className="flex justify-end gap-4 pt-4 border-t border-white/10">
                   <button
                    type="button"
                    onClick={onClose}
                    className="font-technical text-white/50 hover:text-white px-6 py-2 transition-colors"
                  >
                    ABORT
                  </button>

                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="kizuna-shard-btn-wrapper relative group"
                  >
                     <span className="kizuna-shard-btn-inner">
                       {isSubmitting ? 'COMPILING...' : 'INITIALIZE SOUL'}
                     </span>
                  </button>
                </div>

              </form>

              {/* Decorative Elements */}
              <div className="absolute top-0 right-0 w-32 h-32 bg-cyan-500/5 blur-3xl rounded-full pointer-events-none" />
              <div className="absolute bottom-0 left-0 w-32 h-32 bg-blue-600/10 blur-3xl rounded-full pointer-events-none" />
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};
