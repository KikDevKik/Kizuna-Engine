import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Send, Terminal } from 'lucide-react';
import { useRitual } from '../contexts/RitualContext';
import '../KizunaHUD.css';

// ------------------------------------------------------------------
// TYPEWRITER COMPONENT (Shizuku Effect)
// ------------------------------------------------------------------
const TypewriterText: React.FC<{
  text: string;
  isActive: boolean;
  onComplete?: () => void;
}> = ({ text, isActive, onComplete }) => {
  const [displayed, setDisplayed] = useState('');
  const [isComplete, setIsComplete] = useState(false);

  // If not active (e.g. old history), show full text immediately
  useEffect(() => {
    if (!isActive) {
      setDisplayed(text);
      setIsComplete(true);
    }
  }, [isActive, text]);

  useEffect(() => {
    if (!isActive || isComplete) return;

    // Reset if text changes
    setDisplayed('');
    setIsComplete(false);

    let index = 0;
    const intervalId = setInterval(() => {
      if (index < text.length) {
        setDisplayed(text.slice(0, index + 1));
        index++;
      } else {
        clearInterval(intervalId);
        setIsComplete(true);
        if (onComplete) onComplete();
      }
    }, 50); // Slow cadence (50ms)

    return () => clearInterval(intervalId);
  }, [text, isActive]); // Depend on text to restart if it changes

  const finishImmediately = () => {
    if (!isComplete && isActive) {
      setDisplayed(text);
      setIsComplete(true);
      if (onComplete) onComplete();
    }
  };

  return (
    <div onClick={finishImmediately} className="cursor-pointer">
      {displayed}
      {isActive && !isComplete && <span className="animate-pulse">_</span>}
    </div>
  );
};

// ------------------------------------------------------------------
// MAIN MODAL
// ------------------------------------------------------------------
interface SoulForgeModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export const SoulForgeModal: React.FC<SoulForgeModalProps> = ({ isOpen, onClose, onCreated }) => {
  const { messages, status, isLoading, error, sendMessage, startRitual, resetRitual } = useRitual();
  const [inputValue, setInputValue] = useState('');
  const [animationPhase, setAnimationPhase] = useState<'normal' | 'resonance' | 'dissipation'>('normal');
  const scrollRef = useRef<HTMLDivElement>(null);

  // 1. Initial Fetch & State Reset on Open
  useEffect(() => {
    if (isOpen) {
      startRitual();
      setAnimationPhase('normal');
    }
  }, [isOpen, startRitual]);

  // 2. Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, inputValue]);

  // 3. Completion Sequence (Catarsis Procedural)
  useEffect(() => {
    if (status === 'complete') {
      // 0s: Lock (Implicit via status check in input)

      // 1.5s: Resonance
      setAnimationPhase('resonance');

      const timer1 = setTimeout(() => {
        // 3. Dissipation
        setAnimationPhase('dissipation');

        const timer2 = setTimeout(() => {
           // 4. Close & Reset
           onCreated(); // Fetch new roster
           onClose();   // Close modal

           // We reset AFTER closing to ensure next time is fresh.
           // Requirement: "return to reality without losing progress" applies to *interruption*.
           // But completion is *final*. So we reset.
           setTimeout(() => resetRitual(), 500);

        }, 1000); // 1s Dissipation duration
        return () => clearTimeout(timer2);
      }, 1500); // 1.5s Resonance duration

      return () => clearTimeout(timer1);
    }
  }, [status, onClose, onCreated, resetRitual]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading || status === 'complete') return;

