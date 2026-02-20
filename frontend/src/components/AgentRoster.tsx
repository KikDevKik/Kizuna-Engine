import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Plus } from 'lucide-react';
import { SoulForgeModal } from './SoulForgeModal';
import '../KizunaHUD.css';

interface Agent {
  id: string;
  name: string;
  role: string;
  avatar_path?: string | null;
  systemStatus?: string; // Optional decoration
}

interface AgentRosterProps {
  onSelect?: (agent: Agent) => void;
}

// ------------------------------------------------------------------
// ANIMATION VARIANTS
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

  // Fetch Agents
  const fetchAgents = async () => {
    try {
      setIsLoading(true);
      const res = await fetch('http://localhost:8000/api/agents/'); // Env var recommended
      if (!res.ok) throw new Error('Failed to fetch agents');
      const data = await res.json();

      // Transform data to match UI expectations if needed
      // Add "Create New" placeholder
      const loadedAgents = data.map((a: any) => ({
        ...a,
        systemStatus: 'ONLINE' // Mock status
      }));

      // Append the "Create New" card
      const createCard: Agent = {
        id: 'create-new',
        name: 'NEW SOUL',
        role: 'INITIALIZE',
        systemStatus: 'WAITING'
      };

      setAgents([...loadedAgents, createCard]);
    } catch (err) {
      console.error(err);
      // Fallback or empty state
      setAgents([{
          id: 'create-new',
          name: 'NEW SOUL',
          role: 'INITIALIZE',
          systemStatus: 'WAITING'
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAgents();
  }, []);

  // Carousel Parameters
  const radius = 350;
  const theta = agents.length > 0 ? 360 / agents.length : 0;

  const rotateCarousel = (direction: number) => {
    if (agents.length === 0) return;
    setActiveIndex((prev) => {
      let next = prev + direction;
      if (next < 0) next = agents.length - 1;
      if (next >= agents.length) next = 0;
      return next;
    });
  };

  const handleSelect = () => {
    const selected = agents[activeIndex];
    if (selected.id === 'create-new') {
      setIsModalOpen(true);
    } else if (onSelect) {
      onSelect(selected);
    }
  };

  const handleAgentCreated = () => {
    fetchAgents();
    // Optionally jump to the new agent (would be at index length-1 before the create card?)
    // For now just refresh list.
  };

  if (isLoading) return <div className="text-cyan-500 font-technical text-center mt-20">ESTABLISHING LINK...</div>;

  return (
    <>
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        exit="exit"
        className="flex flex-col items-center justify-center w-full h-[500px]"
      >

        {/* 3D SCENE */}
        <div className="perspective-scene" style={{ perspective: "1500px" }}>
          <motion.div
            className="carousel-axis"
            animate={{ rotateY: activeIndex * -theta }}
            transition={{ type: "spring", stiffness: 220, damping: 25, mass: 1 }}
            style={{ transformStyle: "preserve-3d", width: '260px', height: '380px', position: 'relative' }}
          >
            {agents.map((agent, index) => {
              const angle = index * theta;
              const isFocused = activeIndex === index;
              const isCreateCard = agent.id === 'create-new';

              return (
                <motion.div
                  key={agent.id}
                  variants={shardVariants}
                  className="agent-card-container"
                  style={{
                    transform: `rotateY(${angle}deg) translateZ(${radius}px)`,
                    rotateZ: isFocused ? "-2deg" : "-15deg",
                    opacity: isFocused ? 1 : 0.4,
                    scale: isFocused ? 1.05 : 0.9,
                  }}
                  transition={{ duration: 0.4 }}
                >
                  <motion.div
                    className={`agent-card-glass ${isFocused ? 'border-cyan-400' : 'border-slate-700'}`}
                    animate={{
                       filter: isFocused
                         ? "drop-shadow(0 0 20px #00D1FF) saturate(150%)"
                         : "drop-shadow(0 0 0px #141413) saturate(0%)",
                    }}
                    onClick={() => {
                       setActiveIndex(index);
                       if (isFocused) handleSelect();
                    }}
                  >
                    {isCreateCard ? (
                      // CREATE NEW CARD CONTENT
                      <div className="flex flex-col items-center justify-center h-full gap-4 text-cyan-400">
                        <div className="p-4 border border-dashed border-cyan-400/50 rounded-full">
                          <Plus size={48} />
                        </div>
                        <h2 className="font-monumental text-xl tracking-widest">FORGE NEW SOUL</h2>
                      </div>
                    ) : (
                      // AGENT CARD CONTENT
                      <>
                        {/* Avatar / Visual Placeholder */}
                        <div className="flex-1 flex items-center justify-center mb-4 relative overflow-hidden">
                           {agent.avatar_path ? (
                             <img src={agent.avatar_path} alt={agent.name} className="w-full h-full object-cover opacity-80" />
                           ) : (
                             // TYPOGRAPHIC FALLBACK
                             <div className="relative w-32 h-32 flex items-center justify-center">
                               <div className="absolute inset-0 border-2 border-cyan-400/30" style={{ clipPath: 'polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)' }} />
                               <span className="font-monumental text-6xl text-cyan-400 drop-shadow-[0_0_10px_rgba(0,209,255,0.8)]">
                                 {agent.name.charAt(0).toUpperCase()}
                               </span>
                             </div>
                           )}
                        </div>

                        <div className="flex flex-col gap-1">
                          <h2 className="agent-card-title text-3xl">{agent.name}</h2>
                          <p className="agent-card-role text-xs tracking-widest text-cyan-200/70">{agent.role}</p>
                        </div>

                        <div className="mt-4">
                          <div className="w-full h-[1px] bg-white/20 my-2" />
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
                  </motion.div>
                </motion.div>
              );
            })}
          </motion.div>
        </div>

        {/* CONTROLS */}
        <motion.div variants={shardVariants} className="mt-8 flex gap-8 z-50">
          <button
            onClick={() => rotateCarousel(-1)}
            className="kizuna-shard-btn-wrapper"
            style={{ padding: '2px', clipPath: 'polygon(10% 0, 100% 0, 100% 70%, 90% 100%, 0 100%, 0 30%)' }}
          >
            <div className="kizuna-shard-btn-inner" style={{ padding: '8px 24px' }}>
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
            className="kizuna-shard-btn-wrapper"
            style={{ padding: '2px', clipPath: 'polygon(10% 0, 100% 0, 100% 70%, 90% 100%, 0 100%, 0 30%)' }}
          >
            <div className="kizuna-shard-btn-inner" style={{ padding: '8px 24px' }}>
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
