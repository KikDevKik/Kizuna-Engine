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

export const SystemLogs: React.FC = () => {
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
    <div className="fixed bottom-4 left-4 z-0 pointer-events-none opacity-60">
      <div className="font-technical text-xs text-cyan-800 tracking-widest mb-1 border-b border-cyan-900/30 w-32">
        SYS.LOG //
      </div>
      <div className="flex flex-col-reverse h-32 w-64 overflow-hidden font-mono text-[10px] text-cyan-600/70">
        <AnimatePresence>
          {logs.map((log, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              className="whitespace-nowrap"
            >
              <span className="text-cyan-800 mr-2">{`>`}</span>
              {log}
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
};
