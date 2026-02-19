import React, { useEffect, useRef } from 'react';
import { useLiveAPI } from './hooks/useLiveAPI';

function App() {
  const { connected, status, volume, connect, disconnect } = useLiveAPI();

  // Simple volume visualizer using refs
  const volumeRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (volumeRef.current) {
      volumeRef.current.style.width = `${volume * 100}%`;
    }
  }, [volume]);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-black text-white p-4 font-mono">
      <h1 className="text-4xl font-bold mb-8 tracking-widest uppercase">Kizuna Engine</h1>

      <div className="w-full max-w-md bg-gray-900 rounded-lg p-6 border border-gray-700 shadow-xl">
        <div className="flex items-center justify-between mb-6">
          <span className={`h-3 w-3 rounded-full ${connected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></span>
          <span className="text-sm uppercase tracking-wider text-gray-400">{status}</span>
        </div>

        {/* Volume Meter */}
        <div className="h-2 bg-gray-800 rounded-full overflow-hidden mb-8">
           <div
             ref={volumeRef}
             className="h-full bg-blue-500 transition-all duration-75 ease-out"
             style={{ width: '0%' }}
           />
        </div>

        <button
          onClick={connected ? disconnect : connect}
          className={`w-full py-4 rounded-md font-bold text-lg transition-all duration-200 transform hover:scale-[1.02] active:scale-[0.98] ${
            connected
              ? 'bg-red-600 hover:bg-red-700 text-white shadow-[0_0_15px_rgba(220,38,38,0.5)]'
              : 'bg-blue-600 hover:bg-blue-700 text-white shadow-[0_0_15px_rgba(37,99,235,0.5)]'
          }`}
        >
          {connected ? 'DISCONNECT' : 'INITIATE LINK'}
        </button>
      </div>

      {/* TODO: Video Capture Implementation */}
      {/*
        Future implementation for video capture using navigator.mediaDevices.getUserMedia({ video: true })
        and sending frames via WebSocket.
      */}

      <div className="mt-12 text-xs text-gray-600">
        System Status: {connected ? 'ONLINE' : 'STANDBY'}
      </div>
    </div>
  );
}

export default App;
