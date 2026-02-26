import { useState, useCallback, useEffect } from 'react';
import { useLiveAPI } from './hooks/useLiveAPI';
import { Layout } from './components/Layout';
import { KizunaCore } from './components/KizunaCore';
import { AgentRoster } from './components/AgentRoster';
import { DistrictZero } from './components/DistrictZero';
import { VisionPanel } from './components/VisionPanel';
import { EpistemicPanel } from './components/EpistemicPanel';
import { SystemLogs } from './components/SystemLogs';
import { JulesSanctuary } from './components/JulesSanctuary';
import { ConfigurationPanel } from './components/ConfigurationPanel';
import { ConnectionSeveredModal } from './components/ConnectionSeveredModal';
import { RitualProvider } from './contexts/RitualContext';
import { RosterProvider } from './contexts/RosterContext';
import { AnimatePresence, motion } from 'framer-motion';
import { Power, Settings } from 'lucide-react';
import './KizunaHUD.css';

function App() {
  const liveApi = useLiveAPI();
  const {
    connected,
    status,
    volumeRef,
    isAiSpeaking,
    isSevered,
    severanceReason,
    connect,
    disconnect,
    sendImage,
    addSystemAudio,
    removeSystemAudio
  } = liveApi;

  const [viewMode, setViewMode] = useState<'core' | 'roster' | 'district'>('roster'); // Default to Roster to force selection
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);
  const [isSanctuaryOpen, setIsSanctuaryOpen] = useState(false);

  // Configuration State
  const [isConfigOpen, setIsConfigOpen] = useState(false);
  const [showScanlines, setShowScanlines] = useState(() => {
    return localStorage.getItem('kizuna_scanlines') === 'true';
  });

  // Derived state for Law 4 logic (passed to Core)
  const isListening = connected && !isAiSpeaking;

  // Persist Scanlines
  useEffect(() => {
    localStorage.setItem('kizuna_scanlines', String(showScanlines));
  }, [showScanlines]);

  const handleAgentSelect = useCallback((agentId: string) => {
    console.log(`Agent Selected: ${agentId}`);
    setSelectedAgentId(agentId);
    setViewMode('core');
  }, []);

  const handleAgentForged = useCallback((agentId: string) => {
    console.log(`Agent Forged: ${agentId}`);
    setSelectedAgentId(agentId);
    // Stay in District mode to see the Mock Session UI
  }, []);

  const handleToggleConnection = () => {
    if (connected) {
      disconnect();
    } else {
      if (selectedAgentId) {
        connect(selectedAgentId);
      } else {
        // Fallback: If no agent selected (shouldn't happen in Core view if we force Roster first),
        // maybe switch back to roster?
        console.warn("No agent selected. Switching to Roster.");
        setViewMode('roster');
      }
    }
  };

  const handleReboot = () => {
    if (selectedAgentId) {
      connect(selectedAgentId);
    } else {
      console.warn("Reboot requested but no agent selected.");
      setViewMode('roster');
    }
  };

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
        if (event.ctrlKey && event.shiftKey && (event.key === 'P' || event.key === 'p')) {
            event.preventDefault();
            setIsSanctuaryOpen(prev => !prev);
        }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <RitualProvider>
    <RosterProvider>
    <Layout showScanlines={showScanlines}>
      {/* HEADER / NAV */}
      <header className="fixed top-0 left-0 w-full p-6 flex justify-between items-start z-50 pointer-events-none">
        <div className="flex flex-col pointer-events-auto">
          <h1 className="font-monumental text-5xl skew-x-[-10deg] tracking-tighter leading-none">
            KIZUNA<span className="text-electric-blue">ENGINE</span>
          </h1>
          <div className="h-1 w-32 bg-electric-blue skew-x-[-10deg] mt-1" />
          <div className="font-technical text-xs mt-1 opacity-70 text-electric-blue">
            MULTIMODAL INTERFACE V4.0 // AGENT: {selectedAgentId || 'NONE'}
          </div>
        </div>

        <div className="flex gap-4 pointer-events-auto items-center">
          {/* Config Button */}
          <button
            onClick={() => setIsConfigOpen(true)}
            className="text-electric-blue/60 hover:text-electric-blue transition-colors mr-4"
          >
             <Settings size={24} />
          </button>

          <button
            onClick={() => setViewMode('core')}
            className={`kizuna-shard-nav-btn ${viewMode === 'core' ? 'active' : ''}`}
          >
            <div className="kizuna-shard-nav-inner">
              CORE VIEW
            </div>
          </button>
          <button
            onClick={() => setViewMode('district')}
            className={`kizuna-shard-nav-btn ${viewMode === 'district' ? 'active' : ''}`}
          >
            <div className="kizuna-shard-nav-inner">
              DISTRICT ZERO
            </div>
          </button>
          <button
            onClick={() => setViewMode('roster')}
            className={`kizuna-shard-nav-btn ${viewMode === 'roster' ? 'active' : ''}`}
          >
            <div className="kizuna-shard-nav-inner">
              AGENT ROSTER
            </div>
          </button>
        </div>
      </header>

      {/* MAIN CONTENT AREA */}
      <main className="relative w-full h-full flex items-center justify-center z-10">
        <AnimatePresence mode="wait">
          {viewMode === 'core' ? (
            <motion.div
              key="core-view"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 1.1, filter: 'blur(10px)' }}
              transition={{ duration: 0.5 }}
              className="flex flex-col items-center justify-center"
            >
              <KizunaCore
                volumeRef={volumeRef}
                isListening={isListening}
                isAiSpeaking={isAiSpeaking}
                status={status}
              />

              {/* Connection Toggle (Core View) */}
              <div className="mt-12 pointer-events-auto">
                <button
                  onClick={handleToggleConnection}
                  disabled={status === 'connecting'}
                  className={`kizuna-shard-btn-wrapper ${!selectedAgentId ? 'opacity-50 grayscale' : ''}`}
                >
                  <span className="kizuna-shard-btn-inner">
                    {status === 'connecting' ? (
                      'SYNCING...'
                    ) : connected ? (
                      <>TERMINATE <Power size={20} /></>
                    ) : (
                      <>{selectedAgentId ? 'INITIATE LINK' : 'SELECT AGENT'} <Power size={20} /></>
                    )}
                  </span>
                </button>
              </div>
            </motion.div>
          ) : viewMode === 'district' ? (
             <motion.div
              key="district-view"
              initial={{ opacity: 0, x: 50 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -50, filter: 'blur(10px)' }}
              transition={{ duration: 0.5 }}
              className="w-full h-full flex items-center justify-center pointer-events-auto"
            >
              <DistrictZero
                connect={connect}
                disconnect={disconnect}
                onAgentForged={handleAgentForged}
              />
            </motion.div>
          ) : (
            <motion.div
              key="roster-view"
              initial={{ opacity: 0, y: 50 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -50, filter: 'blur(10px)' }}
              transition={{ duration: 0.5 }}
              className="w-full h-full flex items-center justify-center pointer-events-auto"
            >
              <AgentRoster onSelect={handleAgentSelect} />
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      {/* PERIPHERAL PANELS */}
      <VisionPanel
        connected={connected}
        sendImage={sendImage}
        addSystemAudio={addSystemAudio}
        removeSystemAudio={removeSystemAudio}
      />
      <EpistemicPanel />
      <SystemLogs />

      <JulesSanctuary
        isOpen={isSanctuaryOpen}
        onClose={() => setIsSanctuaryOpen(false)}
        api={liveApi}
      />

      <ConfigurationPanel
        isOpen={isConfigOpen}
        onClose={() => setIsConfigOpen(false)}
        showScanlines={showScanlines}
        setShowScanlines={setShowScanlines}
      />

      {/* CRITICAL ALERTS */}
      <AnimatePresence>
        {isSevered && (
            <motion.div
            key="modal-severed"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.5 }}
            className="fixed inset-0 z-[100] pointer-events-auto"
            >
            <ConnectionSeveredModal
                reason={severanceReason}
                onReboot={handleReboot}
            />
            </motion.div>
        )}
      </AnimatePresence>

      {/* FOOTER STATUS */}
      <footer className="fixed bottom-0 left-0 w-full p-4 flex justify-between items-end z-40 pointer-events-none opacity-80 text-[10px] font-technical text-vintage-navy">
        <div>
           MEMORY_USAGE: 64TB // LATENCY: 12ms
        </div>
        <div>
           SECURE_CHANNEL: {connected ? 'ENCRYPTED' : 'OPEN'} // TARGET: {selectedAgentId || 'NULL'}
        </div>
      </footer>
    </Layout>
    </RosterProvider>
    </RitualProvider>
  );
}

export default App;
