import { useState, useEffect } from 'react';
import { useLiveAPI } from './hooks/useLiveAPI';
import { Layout } from './components/Layout';
import { KizunaCore } from './components/KizunaCore';
import { AgentRoster } from './components/AgentRoster';
import { VisionPanel } from './components/VisionPanel'; // Assuming VisionPanel exists in components/VisionPanel.tsx
import { EpistemicPanel } from './components/EpistemicPanel'; // Assuming EpistemicPanel exists in components/EpistemicPanel.tsx
import { SystemLogs } from './components/SystemLogs';
import { JulesSanctuary } from './components/JulesSanctuary';
import { AnimatePresence, motion } from 'framer-motion';
import { Power } from 'lucide-react';
import './KizunaHUD.css';

function App() {
  const api = useLiveAPI();
  const { connected, status, volumeRef, isAiSpeaking, connect, disconnect } = api;
  const [viewMode, setViewMode] = useState<'core' | 'roster'>('core');
  const [isSanctuaryOpen, setIsSanctuaryOpen] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key.toLowerCase() === 'j') {
        e.preventDefault();
        setIsSanctuaryOpen(prev => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Derived state for Law 4 logic (passed to Core)
  const isListening = connected && !isAiSpeaking;

  const handleToggleConnection = () => {
    if (connected) disconnect();
    else connect();
  };

  return (
    <Layout>
      {/* HEADER / NAV */}
      <header className="fixed top-0 left-0 w-full p-6 flex justify-between items-start z-50 pointer-events-none">
        <div className="flex flex-col pointer-events-auto">
          <h1 className="font-monumental text-5xl skew-x-[-10deg] tracking-tighter leading-none">
            KIZUNA<span className="text-cyan-400">ENGINE</span>
          </h1>
          <div className="h-1 w-32 bg-cyan-500 skew-x-[-10deg] mt-1" />
          <div className="font-technical text-xs mt-1 opacity-70">
            MULTIMODAL INTERFACE V4.0
          </div>
        </div>

        <div className="flex gap-4 pointer-events-auto">
          <button
            onClick={() => setViewMode('core')}
            className={`px-4 py-1 font-technical border skew-x-[-10deg] transition-all ${
              viewMode === 'core' ? 'bg-cyan-500 text-black border-cyan-400' : 'bg-transparent text-cyan-400 border-cyan-900/50'
            }`}
          >
            CORE VIEW
          </button>
          <button
            onClick={() => setViewMode('roster')}
            className={`px-4 py-1 font-technical border skew-x-[-10deg] transition-all ${
              viewMode === 'roster' ? 'bg-cyan-500 text-black border-cyan-400' : 'bg-transparent text-cyan-400 border-cyan-900/50'
            }`}
          >
            AGENT ROSTER
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
                  className="kizuna-shard-btn-wrapper"
                >
                  <span className="kizuna-shard-btn-inner">
                    {status === 'connecting' ? (
                      'SYNCING...'
                    ) : connected ? (
                      <>TERMINATE <Power size={20} /></>
                    ) : (
                      <>INITIATE LINK <Power size={20} /></>
                    )}
                  </span>
                </button>
              </div>
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
              <AgentRoster onSelect={() => setViewMode('core')} />
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      {/* PERIPHERAL PANELS */}
      <VisionPanel />
      <EpistemicPanel />
      <SystemLogs />

      <JulesSanctuary
        isOpen={isSanctuaryOpen}
        onClose={() => setIsSanctuaryOpen(false)}
        api={api}
      />

      {/* FOOTER STATUS */}
      <footer className="fixed bottom-0 left-0 w-full p-4 flex justify-between items-end z-40 pointer-events-none opacity-80 text-[10px] font-technical text-cyan-700">
        <div>
           MEMORY_USAGE: 64TB // LATENCY: 12ms
        </div>
        <div>
           SECURE_CHANNEL: {connected ? 'ENCRYPTED' : 'OPEN'} // PORT: 8000
        </div>
      </footer>
    </Layout>
  );
}

export default App;
