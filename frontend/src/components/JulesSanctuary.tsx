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
  const { videoRef, captureFrame, isReady: isCameraReady } = useVision(isOpen ? 'camera' : 'off');
  const [autoSync, setAutoSync] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [bpm, setBpm] = useState(80);

  // Bio-Link Transmit
  const handleBioTransmit = async () => {
    try {
        const token = localStorage.getItem("token") || "guest-token";
        const res = await fetch("http://localhost:8000/api/bio/submit", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify({ bpm })
        });
        if (res.ok) {
            addLog(`BIO: Pulse transmitted (${bpm} BPM)`);
        } else {
            addLog("BIO: Error transmitting");
        }
    } catch (e) {
        addLog(`BIO: Network Error`);
    }
  };

  // Log Helper
  const addLog = (msg: string) => {
    setLogs(prev => [`[${new Date().toLocaleTimeString()}] ${msg}`, ...prev].slice(0, 20));
  };

  // Auto-Sync Logic
  useEffect(() => {
    let interval: number;
    if (autoSync && isCameraReady && api.connected) {
      interval = window.setInterval(async () => {
        const frame = await captureFrame();
        if (frame) {
          api.sendImage(frame);
          addLog("AUTO-SYNC: Frame sent");
        }
      }, 2500);
    }
    return () => clearInterval(interval);
  }, [autoSync, isCameraReady, api.connected, captureFrame, api]);

  // Manual Capture
  const handleCapture = async () => {
    const frame = await captureFrame();
    if (frame) {
      api.sendImage(frame);
      addLog("MANUAL: Frame sent");
    } else {
      addLog("ERROR: Camera not ready");
    }
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
          <div className="w-[800px] h-[600px] bg-abyssal-black border border-electric-blue/50 shadow-2xl shadow-electric-blue/20 flex flex-col overflow-hidden relative shape-modal-shard">

            {/* Header */}
            <div className="h-12 bg-vintage-navy/20 border-b border-electric-blue/30 flex items-center justify-between px-6">
              <div className="flex items-center gap-2 font-technical text-electric-blue">
                <Terminal size={18} />
                <span>NEURAL LAB // JULES ACCESS</span>
              </div>
              <button onClick={onClose} className="text-electric-blue/60 hover:text-electric-blue">
                <X size={20} />
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 flex p-4 gap-4">

              {/* Left Column: Vision */}
              <div className="flex-1 flex flex-col gap-4">
                <div className="bg-abyssal-black border border-vintage-navy/50 relative aspect-video flex items-center justify-center overflow-hidden">
                  <video
                    ref={videoRef}
                    className="w-full h-full object-cover opacity-80"
                    playsInline
                    muted
                  />
                  {!isCameraReady && <div className="absolute text-vintage-navy font-technical">NO SIGNAL</div>}
                  {api.connected && isCameraReady && (
                      <div className="absolute top-2 right-2 flex gap-1">
                          <div className="w-2 h-2 bg-alert-red rounded-full animate-pulse" />
                          <span className="text-[10px] text-alert-red font-mono">LIVE</span>
                      </div>
                  )}
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={handleCapture}
                    disabled={!isCameraReady || !api.connected}
                    className="kizuna-shard-btn-wrapper flex-1"
                  >
                    <div className="kizuna-shard-btn-inner gap-2">
                      <Camera size={16} /> CAPTURE FRAME
                    </div>
                  </button>
                  <button
                    onClick={() => setAutoSync(!autoSync)}
                    className={`kizuna-shard-btn-wrapper flex-1 ${autoSync ? '!bg-alert-red' : ''}`}
                  >
                    <div className={`kizuna-shard-btn-inner gap-2 ${autoSync ? '!text-alert-red bg-alert-red/10' : ''}`}>
                      <Activity size={16} /> {autoSync ? 'STOP SYNC' : 'AUTO SYNC (2.5s)'}
                    </div>
                  </button>
                </div>
              </div>

              {/* Right Column: Metrics & Logs */}
              <div className="w-80 flex flex-col gap-4">

                {/* Status Box */}
                <div className="p-3 bg-vintage-navy/10 border border-electric-blue/30">
                  <h3 className="text-xs font-technical text-electric-blue/60 mb-2">SYSTEM STATUS</h3>
                  <div className="space-y-2 text-sm font-mono text-electric-blue">
                    <div className="flex justify-between">
                      <span>CONNECTION:</span>
                      <span className={api.connected ? "text-green-400" : "text-alert-red"}>
                        {api.status.toUpperCase()}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>AUDIO IN:</span>
                      <div className="w-20 h-4 bg-vintage-navy/50 overflow-hidden relative">
                         <span className="text-[10px] absolute inset-0 flex items-center justify-center">{api.isAiSpeaking ? "AI SPEAKING" : "LISTENING"}</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Bio-Link Simulation (Phase 3) */}
                <div className="p-3 bg-vintage-navy/10 border border-electric-blue/30">
                    <h3 className="text-xs font-technical text-electric-blue/60 mb-2">BIO-LINK SIMULATION</h3>
                    <div className="flex items-center gap-2 mb-2">
                        <Activity size={16} className="text-alert-red animate-pulse" />
                        <span className="text-sm font-mono text-electric-blue">{bpm} BPM</span>
                    </div>
                    <input
                        type="range" min="40" max="160" value={bpm}
                        onChange={(e) => setBpm(Number(e.target.value))}
                        className="w-full h-2 bg-vintage-navy rounded-lg appearance-none cursor-pointer mb-2 accent-electric-blue"
                    />
                    <button onClick={handleBioTransmit} className="w-full bg-electric-blue/20 hover:bg-electric-blue/40 text-electric-blue font-technical py-1 text-xs border border-electric-blue/50">
                        INJECT SIGNAL
                    </button>
                </div>

                {/* Logs */}
                <div className="flex-1 bg-abyssal-black/50 border border-vintage-navy/50 p-2 font-mono text-[10px] text-electric-blue overflow-y-auto">
                   {logs.map((log, i) => (
                       <div key={i} className="mb-1 border-b border-vintage-navy/20 pb-1">{log}</div>
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
