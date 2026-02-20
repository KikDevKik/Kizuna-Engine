import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus } from 'lucide-react';
import { SoulForgeModal } from './SoulForgeModal';
import '../KizunaHUD.css';

interface Agent {
  id: string;
  name: string;
  role: string;
  avatar_path?: string | null;
  systemStatus?: string;
}

interface AgentRosterProps {
  onSelect?: (agentId: string) => void;
}

// ------------------------------------------------------------------
// ANIMATION VARIANTS (Container & UI)
// ------------------------------------------------------------------
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.06,
      delayChildren: 0.1
    }
  },
  exit: {
    opacity: 0,
    transition: { staggerChildren: 0.03, staggerDirection: -1 }
  }
};

const shardVariants = {
  hidden: {
    y: 100,
    opacity: 0,
    scale: 0.6,
    rotateX: -45,
    rotateZ: 10,
    filter: "blur(10px)"
  },
  visible: {
    y: 0,
    opacity: 1,
    scale: 1,
    rotateX: 0,
    rotateZ: 0,
    filter: "blur(0px)",
    transition: {
      type: "spring" as const,
      stiffness: 200,
      damping: 20,
      mass: 0.8
    }
  },
  exit: {
    y: -50,
    opacity: 0,
    filter: "blur(10px)",
    transition: { duration: 0.2 }
  }
};

