import { useRef, useEffect } from 'react';
import { useLiveAPI } from './hooks/useLiveAPI';

function App() {
  const { connected, status, volume, isAiSpeaking, connect, disconnect } = useLiveAPI();

  // Volume visualizer using scale
  const coreRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (coreRef.current && connected && !isAiSpeaking) {
      // User is speaking (or silence)
      // Scale base is 1.0, max is 1.3 based on volume
      const scale = 1.0 + (volume * 0.3);
      coreRef.current.style.transform = `scale(${scale})`;
    } else if (coreRef.current) {
      coreRef.current.style.transform = 'scale(1.0)';
    }
  }, [volume, connected, isAiSpeaking]);

  const handleToggle = () => {
    if (connected) {
      disconnect();
    } else {
      connect();
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-midnight text-pure-white p-4 font-mono relative overflow-hidden">
      {/* Background Patterns */}
      <div className="absolute inset-0 bg-grid-pattern pointer-events-none opacity-40"></div>
      <div className="absolute inset-0 scanlines pointer-events-none opacity-30"></div>

      {/* Header */}
      <div className="absolute top-8 left-8 z-10">
        <h1 className="text-2xl font-black italic tracking-widest uppercase text-cyan-persona drop-shadow-[0_0_10px_rgba(0,229,255,0.8)]">
          KIZUNA ENGINE
        </h1>
        <div className="h-1 w-32 bg-cyan-persona mt-1 clip-diagonal"></div>
      </div>

      <div className="absolute top-8 right-8 z-10 flex items-center space-x-4">
        <div className="text-right">
          <div className="text-xs text-cyan-persona uppercase tracking-widest">System Status</div>
          <div className="text-xl font-bold uppercase">{status}</div>
        </div>
        <div className={`w-3 h-3 rotate-45 border border-cyan-persona ${connected ? 'bg-cyan-persona animate-pulse' : 'bg-transparent'}`}></div>
      </div>


      {/* Resonance Center */}
      <div className="relative z-10 mb-24 flex items-center justify-center">
        {/* Outer Ring */}
        <div className={`absolute w-80 h-80 rounded-full border border-gray-800 transition-all duration-500 ${connected ? 'scale-100 opacity-100' : 'scale-75 opacity-20'}`}></div>
        <div className={`absolute w-[400px] h-[400px] rounded-full border border-gray-900 transition-all duration-700 ${connected ? 'scale-100 opacity-50' : 'scale-50 opacity-0'}`}></div>

        {/* Core Circle */}
        <div
          ref={coreRef}
          className={`w-48 h-48 rounded-full flex items-center justify-center transition-all duration-100 ease-out
                ${connected && isAiSpeaking
              ? 'bg-pure-white shadow-[0_0_60px_rgba(255,255,255,0.6)] animate-pulse' /* AI Speaking: White Glow */
              : connected
                ? 'bg-tartarus border-4 border-cyan-persona shadow-[0_0_20px_rgba(0,229,255,0.4)] animate-pulse' /* Listening: Cyan Border + Pulse */
                : 'bg-tartarus border border-gray-700' /* Disconnected */
            }
            `}
        >
        </div>
      </div>

      {/* Controls */}
      <button
        onClick={handleToggle}
        className={`
            relative z-10 w-72 h-16
            clip-diagonal
            flex items-center justify-center
            text-xl font-black tracking-[0.2em] uppercase
            transition-all duration-300
            cursor-pointer select-none
            group
            ${connected
            ? 'bg-pure-white text-midnight hover:bg-red-500 hover:text-white'
            : 'bg-pure-white text-midnight hover:bg-cyan-persona hover:text-white'
          }
        `}
      >
        <span className="relative z-10 group-hover:scale-105 transition-transform">
          {connected ? 'TERMINATE' : 'INITIATE'}
        </span>
      </button>

      {/* Footer / Decorative */}
      <div className="absolute bottom-8 w-full px-8 flex justify-between items-end text-xs text-gray-500 font-bold uppercase tracking-widest pointer-events-none">
        <div>
          P3-HUD-V3.5 // ART_DIR
        </div>
        <div className="flex flex-col items-end">
          <span>MEM: 64TB</span>
          <span>SYNC: {connected ? '100%' : 'OFFLINE'}</span>
        </div>
      </div>

    </div>
  );
}

export default App;
