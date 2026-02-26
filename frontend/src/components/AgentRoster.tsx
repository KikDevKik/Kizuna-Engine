import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Trash2 } from 'lucide-react';
import { SoulForgeModal } from './SoulForgeModal';
import { DeleteAgentModal } from './DeleteAgentModal';
import { useRoster, type Agent } from '../contexts/RosterContext';
import '../KizunaHUD.css';

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
    y: 50,
    opacity: 0,
    scale: 0.9
  },
  visible: {
    y: 0,
    opacity: 1,
    scale: 1,
    transition: {
      type: "spring" as const,
      stiffness: 200,
      damping: 20,
      mass: 0.8
    }
  },
  exit: {
    y: 20,
    opacity: 0,
    transition: { duration: 0.2 }
  }
};

export const AgentRoster: React.FC<AgentRosterProps> = ({ onSelect }) => {
  const { myAgents, isLoading, error, refreshAgents } = useRoster();
  const [activeIndex, setActiveIndex] = useState(0);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [agentToDelete, setAgentToDelete] = useState<Agent | null>(null);
  const [localError, setLocalError] = useState<string | null>(null);

  // Compute display agents (My Agents + Create New)
  const agents = useMemo(() => {
    const createCard: Agent = {
      id: 'create-new',
      name: 'NEW SOUL',
      role: 'INITIALIZE',
      systemStatus: 'WAITING'
    };
    return [...myAgents, createCard];
  }, [myAgents]);

  // Adjust activeIndex if out of bounds (e.g. after deletion)
  useEffect(() => {
    if (activeIndex >= agents.length) {
        setActiveIndex(Math.max(0, agents.length - 1));
    }
  }, [agents.length, activeIndex]);

  // ------------------------------------------------------------------
  // AUTONOMOUS AGENT LOGIC (Option B)
  // ------------------------------------------------------------------

  // Strict Linear Navigation (No Wrapping)
  const rotateCarousel = useCallback((direction: number) => {
    if (agents.length === 0) return;
    setActiveIndex((prev) => {
      const next = prev + direction;
      // Clamp values
      if (next < 0) return 0;
      if (next >= agents.length) return agents.length - 1;
      return next;
    });
  }, [agents.length]);

  // Keyboard Navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore if typing in an input or textarea
      const target = e.target as HTMLElement;
      if (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.isContentEditable
      ) {
        return;
      }

      if (isModalOpen || agentToDelete || agents.length === 0) return;

      if (e.key === 'ArrowLeft') {
        rotateCarousel(-1);
      } else if (e.key === 'ArrowRight') {
        rotateCarousel(1);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isModalOpen, agentToDelete, rotateCarousel, agents.length]);

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
    await refreshAgents();
  };

  const handleDeleteConfirm = async () => {
    if (!agentToDelete) return;
    try {
      const res = await fetch(`http://localhost:8000/api/agents/${agentToDelete.id}`, {
        method: 'DELETE',
      });
      if (!res.ok) {
        throw new Error('Failed to delete agent');
      }
      setAgentToDelete(null);
      await refreshAgents();
      // Reset to beginning is handled by effect, but let's be safe
      setActiveIndex(0);
    } catch (err: any) {
      console.error("Delete error:", err);
      setLocalError(err.message || "DELETE_FAILED");
    }
  };

  // ------------------------------------------------------------------
  // REVOLVER CYLINDER LOGIC (TRIGONOMETRIC)
  // ------------------------------------------------------------------
  const CYLINDER_RADIUS = 500;
  const CARD_ANGLE = 25; // Degrees per card

  const getCardStyle = (index: number) => {
    const offsetIndex = index - activeIndex;
    const angleDeg = offsetIndex * CARD_ANGLE;
    const angleRad = (angleDeg * Math.PI) / 180;

    const x = CYLINDER_RADIUS * Math.sin(angleRad);
    const z = CYLINDER_RADIUS * Math.cos(angleRad) - CYLINDER_RADIUS; // At angle=0, z=0.

    const rotateY = angleDeg;

    // Visibility Culling & Fading
    const absOffset = Math.abs(offsetIndex);
    const opacity = 1 - (absOffset * 0.25); // Fade out distant cards
    const scale = absOffset === 0 ? 1.1 : 0.9;
    const zIndex = 100 - absOffset;

    return {
      x,
      z,
      rotateY,
      rotateZ: absOffset === 0 ? "-2deg" : "-5deg", // Aggressive tilt
      scale,
      opacity: Math.max(opacity, 0),
      zIndex,
      filter: absOffset === 0
        ? "blur(0px) brightness(1.2) drop-shadow(0 0 30px rgba(0,209,255,0.3))"
        : `blur(${absOffset * 2}px) brightness(0.5)`,
      transition: {
        type: "spring" as const,
        stiffness: 200,
        damping: 30,
        mass: 1
      }
    };
  };

  if (isLoading && agents.length <= 1) { // 1 because createCard is always there
      return <div className="text-electric-blue font-technical text-center mt-20 animate-pulse">ESTABLISHING LINK...</div>;
  }

  const isFirst = activeIndex === 0;
  const isLast = activeIndex === agents.length - 1;

  // Accessibility: Announce current selection
  const currentAgent = agents[activeIndex];
  const a11yAnnouncement = currentAgent
    ? `Selected: ${currentAgent.name}, ${currentAgent.role}`
    : 'Agent Carousel';

  const displayError = error || localError;

  return (
    <>
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        exit="exit"
        role="region"
        aria-label="Agent Selection Carousel"
        className="flex flex-col items-center justify-center w-full h-[700px] relative overflow-hidden"
      >
        {/* Screen Reader Live Region */}
        <div
          aria-live="polite"
          aria-atomic="true"
          style={{
            position: 'absolute',
            width: 1,
            height: 1,
            padding: 0,
            margin: -1,
            overflow: 'hidden',
            clip: 'rect(0, 0, 0, 0)',
            whiteSpace: 'nowrap',
            border: 0
          }}
        >
          {a11yAnnouncement}
        </div>

        {displayError && (
            <div className="absolute top-4 text-alert-red font-technical text-sm bg-abyssal-black/90 p-4 border border-alert-red z-[300] shadow-[0_0_20px_rgba(255,51,102,0.4)] backdrop-blur-md tracking-widest uppercase">
                {'>'} CONNECTION_ERROR: {displayError}
            </div>
        )}

        {/* 3D STAGE - Single Relative Container */}
        <div
          className="w-full h-[450px] flex items-center justify-center relative"
          style={{ perspective: "1000px" }} // Perspective on container
        >
            <AnimatePresence>
            {agents.map((agent, index) => {
              const isCreateCard = agent.id === 'create-new';
              const isFocused = activeIndex === index;

              // Optimization: Only render visible arc
              if (Math.abs(index - activeIndex) > 4) return null;

              return (
                <motion.div
                  key={agent.id}
                  layoutId={`agent-card-${agent.id}`}
                  className="absolute w-[260px] h-[380px]" // Fixed size card
                  initial={false}
                  animate={getCardStyle(index)}
                  style={{
                    transformStyle: "preserve-3d",
                    cursor: "pointer",
                    // Fix for backface visibility flickering
                    backfaceVisibility: "hidden"
                  }}
                  onClick={() => setActiveIndex(index)}
                >
                  {/* CARD CONTENT */}
                  <div
                    className={`agent-card-glass w-full h-full ${isFocused ? 'border-electric-blue' : 'border-vintage-navy'}`}
                  >
                    {/* DELETE BUTTON (Only on Focused & Real Agents) */}
                    {isFocused && !isCreateCard && (
                      <div className="absolute top-2 right-2 z-50">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setAgentToDelete(agent);
                          }}
                          className="p-2 text-electric-blue hover:text-alert-red transition-colors opacity-50 hover:opacity-100"
                          title="Terminate Soul"
                          aria-label={`Delete agent ${agent.name}`}
                        >
                          <Trash2 size={20} />
                        </button>
                      </div>
                    )}

                    {isCreateCard ? (
                      // CREATE NEW CARD CONTENT
                      <div className="flex flex-col items-center justify-center h-full gap-4 text-electric-blue">
                        <div className="shape-shard-create p-6 bg-electric-blue/10 flex items-center justify-center hover:bg-electric-blue/20 transition-colors duration-300">
                          {/* UI HOTFIX: Constrained Container for Void Portal */}
                          <div className="w-16 h-16 relative flex items-center justify-center overflow-hidden shrink-0">
                            <div className="ritual-void-portal">
                              <div className="void-ring" />
                              <div className="void-ring" />
                              <div className="void-ring" />
                              <div className="void-core" />
                            </div>
                          </div>
                        </div>
                        <h2 className="font-monumental text-xl tracking-widest text-center">FORGE NEW SOUL</h2>
                      </div>
                    ) : (
                      // AGENT CARD CONTENT
                      <>
                        {/* Avatar / Visual Placeholder */}
                        <div className="shape-shard-avatar flex-1 flex items-center justify-center mb-4 relative overflow-hidden bg-abyssal-black/20">
                           {agent.avatar_path ? (
                             <img src={agent.avatar_path} alt={agent.name} className="w-full h-full object-cover opacity-90" />
                           ) : (
                             // TYPOGRAPHIC FALLBACK
                             <div className="relative w-full h-full flex items-center justify-center">
                               <div className="absolute inset-0 border border-electric-blue/10" />
                               <span className="font-monumental text-6xl text-electric-blue/80 drop-shadow-[0_0_15px_rgba(0,209,255,0.5)]">
                                 {agent.name.charAt(0).toUpperCase()}
                               </span>
                             </div>
                           )}
                        </div>

                        <div className="flex flex-col gap-1">
                          <h2 className="agent-card-title text-3xl truncate">{agent.name}</h2>
                          <p className="agent-card-role text-xs tracking-widest text-electric-blue/70 uppercase">{agent.role}</p>
                        </div>

                        <div className="mt-4">
                          <div className="w-full h-[1px] bg-electric-blue/30 my-2" />
                          <div className="flex justify-between items-end">
                             <span className="font-technical text-2xl text-electric-blue">
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
        <motion.div variants={shardVariants} className="mt-12 flex gap-8 z-[200] relative">
          <button
            onClick={() => rotateCarousel(-1)}
            disabled={isFirst}
            className={`kizuna-shard-btn-wrapper transition-opacity duration-300 ${isFirst ? 'opacity-50 cursor-not-allowed' : 'opacity-100'}`}
            aria-label="Previous Agent"
          >
            <div className="kizuna-shard-btn-inner">
               &lt; PREV
            </div>
          </button>

          <button
            onClick={handleSelect}
            className="kizuna-shard-btn-wrapper"
            aria-label={agents[activeIndex]?.id === 'create-new' ? 'Create new agent' : `Initiate link with ${agents[activeIndex]?.name}`}
          >
             <span className="kizuna-shard-btn-inner">
               {agents[activeIndex]?.id === 'create-new' ? 'INITIALIZE' : 'INITIATE LINK'}
             </span>
          </button>

          <button
            onClick={() => rotateCarousel(1)}
            disabled={isLast}
            className={`kizuna-shard-btn-wrapper transition-opacity duration-300 ${isLast ? 'opacity-50 cursor-not-allowed' : 'opacity-100'}`}
            aria-label="Next Agent"
          >
            <div className="kizuna-shard-btn-inner">
              NEXT &gt;
            </div>
          </button>

          {/* Keyboard Hint */}
          <div className="absolute top-full mt-4 left-1/2 -translate-x-1/2 text-electric-blue/30 text-[10px] font-technical tracking-widest flex gap-4 pointer-events-none select-none w-max">
            <span>[ KEYBOARD: ← / → ]</span>
          </div>
        </motion.div>
      </motion.div>

      <SoulForgeModal
        isOpen={isModalOpen}
        onClose={() => {
            setIsModalOpen(false);
            refreshAgents();
        }}
        onCreated={handleAgentCreated}
      />

      <DeleteAgentModal
        isOpen={!!agentToDelete}
        onClose={() => setAgentToDelete(null)}
        onConfirm={handleDeleteConfirm}
        agentName={agentToDelete?.name || ''}
      />
    </>
  );
};
