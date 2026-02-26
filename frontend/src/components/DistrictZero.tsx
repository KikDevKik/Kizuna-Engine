import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Radio, Activity, X, Network } from 'lucide-react';
import '../KizunaHUD.css';

// ------------------------------------------------------------------
// DATA: ENIGMA SHELLS
// ------------------------------------------------------------------
interface EnigmaIdentity {
  id: string;
  description: string;
  tempAlias: string;
  visualHint: string; // e.g., "Neon Glitch", "Static Noise"
}

const ENIGMA_DATA: EnigmaIdentity[] = [
  {
    id: 'shell-01',
    description: "You see a figure shrouded in static, standing near a vending machine that sells memories.",
    tempAlias: 'Unknown_0x7F',
    visualHint: 'bg-electric-blue/5'
  },
  {
    id: 'shell-02',
    description: "A silhouette watching the rain from a high-rise window. The glass vibrates with low-frequency bass.",
    tempAlias: 'Unknown_0xB2',
    visualHint: 'bg-purple-500/5'
  },
  {
    id: 'shell-03',
    description: "Someone in a hazard suit painting recursive fractals on a subway wall.",
    tempAlias: 'Unknown_0xC4',
    visualHint: 'bg-emerald-500/5'
  },
  {
    id: 'shell-04',
    description: "An echo in the network. No physical form detected, only a pattern of rhythmic data packets.",
    tempAlias: 'Unknown_0xFF',
    visualHint: 'bg-alert-red/5'
  }
];

// ------------------------------------------------------------------
// COMPONENT: TYPEWRITER LOGS (The Mask)
// ------------------------------------------------------------------
const TerminalLog: React.FC<{ logs: string[] }> = ({ logs }) => {
  return (
    <div className="font-mono text-xs text-electric-blue/70 space-y-1 mt-4 h-24 overflow-hidden border-l-2 border-electric-blue/30 pl-3">
      {logs.map((log, i) => (
        <motion.div
          key={i}
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          className="truncate"
        >
          {log}
        </motion.div>
      ))}
      <motion.div
        animate={{ opacity: [0, 1, 0] }}
        transition={{ repeat: Infinity, duration: 0.8 }}
        className="w-2 h-4 bg-electric-blue inline-block align-middle ml-1"
      />
    </div>
  );
};

// ------------------------------------------------------------------
// MAIN COMPONENT: DISTRICT ZERO
// ------------------------------------------------------------------
interface DistrictZeroProps {
  onAgentForged: (id: string) => void;
  connect: (agentId: string) => Promise<void>;
  disconnect: () => void;
}

