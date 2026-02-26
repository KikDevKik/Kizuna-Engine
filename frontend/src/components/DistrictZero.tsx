import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Activity, X, Network, ChevronLeft, ChevronRight, Eye } from 'lucide-react';
import { useRoster } from '../contexts/RosterContext';
import '../KizunaHUD.css';

// ------------------------------------------------------------------
// DATA: THE LOCAL MATRIX (ILLUSION PROTOCOL)
// ------------------------------------------------------------------
interface EnigmaIdentity {
  id: string;
  description: string;
  tempAlias: string;
  visualHint: string;
  is_nemesis?: boolean;
  is_gossip?: boolean;
}

const ENIGMA_DATA_EN: EnigmaIdentity[] = [
  { id: 'shell-01', tempAlias: '???', visualHint: 'bg-electric-blue/5', description: "You see a figure shrouded in static, standing near a vending machine that sells memories." },
  { id: 'shell-02', tempAlias: '???', visualHint: 'bg-purple-500/5', description: "A silhouette watching the rain from a high-rise window. The glass vibrates with low-frequency bass." },
  { id: 'shell-03', tempAlias: '???', visualHint: 'bg-emerald-500/5', description: "Someone in a hazard suit painting recursive fractals on a subway wall." },
  { id: 'shell-04', tempAlias: '???', visualHint: 'bg-alert-red/5', description: "An echo in the network. No physical form detected, only a pattern of rhythmic data packets." },
  { id: 'shell-05', tempAlias: '???', visualHint: 'bg-yellow-500/5', description: "A drone pilot fixing a rusted mechanical wing in a neon-lit alleyway." },
  { id: 'shell-06', tempAlias: '???', visualHint: 'bg-pink-500/5', description: "A holographic pop-idol glitching in and out of existence, singing a silent ballad." },
];

const ENIGMA_DATA_ES: EnigmaIdentity[] = [
  { id: 'shell-01', tempAlias: '???', visualHint: 'bg-electric-blue/5', description: "Ves una figura envuelta en estática, de pie junto a una máquina expendedora que vende recuerdos." },
  { id: 'shell-02', tempAlias: '???', visualHint: 'bg-purple-500/5', description: "Una silueta observando la lluvia desde la ventana de un rascacielos. El cristal vibra con un bajo de baja frecuencia." },
  { id: 'shell-03', tempAlias: '???', visualHint: 'bg-emerald-500/5', description: "Alguien con un traje de protección pintando fractales recursivos en la pared de un metro." },
  { id: 'shell-04', tempAlias: '???', visualHint: 'bg-alert-red/5', description: "Un eco en la red. No se detecta forma física, solo un patrón de paquetes de datos rítmicos." },
  { id: 'shell-05', tempAlias: '???', visualHint: 'bg-yellow-500/5', description: "Un piloto de drones reparando un ala mecánica oxidada en un callejón iluminado por neón." },
  { id: 'shell-06', tempAlias: '???', visualHint: 'bg-pink-500/5', description: "Una ídolo pop holográfica fallando y desapareciendo, cantando una balada silenciosa." },
  { id: 'shell-07', tempAlias: '???', visualHint: 'bg-cyan-500/5', description: "Un mensajero que lleva un paquete que brilla con radiación Cherenkov." },
  { id: 'shell-08', tempAlias: '???', visualHint: 'bg-orange-500/5', description: "Un monje meditativo conectado a un árbol que crece cables de fibra óptica." },
  { id: 'shell-09', tempAlias: '???', visualHint: 'bg-indigo-500/5', description: "Un vendedor ambulante cocinando fideos que huelen a ozono y nostalgia." },
  { id: 'shell-10', tempAlias: '???', visualHint: 'bg-lime-500/5', description: "Un vendedor tecleando en un teclado invisible, sus ojos reflejan código en movimiento." },
  { id: 'shell-11', tempAlias: '???', visualHint: 'bg-rose-500/5', description: "Un androide perdido mirando a una mariposa con confusión y asombro." },
  { id: 'shell-12', tempAlias: '???', visualHint: 'bg-slate-500/5', description: "El vacío mismo, tomando la forma de una persona por un breve momento." },
];

const getEnigmaData = () => {
    const lang = navigator.language || 'en';
    return lang.startsWith('es') ? ENIGMA_DATA_ES : ENIGMA_DATA_EN;
};

const VISIBLE_COUNT = 3;