export const AgentRoster: React.FC<AgentRosterProps> = ({ onSelect }) => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [activeIndex, setActiveIndex] = useState(0);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch Agents
  const fetchAgents = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const res = await fetch('http://localhost:8000/api/agents/');

      if (!res.ok) {
        throw new Error(`Failed to fetch agents: ${res.statusText}`);
      }

      const data = await res.json();

      if (!Array.isArray(data)) {
        throw new Error("Invalid API response format");
      }

      // Transform data
      const loadedAgents: Agent[] = data.map((a: any) => ({
        id: a.id,
        name: a.name,
        role: a.role || 'UNKNOWN',
        avatar_path: a.avatar_path,
        systemStatus: 'ONLINE'
      }));

      // Ensure consistent sort order (by Name)
      loadedAgents.sort((a, b) => a.name.localeCompare(b.name));

      // Append the "Create New" card
      const createCard: Agent = {
        id: 'create-new',
        name: 'NEW SOUL',
        role: 'INITIALIZE',
        systemStatus: 'WAITING'
      };

      setAgents([...loadedAgents, createCard]);

      // Ensure active index is valid
      if (activeIndex >= loadedAgents.length + 1) {
          setActiveIndex(0);
      }

    } catch (err: any) {
      console.error("Error fetching agents:", err);
      setError(err.message);
      // Fallback
      setAgents([{
          id: 'create-new',
          name: 'NEW SOUL',
          role: 'INITIALIZE',
          systemStatus: 'WAITING'
      }]);
    } finally {
      setIsLoading(false);
    }
  }, []); // Removed activeIndex dependency

  useEffect(() => {
    fetchAgents();
  }, [fetchAgents]);

  // ------------------------------------------------------------------
  // AUTONOMOUS AGENT LOGIC (Option B)
  // ------------------------------------------------------------------

  // Strict Linear Navigation (No Wrapping)
  const rotateCarousel = (direction: number) => {
    if (agents.length === 0) return;
    setActiveIndex((prev) => {
      const next = prev + direction;
      // Clamp values
      if (next < 0) return 0;
      if (next >= agents.length) return agents.length - 1;
      return next;
    });
  };

  const handleSelect = () => {
    const selected = agents[activeIndex];
    if (!selected) return;

    if (selected.id === 'create-new') {
      setIsModalOpen(true);
    } else if (onSelect) {
      onSelect(selected.id);
    }
  };

  const handleAgentCreated = async () => {
    await fetchAgents();
  };

  // Determine Card Style based on relative offset
  const getCardStyle = (index: number) => {
    const offset = index - activeIndex;
    const absOffset = Math.abs(offset);
    const direction = offset > 0 ? 1 : -1;

    // Base Transition Config
    const transition = {
      type: "spring" as const,
      stiffness: 300,
      damping: 30,
      mass: 1
    };

    // 1. ACTIVE CENTER CARD (Focus)
    if (offset === 0) {
      return {
        x: 0,
        z: 0,
        rotateY: 0,
        scale: 1.1,
        opacity: 1,
        zIndex: 100,
        filter: "blur(0px) brightness(1.2) drop-shadow(0 0 30px rgba(0,209,255,0.3))",
        transition
      };
    }

    // 2. IMMEDIATE NEIGHBORS (Visible Side Cards)
    if (absOffset === 1) {
      return {
        x: direction * 320, // Spread out to sides
        z: -100,            // Push back slightly
        rotateY: direction * -15, // Angle inward slightly to face camera
        scale: 0.9,
        opacity: 0.7,
        zIndex: 90,
        filter: "blur(0px) brightness(0.6)",
        transition
      };
    }

    // 3. DISTANT STACK (Deck Effect)
    // Tightly stacked behind the neighbors
    const baseStackX = direction * 380;
    const stackSpacing = 20;
    const stackZ = -200 - (absOffset * 40);

    return {
      x: baseStackX + (direction * (absOffset - 2) * stackSpacing),
      z: stackZ,
      rotateY: direction * -5, // Flatter angle for the stack
      scale: 0.8,
      opacity: 0.2, // Faded
      zIndex: 80 - absOffset,
      filter: "blur(4px) brightness(0.4)",
      transition
    };
  };

  if (isLoading && agents.length === 0) {
      return <div className="text-cyan-500 font-technical text-center mt-20 animate-pulse">ESTABLISHING LINK...</div>;
  }

  const isFirst = activeIndex === 0;
  const isLast = activeIndex === agents.length - 1;

  return (
    <>
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        exit="exit"
        className="flex flex-col items-center justify-center w-full h-[700px] relative overflow-hidden"
      >
        {error && (
            <div className="absolute top-4 text-red-500 font-mono text-xs bg-black/50 p-2 border border-red-500 z-50">
                CONNECTION_ERROR: {error}
            </div>
        )}

        {/* 3D STAGE - Single Relative Container */}
        <div
          className="w-full h-[450px] flex items-center justify-center relative"
          style={{ perspective: "1200px" }} // Perspective on container
        >
            <AnimatePresence>
            {agents.map((agent, index) => {
              const isCreateCard = agent.id === 'create-new';
              const isFocused = activeIndex === index;

              // Only render if within reasonable range to save DOM performance
              // (Optional optimization, but good for large lists)
              if (Math.abs(index - activeIndex) > 5) return null;

              return (
                <motion.div
                  key={agent.id}
                  layoutId={`agent-card-${agent.id}`}
                  className="absolute w-[260px] h-[380px]" // Fixed size card
                  initial={false}
                  animate={getCardStyle(index)}
                  style={{
                    transformStyle: "preserve-3d",
                    cursor: "pointer"
                  }}
                  onClick={() => setActiveIndex(index)}
                >
                  {/* CARD CONTENT */}
                  <div
                    className={`agent-card-glass w-full h-full ${isFocused ? 'border-cyan-400' : 'border-slate-700'}`}
                  >
                    {isCreateCard ? (
                      // CREATE NEW CARD CONTENT
                      <div className="flex flex-col items-center justify-center h-full gap-4 text-cyan-400">
                        <div className="p-4 border border-dashed border-cyan-400/50 rounded-full">
                          <Plus size={48} />
                        </div>
                        <h2 className="font-monumental text-xl tracking-widest text-center">FORGE NEW SOUL</h2>
                      </div>
                    ) : (
                      // AGENT CARD CONTENT
                      <>
                        {/* Avatar / Visual Placeholder */}
                        <div className="flex-1 flex items-center justify-center mb-4 relative overflow-hidden bg-black/20 rounded-sm">
                           {agent.avatar_path ? (
                             <img src={agent.avatar_path} alt={agent.name} className="w-full h-full object-cover opacity-90" />
                           ) : (
                             // TYPOGRAPHIC FALLBACK
                             <div className="relative w-full h-full flex items-center justify-center">
                               <div className="absolute inset-0 border border-cyan-400/10" />
                               <span className="font-monumental text-6xl text-cyan-400/80 drop-shadow-[0_0_15px_rgba(0,209,255,0.5)]">
                                 {agent.name.charAt(0).toUpperCase()}
                               </span>
                             </div>
                           )}
                        </div>

                        <div className="flex flex-col gap-1">
                          <h2 className="agent-card-title text-3xl truncate">{agent.name}</h2>
                          <p className="agent-card-role text-xs tracking-widest text-cyan-200/70 uppercase">{agent.role}</p>
                        </div>

                        <div className="mt-4">
                          <div className="w-full h-[1px] bg-white/10 my-2" />
                          <div className="flex justify-between items-end">
                             <span className="font-technical text-2xl text-cyan-300">
                                {agent.systemStatus === 'ONLINE' ? '100%' : '---'}
                             </span>
                             <span className="font-technical text-xs text-white/50">
                                {agent.systemStatus}
                             </span>
                          </div>
                        </div>
                      </>
                    )}
                  </div>
                </motion.div>
              );
            })}
            </AnimatePresence>
        </div>

        {/* CONTROLS */}
        <motion.div variants={shardVariants} className="mt-12 flex gap-8 z-50 relative">
          <button
            onClick={() => rotateCarousel(-1)}
            disabled={isFirst}
            className={`kizuna-shard-btn-wrapper transition-opacity duration-300 ${isFirst ? 'opacity-30 cursor-not-allowed' : 'opacity-100'}`}
          >
            <div className="kizuna-shard-btn-inner">
               &lt; PREV
            </div>
          </button>

          <button
            onClick={handleSelect}
            className="kizuna-shard-btn-wrapper"
          >
             <span className="kizuna-shard-btn-inner">
               {agents[activeIndex]?.id === 'create-new' ? 'INITIALIZE' : 'INITIATE LINK'}
             </span>
          </button>

          <button
            onClick={() => rotateCarousel(1)}
            disabled={isLast}
            className={`kizuna-shard-btn-wrapper transition-opacity duration-300 ${isLast ? 'opacity-30 cursor-not-allowed' : 'opacity-100'}`}
          >
            <div className="kizuna-shard-btn-inner">
              NEXT &gt;
            </div>
          </button>
        </motion.div>
      </motion.div>

      <SoulForgeModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onCreated={handleAgentCreated}
      />
    </>
  );
};