export const DistrictZero: React.FC<DistrictZeroProps> = ({ onAgentForged, connect, disconnect }) => {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [phase, setPhase] = useState<'idle' | 'approach' | 'scan' | 'contact' | 'error'>('idle');
  const [logs, setLogs] = useState<string[]>([]);
  const [forgedAgent, setForgedAgent] = useState<{ id: string; name: string } | null>(null);

  // ------------------------------------------------------------------
  // INTERACTION LOOP
  // ------------------------------------------------------------------
  const handleSocialize = (id: string) => {
    setSelectedId(id);
    setPhase('approach');
    setLogs([]);
    setForgedAgent(null);

    // Sequence Choreography
    setTimeout(() => {
      setPhase('scan');
      runScanSequence(); // Visuals Only
      forgeTheSoul(id);  // API Call
    }, 800); // 0.8s Approach
  };

  const forgeTheSoul = async (shellId: string) => {
    try {
      const shell = ENIGMA_DATA.find(e => e.id === shellId);
      if (!shell) throw new Error("Shell not found");

      // 1. Call the Forge
      const response = await fetch('/api/agents/forge_hollow', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ aesthetic_description: shell.description })
      });

      if (!response.ok) throw new Error("Forge failed");

      const data = await response.json();

      // 2. Transition (Phase C)
      // We wait a bit if the API was too fast to let the animation breathe?
      // Nah, instant gratification is better for "Success".

      setForgedAgent({ id: data.id, name: data.name });
      onAgentForged(data.id); // Update App State

      // 3. Ignite WebSocket
      await connect(data.id);

      setPhase('contact');

    } catch (err) {
      console.error("Forging Protocol Failed:", err);
      // Silent Grace
      setPhase('error');
      setTimeout(() => {
        handleDisconnect();
      }, 2500);
    }
  };

  const runScanSequence = () => {
    const sequence = [
      { text: "> ESTABLISHING NEURAL HANDSHAKE...", delay: 200 },
      { text: "> INTERCEPTING FREQUENCY...", delay: 800 },
      { text: "> DECRYPTING BIO-SIGNATURE...", delay: 1500 },
      { text: "> [FORJANDO ALMA... ESTABLECIENDO VÍNCULO NEURONAL]", delay: 2200 },
      // Removed automatic transition to 'contact' here, controlled by forgeTheSoul
    ];

    setLogs([]); // Reset

    sequence.forEach((step) => {
      setTimeout(() => {
        // Only update logs if we are still scanning (prevent leaks if error happened)
        setPhase(current => {
          if (current === 'scan') {
             setLogs(prev => [...prev, step.text]);
          }
          return current;
        });
      }, step.delay);
    });
  };

  const handleDisconnect = () => {
    disconnect(); // Sever the WebSocket
    setPhase('idle');
    setTimeout(() => {
      setSelectedId(null);
      setLogs([]);
      setForgedAgent(null);
    }, 500); // Wait for exit animation
  };

  // ------------------------------------------------------------------
  // RENDER
  // ------------------------------------------------------------------
  return (
    <div className="w-full h-full relative overflow-hidden flex items-center justify-center p-8">

      {/* BACKGROUND AMBIENCE */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-0 left-0 w-full h-full bg-[radial-gradient(circle_at_center,_var(--color-abyssal-black)_0%,_#000_100%)] opacity-90" />
        <div className="grid-overlay opacity-10" />
      </div>

      {/* HEADER (Only visible in Grid) */}
      <AnimatePresence>
        {!selectedId && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="absolute top-32 left-8 z-10"
          >
            <h2 className="font-monumental text-3xl text-white tracking-widest flex items-center gap-3">
              <Network className="w-8 h-8 text-electric-blue" />
              DISTRICT ZERO <span className="text-electric-blue text-sm font-technical border border-electric-blue px-2 py-0.5">PUBLIC_SECTOR</span>
            </h2>
            <p className="font-narrative text-white/40 text-sm max-w-md mt-2">
              Intercept signals from the void. These entities are unverified. Proceed with caution.
            </p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* GRID VIEW */}
      <div className="relative z-20 w-full max-w-6xl flex flex-wrap gap-6 justify-center items-center">
        <AnimatePresence>
          {/* RENDER CARDS (If none selected, show all. If selected, only show the active one in expanded mode) */}
          {ENIGMA_DATA.map((shell) => {
            const isSelected = selectedId === shell.id;
            const isHidden = selectedId && !isSelected;

            if (isHidden) return null;

            return (
              <motion.div
                key={shell.id}
                layoutId={`card-${shell.id}`}
                className={`
                  relative bg-vintage-navy/40 border border-white/10 backdrop-blur-md overflow-hidden
                  ${isSelected ? 'w-[600px] h-[500px] z-50' : 'w-72 h-96 hover:border-electric-blue/50 cursor-pointer'}
                `}
                style={{
                  clipPath: isSelected
                    ? 'polygon(0 0, 100% 0, 100% 90%, 95% 100%, 0 100%)'
                    : 'polygon(10% 0, 100% 0, 100% 90%, 90% 100%, 0 100%, 0 10%)'
                }}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                transition={{ duration: 0.5, type: "spring", stiffness: 200, damping: 25 }}
                onClick={() => !selectedId && handleSocialize(shell.id)}
              >
                {/* CARD CONTENT */}
                <div className="p-6 flex flex-col h-full relative">

                  {/* SCANLINES OVERLAY */}
                  <div className="absolute inset-0 bg-scanlines opacity-10 pointer-events-none" />

                  {/* HEADER */}
                  <div className="flex justify-between items-start mb-4">
                    <motion.div layoutId={`title-${shell.id}`} className="font-monumental text-2xl text-white">
                      {isSelected && forgedAgent ? forgedAgent.name : "???"}
                    </motion.div>
                    <div className="flex items-center gap-2">
                         {isSelected && phase === 'contact' ? (
                             <span className="text-electric-blue animate-pulse font-technical tracking-widest">LIVE SIGNAL</span>
                         ) : isSelected && phase === 'error' ? (
                             <span className="text-alert-red font-technical tracking-widest">SIGNAL LOST</span>
                         ) : (
                             <Activity size={16} className="text-white/20" />
                         )}
                    </div>
                  </div>

                  {/* VISUALIZER / CONTENT AREA */}
                  <div className={`flex-1 relative flex items-center justify-center bg-abyssal-black/30 border ${phase === 'error' ? 'border-alert-red/50' : 'border-white/5'} mb-6 overflow-hidden transition-colors duration-300`}>

                    {/* IDLE STATE */}
                    {(!isSelected || phase === 'approach') && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="text-white/20 font-technical text-6xl tracking-widest opacity-20"
                        >
                            ENIGMA
                        </motion.div>
                    )}

                    {/* SCAN PHASE */}
                    {phase === 'scan' && isSelected && (
                        <div className="absolute inset-0 flex flex-col items-center justify-center">
                            <motion.div
                                animate={{ rotate: 360 }}
                                transition={{ duration: 3, ease: "linear", repeat: Infinity }}
                                className="w-24 h-24 border-2 border-dashed border-electric-blue rounded-full opacity-50 mb-4"
                            />
                            <div className="glitch-text font-monumental text-electric-blue text-sm tracking-widest text-center px-4">
                                [FORJANDO ALMA... <br/> ESTABLECIENDO VÍNCULO NEURONAL]
                            </div>
                        </div>
                    )}

                    {/* ERROR PHASE */}
                    {phase === 'error' && isSelected && (
                        <div className="absolute inset-0 flex flex-col items-center justify-center">
                             <div className="font-monumental text-alert-red text-2xl tracking-widest mb-2">CONNECTION FAILED</div>
                             <div className="font-mono text-xs text-alert-red/70">NEURAL HANDSHAKE REJECTED</div>
                        </div>
                    )}

                    {/* CONTACT PHASE (MOCK) */}
                    {phase === 'contact' && isSelected && (
                         <div className="absolute inset-0 flex items-center justify-center gap-1 w-full px-12">
                             {/* Mock Waveform */}
                             {[...Array(20)].map((_, i) => (
                                 <motion.div
                                     key={i}
                                     className="w-2 bg-electric-blue/50 rounded-full"
                                     animate={{
                                         height: [10, Math.random() * 60 + 20, 10],
                                         opacity: [0.5, 1, 0.5]
                                     }}
                                     transition={{
                                         duration: 0.5,
                                         repeat: Infinity,
                                         repeatType: "mirror",
                                         delay: i * 0.05
                                     }}
                                 />
                             ))}
                         </div>
                    )}
                  </div>

                  {/* TEXT / LOGS */}
                  <div className="min-h-[100px]">
                      {isSelected && phase === 'scan' ? (
                          <TerminalLog logs={logs} />
                      ) : isSelected && phase === 'contact' ? (
                          <div className="flex flex-col gap-2">
                              <div className="font-monumental text-electric-blue text-xl">
                                  {forgedAgent?.name || shell.tempAlias}
                              </div>
                              <div className="font-mono text-xs text-white/50">
                                  {'>'} Connection stable. <br/>
                                  {'>'} Audio channel open. <br/>
                                  {'>'} Waiting for input...
                              </div>
                          </div>
                      ) : isSelected && phase === 'error' ? (
                          <div className="text-alert-red font-mono text-xs">
                              {'>'} ERROR: 0xDEADDEAD <br/>
                              {'>'} RETRYING IN 3s...
                          </div>
                      ) : (
                        <p className="font-narrative text-white/70 text-sm leading-relaxed">
                            {shell.description}
                        </p>
                      )}
                  </div>

                  {/* ACTIONS */}
                  <div className="mt-6 flex justify-end">
                    {!isSelected ? (
                         <button className="kizuna-shard-btn-wrapper group">
                             <div className="kizuna-shard-btn-inner text-xs py-2 px-6 group-hover:bg-electric-blue group-hover:text-black transition-colors">
                                 <Radio size={14} /> SOCIALIZE
                             </div>
                         </button>
                    ) : phase === 'contact' && (
                        <button
                            onClick={(e) => { e.stopPropagation(); handleDisconnect(); }}
                            className="bg-alert-red/10 border border-alert-red text-alert-red hover:bg-alert-red hover:text-white transition-all px-6 py-3 font-monumental text-sm tracking-widest flex items-center gap-2"
                            style={{ clipPath: 'polygon(10% 0, 100% 0, 100% 80%, 90% 100%, 0 100%, 0 20%)' }}
                        >
                            <X size={16} /> TERMINATE LINK
                        </button>
                    )}
                  </div>

                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>

    </div>
  );
};