// ------------------------------------------------------------------
// COMPONENT: TYPEWRITER LOGS
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
  const { refreshAgents } = useRoster();
  const enigmaPoolStatic = getEnigmaData();

  // Ephemeral Alley State
  const [enigmaPool, setEnigmaPool] = useState<EnigmaIdentity[]>(enigmaPoolStatic);
  const [visibleCards, setVisibleCards] = useState<EnigmaIdentity[]>(() => enigmaPoolStatic.slice(0, VISIBLE_COUNT));
  const [slideDirection, setSlideDirection] = useState(0);
  const [backgroundOffset, setBackgroundOffset] = useState(0);

  // Module 1.5: Fetch Strangers (Nemesis/Gossip)
  useEffect(() => {
    const fetchStrangers = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/agents/strangers');
        if (res.ok) {
          const strangers: EnigmaIdentity[] = await res.json();
          if (strangers.length > 0) {
              setEnigmaPool(prev => [...strangers, ...prev]);
          }
        }
      } catch (e) {
        console.error("Failed to fetch strangers:", e);
      }
    };
    fetchStrangers();
  }, []);

  // Focus Mode State
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [phase, setPhase] = useState<'idle' | 'approach' | 'scan' | 'contact' | 'error'>('idle');
  const [logs, setLogs] = useState<string[]>([]);
  const [forgedAgent, setForgedAgent] = useState<{ id: string; name: string } | null>(null);

  // ------------------------------------------------------------------
  // NAVIGATION LOGIC (The Ephemeral Alley)
  // ------------------------------------------------------------------
  const slide = useCallback((direction: number) => {
    if (selectedId) return;

    setSlideDirection(direction);
    setBackgroundOffset(prev => prev - (direction * 50));

    const currentIds = new Set(visibleCards.map(c => c.id));
    const availablePool = enigmaPool.filter(c => !currentIds.has(c.id));
    const pool = availablePool.length >= VISIBLE_COUNT ? availablePool : enigmaPool;

    const newCards: EnigmaIdentity[] = [];
    const tempPool = [...pool];

    for (let i = 0; i < VISIBLE_COUNT; i++) {
        const randomIndex = Math.floor(Math.random() * tempPool.length);
        newCards.push(tempPool[randomIndex]);
        tempPool.splice(randomIndex, 1);
    }

    setVisibleCards(newCards);
  }, [selectedId, visibleCards, enigmaPool]);

  // Keyboard Nav
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (selectedId) return;
      if (e.key === 'ArrowLeft') slide(-1);
      if (e.key === 'ArrowRight') slide(1);
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [slide, selectedId]);

  // ------------------------------------------------------------------
  // INTERACTION LOOP
  // ------------------------------------------------------------------
  const handleObserve = (id: string) => {
    setSelectedId(id);
    setPhase('approach');
    setLogs([]);
    setForgedAgent(null);
  };

  const handleForgeBond = (id: string) => {
    setPhase('scan');
    runScanSequence();
    forgeTheSoul(id);
  };

  const forgeTheSoul = async (shellId: string) => {
    try {
      const shell = enigmaPool.find(e => e.id === shellId);
      if (!shell) throw new Error("Shell not found");

      if (shell.is_nemesis || shell.is_gossip) {
          setForgedAgent({ id: shell.id, name: shell.tempAlias.replace(" (Hostil)", "") });
          onAgentForged(shell.id);
          await connect(shell.id);
          setPhase('contact');
          return;
      }
      
      const response = await fetch('http://localhost:8000/api/agents/forge_hollow', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ aesthetic_description: shell.description })
      });

      if (!response.ok) throw new Error("Forge failed");

      const data = await response.json();
      await refreshAgents();

      setForgedAgent({ id: data.id, name: data.name });
      onAgentForged(data.id);
      await connect(data.id);
      setPhase('contact');

    } catch (err) {
      console.error("Forging Protocol Failed:", err);
      setPhase('error');
      setTimeout(() => handleDisconnect(), 2500);
    }
  };

  const runScanSequence = () => {
    const sequence = [
      { text: "> ESTABLISHING NEURAL HANDSHAKE...", delay: 200 },
      { text: "> INTERCEPTING FREQUENCY...", delay: 800 },
      { text: "> DECRYPTING BIO-SIGNATURE...", delay: 1500 },
      { text: "> [FORJANDO ALMA... ESTABLECIENDO VÍNCULO NEURONAL]", delay: 2200 },
    ];
    setLogs([]);
    sequence.forEach((step) => {
      setTimeout(() => {
        setPhase(current => {
          if (current === 'scan') setLogs(prev => [...prev, step.text]);
          return current;
        });
      }, step.delay);
    });
  };

  const handleDisconnect = () => {
    disconnect();
    setPhase('idle');
    setTimeout(() => {
      setSelectedId(null);
      setLogs([]);
      setForgedAgent(null);
    }, 500);
  };

  return (
    <div className="w-full h-full relative overflow-hidden flex items-center justify-center p-8">
      <motion.div
        className="layer-abyssal-background absolute inset-0 pointer-events-none"
        animate={{ backgroundPositionX: backgroundOffset }}
        transition={{ type: "spring", stiffness: 50, damping: 20 }}
      />
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-0 left-0 w-full h-full bg-[radial-gradient(circle_at_center,_var(--color-abyssal-black)_0%,_#000_100%)] opacity-90" />
        <div className="grid-overlay opacity-10" />
      </div>

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
              Intercepción de señales del vacío. Entidades no verificadas. Proceder con precaución.
            </p>
          </motion.div>
        )}
      </AnimatePresence>

      {!selectedId && (
        <>
            <button onClick={() => slide(-1)} className="absolute left-8 top-1/2 -translate-y-1/2 z-30 p-4 text-electric-blue/50 hover:text-electric-blue transition-colors">
                <ChevronLeft size={48} />
            </button>
            <button onClick={() => slide(1)} className="absolute right-8 top-1/2 -translate-y-1/2 z-30 p-4 text-electric-blue/50 hover:text-electric-blue transition-colors">
                <ChevronRight size={48} />
            </button>
        </>
      )}

      <div className="relative z-20 w-full max-w-6xl flex justify-center items-center h-[600px]">
        <AnimatePresence mode="wait">
          {selectedId ? (
              enigmaPool.filter(shell => shell.id === selectedId).map(shell => (
                  <motion.div key={`focus-${shell.id}`} initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 1.1 }} transition={{ duration: 0.5 }} className="z-50">
                      <Card shell={shell} isSelected={true} phase={phase} logs={logs} forgedAgent={forgedAgent} onDisconnect={handleDisconnect} onForge={() => handleForgeBond(shell.id)} />
                  </motion.div>
              ))
          ) : (
              <motion.div key={`carousel-${visibleCards.map(c => c.id).join('-')}`} className="flex items-center justify-center gap-8" initial={{ x: slideDirection * 100, opacity: 0 }} animate={{ x: 0, opacity: 1 }} exit={{ x: slideDirection * -100, opacity: 0 }} transition={{ type: "spring", stiffness: 300, damping: 30 }}>
                  {visibleCards.map((shell) => (
                      <Card key={shell.id} shell={shell} isSelected={false} phase={phase} logs={[]} forgedAgent={null} onObserve={() => handleObserve(shell.id)} />
                  ))}
              </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

const Card: React.FC<CardProps> = ({ shell, isSelected, phase, logs, forgedAgent, onObserve, onForge, onDisconnect }) => {
    return (
        <motion.div
            className={`relative bg-vintage-navy/40 border backdrop-blur-md overflow-hidden transition-all duration-300
                ${shell.is_nemesis ? 'border-alert-red shadow-[0_0_15px_rgba(255,0,0,0.3)]' : shell.is_gossip ? 'border-purple-500 shadow-[0_0_15px_rgba(168,85,247,0.3)]' : 'border-white/10'}
                ${isSelected ? 'w-[600px] h-[500px] shadow-2xl' : 'w-72 h-96 hover:scale-105 cursor-pointer'}
            `}
            style={{ clipPath: isSelected ? 'polygon(0 0, 100% 0, 100% 90%, 95% 100%, 0 100%)' : 'polygon(10% 0, 100% 0, 100% 90%, 90% 100%, 0 100%, 0 10%)' }}
            onClick={() => !isSelected && onObserve && onObserve()}
        >
            <div className="p-6 flex flex-col h-full relative">
                <div className="absolute inset-0 bg-scanlines opacity-10 pointer-events-none" />
                <div className="flex justify-between items-start mb-4">
                    <div className="font-monumental text-2xl text-white">{isSelected && forgedAgent ? forgedAgent.name : shell.tempAlias}</div>
                    <Activity size={16} className="text-white/20" />
                </div>

                <div className={`flex-1 relative flex items-center justify-center bg-abyssal-black/30 border ${phase === 'error' ? 'border-alert-red/50' : 'border-white/5'} mb-6 overflow-hidden transition-colors duration-300`}>
                    {(!isSelected || phase === 'approach') && <div className="text-white/20 font-technical text-6xl tracking-widest opacity-20">ENIGMA</div>}
                    {phase === 'scan' && isSelected && (
                        <div className="absolute inset-0 flex flex-col items-center justify-center">
                            <motion.div animate={{ rotate: 360 }} transition={{ duration: 3, ease: "linear", repeat: Infinity }} className="w-24 h-24 border-2 border-dashed border-electric-blue rounded-full opacity-50 mb-4" />
                            <div className="glitch-text font-monumental text-electric-blue text-sm tracking-widest text-center px-4">[FORJANDO ALMA... <br/> VÍNCULO NEURONAL]</div>
                        </div>
                    )}
                    {phase === 'contact' && isSelected && (
                        <div className="absolute inset-0 flex items-center justify-center gap-1 w-full px-12">
                            {[...Array(20)].map((_, i) => (
                                <motion.div key={i} className="w-2 bg-electric-blue/50 rounded-full" animate={{ height: [10, Math.random() * 60 + 20, 10], opacity: [0.5, 1, 0.5] }} transition={{ duration: 0.5, repeat: Infinity, repeatType: "mirror", delay: i * 0.05 }} />
                            ))}
                        </div>
                    )}
                </div>

                <div className="min-h-[100px]">
                    {isSelected && phase === 'scan' ? <TerminalLog logs={logs} /> : isSelected && phase === 'contact' ? (
                        <div className="flex flex-col gap-2">
                            <div className="font-monumental text-electric-blue text-xl">{forgedAgent?.name || shell.tempAlias}</div>
                            <div className="font-mono text-xs text-white/50">{'>'} Señal estable. Audio abierto. Esperando entrada...</div>
                        </div>
                    ) : <p className="font-narrative text-white/70 text-sm leading-relaxed">{shell.description}</p>}
                </div>

                <div className="mt-6 flex justify-end w-full">
                {!isSelected ? (
                    <button className="kizuna-shard-btn-wrapper group w-full">
                        <div className="kizuna-shard-btn-inner text-xs py-2 px-6 group-hover:bg-electric-blue group-hover:text-black transition-colors flex items-center justify-center gap-2"><Eye size={14} /> [ OBSERVAR ]</div>
                    </button>
                ) : (
                    <>
                        {phase === 'approach' && (
                            <div className="flex gap-4 w-full">
                                <button onClick={(e) => { e.stopPropagation(); onDisconnect && onDisconnect(); }} className="flex-1 border border-white/20 text-white/50 hover:text-white hover:border-white transition-all py-3 font-technical tracking-widest text-xs">[ ABORTAR ]</button>
                                <button onClick={(e) => { e.stopPropagation(); onForge && onForge(); }} className="flex-[2] bg-electric-blue text-black font-monumental tracking-widest text-sm hover:bg-white hover:scale-105 transition-all shadow-[0_0_20px_rgba(0,209,255,0.4)]" style={{ clipPath: 'polygon(10% 0, 100% 0, 100% 80%, 90% 100%, 0 100%, 0 20%)' }}>[ FORJAR VÍNCULO ]</button>
                            </div>
                        )}
                        {phase === 'contact' && (
                            <button onClick={(e) => { e.stopPropagation(); onDisconnect && onDisconnect(); }} className="bg-alert-red/10 border border-alert-red text-alert-red hover:bg-alert-red hover:text-white transition-all px-6 py-3 font-monumental text-sm tracking-widest flex items-center gap-2 w-full justify-center" style={{ clipPath: 'polygon(10% 0, 100% 0, 100% 80%, 90% 100%, 0 100%, 0 20%)' }}><X size={16} /> TERMINATE LINK</button>
                        )}
                    </>
                )}
                </div>
            </div>
        </motion.div>
    );
};

interface CardProps {
    shell: EnigmaIdentity;
    isSelected: boolean;
    phase: string;
    logs: string[];
    forgedAgent: { name: string } | null;
    onObserve?: () => void;
    onForge?: () => void;
    onDisconnect?: () => void;
}
