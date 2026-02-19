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
    <div className="flex flex-col items-center justify-center w-full h-[500px]">

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
                className="agent-card-container"
                style={{
                  transform: `rotateY(${angle}deg) translateZ(${radius}px)`,
                  // Tilt slightly when not focused
                  rotateZ: isFocused ? "-2deg" : "-15deg",
                  opacity: isFocused ? 1 : 0.4,
                  // Scale down distant items
                  scale: isFocused ? 1.05 : 0.9,
                }}
                animate={{
                   filter: isFocused
                     ? "drop-shadow(0 0 20px #00D1FF) saturate(150%)"
                     : "drop-shadow(0 0 0px #141413) saturate(0%)",
                }}
                transition={{ duration: 0.4 }}
              >
                <div
                  className={`agent-card-glass ${isFocused ? 'border-cyan-400' : 'border-slate-700'}`}
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
                </div>
              </motion.div>
            );
          })}
        </motion.div>
      </div>

      {/* CONTROLS (Optional) */}
      <div className="mt-8 flex gap-8 z-50">
        <button
          onClick={() => rotateCarousel(-1)}
          className="px-6 py-2 bg-slate-900 border border-cyan-500/30 text-cyan-400 font-technical hover:bg-cyan-900/40 transition-colors skew-x-[-15deg]"
        >
          <span className="block skew-x-[15deg]">&lt; PREV</span>
        </button>
        <button
          onClick={handleSelect}
          className="px-8 py-2 bg-cyan-600 border border-cyan-400 text-black font-monumental hover:bg-cyan-400 transition-colors shadow-[0_0_15px_rgba(0,209,255,0.4)] skew-x-[-15deg]"
        >
           <span className="block skew-x-[15deg]">INITIATE LINK</span>
        </button>
        <button
          onClick={() => rotateCarousel(1)}
          className="px-6 py-2 bg-slate-900 border border-cyan-500/30 text-cyan-400 font-technical hover:bg-cyan-900/40 transition-colors skew-x-[-15deg]"
        >
          <span className="block skew-x-[15deg]">NEXT &gt;</span>
        </button>
      </div>
    </div>
  );
};
