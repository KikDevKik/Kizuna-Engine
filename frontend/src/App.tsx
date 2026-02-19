import { useRef, useEffect } from 'react';
import { useLiveAPI } from './hooks/useLiveAPI';
import './KizunaHUD.css';

function App() {
  const { connected, status, volumeRef, isAiSpeaking, connect, disconnect } = useLiveAPI();
  const coreRef = useRef<HTMLDivElement>(null);

  // Derived state for Law 4
  const isListening = connected && !isAiSpeaking;

  // LEY 4: EL NÚCLEO REACTIVO (Optimized Animation Loop)
  useEffect(() => {
    let animationFrameId: number;

    const animate = () => {
      if (coreRef.current) {
        // Calculate volume scale
        // volumeRef.current is roughly 0.0 to 1.0 (sometimes higher)
        // We dampen it slightly for smoother visual scaling
        const vol = volumeRef.current * 0.5;

        // Update CSS variable directly to avoid React re-renders
        coreRef.current.style.setProperty('--vol-scale', vol.toFixed(3));
      }
      animationFrameId = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      cancelAnimationFrame(animationFrameId);
    };
  }, [volumeRef]);

  const handleToggle = () => {
    if (connected) {
      disconnect();
    } else {
      connect();
    }
  };

  return (
    <div className="kizuna-hud">
      {/* HEADER */}
      <header className="hud-header">
        <div className="title-block">
          <h1 className="hud-title">KIZUNA ENGINE</h1>
          <div className="title-underline"></div>
        </div>

        <div className="system-status" role="status" aria-live="polite">
          <div className="status-label">SYSTEM STATUS</div>
          <div className="status-value">{status}</div>
        </div>
      </header>

      {/* CORE */}
      <main className="core-container">
        <div className="ring-outer"></div>
        <div className="ring-inner"></div>

        <div
          ref={coreRef}
          className={`kizuna-core ${isListening ? 'listening' : ''} ${isAiSpeaking ? 'speaking' : ''}`}
        ></div>
      </main>

      {/* CONTROLS */}
      <div className="control-panel">
        <button
          onClick={handleToggle}
          disabled={status === 'connecting'}
          className={`btn-action ${connected ? 'terminate' : 'initiate'}`}
          aria-label={connected ? 'Terminate Connection' : 'Initiate Connection'}
        >
          {status === 'connecting' ? 'SYNCING...' : (connected ? 'TERMINATE' : 'INITIATE')}
        </button>
      </div>

      {/* FOOTER */}
      <footer className="hud-footer">
        <div>P3-RELOAD-HUD // V4.0</div>
        <div>MEM: 64TB // SYNC: {connected ? '100%' : 'OFFLINE'}</div>
      </footer>
    </div>
  );
}

export default App;
