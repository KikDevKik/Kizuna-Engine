import React, { useState } from 'react';
import { motion } from 'framer-motion';
import '../KizunaHUD.css';

interface Agent {
  id: string;
  codename: string;
  role: string;
  systemStatus: string;
}

const AGENTS: Agent[] = [
  { id: '1', codename: 'KIZUNA-01', role: 'CORE INTELLIGENCE', systemStatus: 'ONLINE' },
  { id: '2', codename: 'AEGIS-X', role: 'TACTICAL SUPPORT', systemStatus: 'OFFLINE' },
  { id: '3', codename: 'ORACLE-V', role: 'DATA ANALYTICS', systemStatus: 'MAINTENANCE' },
  { id: '4', codename: 'SERAPH-9', role: 'NETWORK SECURITY', systemStatus: 'UNKNOWN' },
  { id: '5', codename: 'VANGUARD', role: 'FIELD OPS', systemStatus: 'OFFLINE' },
];

interface AgentRosterProps {
  onSelect?: (agent: Agent) => void;
}

// ------------------------------------------------------------------
// SHATTER TRANSITION VARIANTS (Proposal 2)
// ------------------------------------------------------------------
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.06, // Fast cascade
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
    rotateZ: 10, // Chaotic entry
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
      stiffness: 200, // Snap effect
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
  const [activeIndex, setActiveIndex] = useState(0);

  // Carousel Parameters
  const radius = 350; // Distance from center (Z-axis)
  const theta = 360 / AGENTS.length; // Degrees per agent

  const rotateCarousel = (direction: number) => {
    setActiveIndex((prev) => {
      let next = prev + direction;
      // Wrap around logic (optional, or clamp)
      if (next < 0) next = AGENTS.length - 1;
      if (next >= AGENTS.length) next = 0;
      return next;
    });
  };

  const handleSelect = () => {
    if (onSelect) {
      onSelect(AGENTS[activeIndex]);
    }
  };

  return (
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
          {AGENTS.map((agent, index) => {
            const angle = index * theta;
            const isFocused = activeIndex === index;

            return (
              <motion.div
                key={agent.id}
                variants={shardVariants} // Apply Shatter Effect
                className="agent-card-container"
                style={{
                  transform: `rotateY(${angle}deg) translateZ(${radius}px)`,
                  // Tilt slightly when not focused (Base offset)
                  // Note: variants animate rotateZ/X during entry, but style overrides it after?
                  // Framer motion merges style and animate. To allow variants to control entry,
                  // we should move the static tilts to 'animate' or conditional classes if possible.
                  // However, for simplicity in 3D carousel, we keep the structural transforms here.
                  // The variant's rotateZ will compound or override during transition.
                  rotateZ: isFocused ? "-2deg" : "-15deg",
                  opacity: isFocused ? 1 : 0.4,
                  // Scale down distant items
                  scale: isFocused ? 1.05 : 0.9,
                }}
                transition={{ duration: 0.4 }}
              >
                <motion.div
                  className={`agent-card-glass ${isFocused ? 'border-cyan-400' : 'border-slate-700'}`}
                  // Move focus animation to inner element to avoid conflict with entrance filter blur
                  animate={{
                     filter: isFocused
                       ? "drop-shadow(0 0 20px #00D1FF) saturate(150%)"
                       : "drop-shadow(0 0 0px #141413) saturate(0%)",
                  }}
                  onClick={() => {
                     setActiveIndex(index);
                     handleSelect();
                  }}
                >
                  <div className="flex flex-col gap-2">
                    <h2 className="agent-card-title">{agent.codename}</h2>
                    <p className="agent-card-role text-xs tracking-widest">{agent.role}</p>
                  </div>

                  <div className="mt-auto">
                    <div className="w-full h-[1px] bg-white/20 my-2" />
                    <div className="flex justify-between items-end">
                       <span className="font-technical text-2xl text-cyan-300">
                          {agent.systemStatus === 'ONLINE' ? '88.4%' : '0.0%'}
                       </span>
                       <span className="font-technical text-xs text-white/50">
                          {agent.systemStatus}
                       </span>
                    </div>
                  </div>
                </motion.div>
              </motion.div>
            );
          })}
        </motion.div>
      </div>

      {/* CONTROLS (Optional) */}
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
           <span className="kizuna-shard-btn-inner">INITIATE LINK</span>
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
  );
};
