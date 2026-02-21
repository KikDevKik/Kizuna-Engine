import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import '../KizunaHUD.css';

const MOCK_LOGS = [
  "INIT KIZUNA_ENGINE.CORE",
  "LOADING NEURAL WEIGHTS...",
  "ESTABLISHING SECURE WS HANDSHAKE",
  "AUDIO BUFFER: 3200 BYTES [OK]",
  "GEMINI-2.5-FLASH-NATIVE: READY",
  "VAD SENSITIVITY: 0.85",
  "ECHO CANCELLATION: ACTIVE",
];

// Optimization: Prevent re-renders when parent re-renders. Component has internal state but no props.
export const SystemLogs = React.memo(() => {
  const [logs, setLogs] = useState<string[]>([]);

  useEffect(() => {
    let i = 0;
    const interval = setInterval(() => {
      if (i < MOCK_LOGS.length) {
        setLogs(prev => [...prev, MOCK_LOGS[i]]);
        i++;
      } else {
        clearInterval(interval);
      }
    }, 800);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="fixed bottom-4 left-4 z-0 pointer-events-none opacity-80">
      <div className="font-log font-technical text-xs text-electric-blue tracking-widest mb-1 border-b border-electric-blue/30 w-32 drop-shadow-[0_0_5px_rgba(0,209,255,0.5)]">
        SYS.LOG //
      </div>
      <div className="flex flex-col-reverse h-32 w-64 overflow-hidden font-mono text-[10px] text-electric-blue/70">
        <AnimatePresence>
          {logs.map((log, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              className="whitespace-nowrap"
            >
              <span className="text-electric-blue mr-2">{`>`}</span>
              {log}
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
});
