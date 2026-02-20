import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { UseLiveAPI } from '../hooks/useLiveAPI';
import { useVision } from '../hooks/useVision';
import { Terminal, Camera, Activity, X } from 'lucide-react';
import '../KizunaHUD.css';

interface JulesSanctuaryProps {
  isOpen: boolean;
  onClose: () => void;
  api: UseLiveAPI;
}

export const JulesSanctuary: React.FC<JulesSanctuaryProps> = ({ isOpen, onClose, api }) => {
  const { videoRef, captureFrame, isCameraReady } = useVision(isOpen);
  const [autoSync, setAutoSync] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);

  // Auto-Sync Logic
  useEffect(() => {
    let interval: number;
    if (autoSync && isCameraReady && api.connected) {
      interval = window.setInterval(() => {
        const frame = captureFrame();
        if (frame) {
          api.sendImage(frame);
          addLog("AUTO-SYNC: Frame sent");
        }
      }, 2000);
    }
    return () => clearInterval(interval);
  }, [autoSync, isCameraReady, api.connected, captureFrame, api]);

  // Manual Capture
  const handleCapture = () => {
    const frame = captureFrame();
    if (frame) {
      api.sendImage(frame);
      addLog("MANUAL: Frame sent");
    } else {
      addLog("ERROR: Camera not ready");
    }
  };

  // Log Helper
  const addLog = (msg: string) => {
    setLogs(prev => [`[${new Date().toLocaleTimeString()}] ${msg}`, ...prev].slice(0, 20));
  };

  // Monitor AI Messages
  useEffect(() => {
      if (api.lastAiMessage) {
          addLog(`AI: ${api.lastAiMessage.substring(0, 50)}...`);
      }
  }, [api.lastAiMessage]);

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/80 backdrop-blur-sm"
        >
          <div className="w-[800px] h-[600px] bg-slate-900 border border-cyan-500/50 shadow-2xl shadow-cyan-500/20 flex flex-col overflow-hidden relative"
               style={{ clipPath: "polygon(2% 0, 100% 0, 100% 95%, 98% 100%, 0 100%, 0 5%)" }}>

            {/* Header */}
            <div className="h-12 bg-cyan-900/20 border-b border-cyan-500/30 flex items-center justify-between px-6">
              <div className="flex items-center gap-2 font-technical text-cyan-400">
                <Terminal size={18} />
                <span>NEURAL LAB // JULES ACCESS</span>
              </div>
              <button onClick={onClose} className="text-cyan-600 hover:text-cyan-300">
                <X size={20} />
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 flex p-4 gap-4">

              {/* Left Column: Vision */}
              <div className="flex-1 flex flex-col gap-4">
                <div className="bg-black border border-cyan-900/50 relative aspect-video flex items-center justify-center overflow-hidden">
                  <video
                    ref={videoRef}
                    className="w-full h-full object-cover opacity-80"
                    playsInline
                    muted
                  />
                  {!isCameraReady && <div className="absolute text-cyan-800 font-technical">NO SIGNAL</div>}
                  {api.connected && isCameraReady && (
                      <div className="absolute top-2 right-2 flex gap-1">
                          <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                          <span className="text-[10px] text-red-500 font-mono">LIVE</span>
                      </div>
                  )}
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={handleCapture}
                    disabled={!isCameraReady || !api.connected}
                    className="flex-1 bg-cyan-900/30 border border-cyan-500/50 text-cyan-400 py-2 font-technical text-sm hover:bg-cyan-500/20 disabled:opacity-50 transition-colors flex items-center justify-center gap-2"
                  >
                    <Camera size={16} /> CAPTURE FRAME
                  </button>
                  <button
                    onClick={() => setAutoSync(!autoSync)}
                    className={`flex-1 border py-2 font-technical text-sm transition-colors flex items-center justify-center gap-2 ${autoSync ? 'bg-red-500/20 border-red-500 text-red-400' : 'bg-cyan-900/30 border-cyan-500/50 text-cyan-400 hover:bg-cyan-500/20'}`}
                  >
                    <Activity size={16} /> {autoSync ? 'STOP SYNC' : 'AUTO SYNC (2s)'}
                  </button>
                </div>
              </div>

              {/* Right Column: Metrics & Logs */}
              <div className="w-80 flex flex-col gap-4">

                {/* Status Box */}
                <div className="p-3 bg-cyan-900/10 border border-cyan-500/30">
                  <h3 className="text-xs font-technical text-cyan-600 mb-2">SYSTEM STATUS</h3>
                  <div className="space-y-2 text-sm font-mono text-cyan-300">
                    <div className="flex justify-between">
                      <span>CONNECTION:</span>
                      <span className={api.connected ? "text-green-400" : "text-red-400"}>
                        {api.status.toUpperCase()}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>AUDIO IN:</span>
                      <div className="w-20 h-4 bg-cyan-900/50 overflow-hidden relative">
                         <span className="text-[10px] absolute inset-0 flex items-center justify-center">{api.isAiSpeaking ? "AI SPEAKING" : "LISTENING"}</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Logs */}
                <div className="flex-1 bg-black/50 border border-cyan-900/50 p-2 font-mono text-[10px] text-cyan-500 overflow-y-auto">
                   {logs.map((log, i) => (
                       <div key={i} className="mb-1 border-b border-cyan-900/20 pb-1">{log}</div>
                   ))}
                </div>

              </div>

            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};