    const content = inputValue;
    setInputValue(''); // Clear immediately
    await sendMessage(content);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') onClose();
  };

  // ------------------------------------------------------------------
  // RENDER HELPERS
  // ------------------------------------------------------------------

  // Resonance Effect Style
  const getContainerStyle = () => {
    if (animationPhase === 'dissipation') {
      return { opacity: 0, scale: 0.95, filter: 'blur(10px)' };
    }
    return { opacity: 1, scale: 1, filter: 'blur(0px)' };
  };

  const getLastMessageStyle = (isLast: boolean) => {
    if (isLast && animationPhase === 'resonance') {
       return "text-cyan-300 drop-shadow-[0_0_10px_rgba(0,255,255,0.8)] animate-pulse";
    }
    return "";
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[100] flex items-center justify-center bg-black/90 backdrop-blur-md"
          onClick={onClose}
          onKeyDown={handleKeyDown}
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={getContainerStyle()}
            transition={{ duration: 0.8, ease: "easeInOut" }}
            className="relative w-full max-w-3xl mx-4 h-[600px] flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            {/* TERMINAL CONTAINER */}
            <div
              className="kizuna-liquid-glass w-full h-full flex flex-col p-8 text-white relative overflow-hidden border border-cyan-900/30"
              style={{
                clipPath: 'polygon(2% 0, 100% 0, 100% 98%, 98% 100%, 0 100%, 0 2%)',
              }}
            >
              {/* HEADER */}
              <div className="flex justify-between items-center mb-6 border-b border-white/10 pb-4 shrink-0">
                <div>
                  <h2 className="font-monumental text-2xl tracking-widest text-cyan-400 flex items-center gap-3">
                    <Terminal size={24} />
                    SOUL FORGE <span className="text-white/20 text-sm align-top">TERMINAL_LINK</span>
                  </h2>
                </div>
                <button
                  onClick={onClose}
                  className="text-white/30 hover:text-red-500 transition-colors"
                >
                  <X size={24} />
                </button>
              </div>

              {/* CONVERSATION HISTORY (Scrollable) */}
              <div
                className="flex-1 overflow-y-auto space-y-6 pr-4 custom-scrollbar mb-6"
                ref={scrollRef}
              >
                {/* Empty State / Loader */}
                {messages.length === 0 && isLoading && (
                   <div className="text-cyan-500/50 font-mono animate-pulse">CONNECTING TO THE VOID...</div>
                )}

                {messages.map((msg, idx) => {
                  const isLast = idx === messages.length - 1;
                  const isSystem = msg.role === 'system';

                  return (
                    <div
                      key={idx}
                      className={`flex flex-col ${isSystem ? 'items-start' : 'items-end'}`}
                    >
                      <span className="text-[10px] text-white/20 font-technical mb-1 uppercase">
                        {msg.role === 'system' ? 'THE VOID' : 'YOU'}
                      </span>

                      <div
                        className={`max-w-[80%] font-mono text-sm leading-relaxed p-3 border border-white/5
                          ${isSystem
                            ? `text-cyan-100/90 bg-black/40 ${getLastMessageStyle(isLast && isSystem)}`
                            : 'text-white/80 bg-white/5'
                          }
                        `}
                        style={{
                           clipPath: isSystem
                             ? 'polygon(0 0, 100% 0, 100% 90%, 95% 100%, 0 100%)'
                             : 'polygon(0 0, 100% 0, 100% 100%, 5% 100%, 0 90%)'
                        }}
                      >
                         {isSystem ? (
                           <TypewriterText
                             text={msg.content}
                             isActive={isLast} // Only type the last message
                           />
                         ) : (
                           msg.content
                         )}
                      </div>
                    </div>
                  );
                })}

                {/* Loading Indicator for Reply */}
                {isLoading && messages.length > 0 && messages[messages.length - 1].role === 'user' && (
                   <div className="text-cyan-500/30 text-xs font-technical animate-pulse mt-2">
                     ANALYZING RESONANCE...
                   </div>
                )}

                {/* Error Display */}
                {error && (
                   <div className="text-red-500/80 font-mono text-sm border border-red-900/50 p-2 bg-red-900/10">
                     ERROR: {error}
                   </div>
                )}

                {/* Completion Message Placeholder (Visually handled by Resonance) */}
                {status === 'complete' && animationPhase !== 'dissipation' && (
                   <div className="text-center mt-8">
                      <h3 className="font-monumental text-xl text-cyan-400 animate-pulse tracking-[0.5em]">INVOCATION COMPLETE</h3>
                   </div>
                )}
              </div>

              {/* INPUT AREA */}
              <form onSubmit={handleSubmit} className="shrink-0 relative">
                <input
                  type="text"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  disabled={isLoading || status === 'complete'}
                  placeholder={status === 'complete' ? "SOUL CRYSTALLIZED" : "Enter your response..."}
                  className="w-full bg-black/60 border border-white/20 p-4 pr-12 text-white font-mono focus:border-cyan-400 focus:outline-none focus:ring-1 focus:ring-cyan-400/50 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  style={{ clipPath: 'polygon(0 0, 100% 0, 100% 80%, 98% 100%, 0 100%)' }}
                  autoFocus
                />
                <button
                  type="submit"
                  disabled={!inputValue.trim() || isLoading || status === 'complete'}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-cyan-400 hover:text-white disabled:opacity-30 transition-colors"
                >
                  <Send size={20} />
                </button>
              </form>

              {/* DECORATIVE BG */}
              <div className="absolute top-0 right-0 w-64 h-64 bg-cyan-500/5 blur-[80px] rounded-full pointer-events-none" />
              <div className="absolute bottom-0 left-0 w-48 h-48 bg-purple-600/5 blur-[60px] rounded-full pointer-events-none" />
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};
