import { useState, useCallback, useRef, useEffect } from 'react';

// Use environment variable for WebSocket URL, defaulting to localhost
const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/live';

export interface UseLiveAPI {
  connected: boolean;
  status: 'disconnected' | 'connecting' | 'connected' | 'error';
  volume: number;
  isAiSpeaking: boolean;
  connect: () => Promise<void>;
  disconnect: () => void;
}

export const useLiveAPI = (): UseLiveAPI => {
  const [connected, setConnected] = useState(false);
  const [status, setStatus] = useState<'disconnected' | 'connecting' | 'connected' | 'error'>('disconnected');
  const [volume, setVolume] = useState(0);
  const [isAiSpeaking, setIsAiSpeaking] = useState(false);

  // 1. References for persistent connection objects
  const socketRef = useRef<WebSocket | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const workletNodeRef = useRef<AudioWorkletNode | null>(null);
  const nextStartTimeRef = useRef<number>(0);

  const disconnect = useCallback(() => {
    console.log("Disconnecting...");
    if (socketRef.current) {
      socketRef.current.close();
      socketRef.current = null;
    }
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(track => track.stop());
      mediaStreamRef.current = null;
    }
    if (workletNodeRef.current) {
      workletNodeRef.current.disconnect();
      workletNodeRef.current = null;
    }
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    setConnected(false);
    setStatus('disconnected');
    setVolume(0);
    setIsAiSpeaking(false);
    nextStartTimeRef.current = 0;
  }, []);

  const connect = useCallback(async () => {
    // Prevent multiple connections
    if (socketRef.current?.readyState === WebSocket.OPEN) return;

    try {
      setStatus('connecting');

      // 1. Initialize AudioContext
      const ctx = new AudioContext({ sampleRate: 16000 });
      audioContextRef.current = ctx;
      await ctx.resume();

      // 2. Load AudioWorklet
      try {
        await ctx.audioWorklet.addModule('/pcm-processor.js');
      } catch (e) {
        console.error("Failed to load audio worklet", e);
        throw e;
      }

      // 3. Setup WebSocket
      const ws = new WebSocket(WS_URL);
      socketRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
        setStatus('connected');
        console.log('WebSocket connected');
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        // Only call disconnect if we are not already disconnected to avoid loops
        // Check if the ref still points to this socket, or if it's already cleared
        if (socketRef.current === ws) {
             disconnect();
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error', error);
        setStatus('error');
      };

      ws.onmessage = async (event) => {
        try {
          const message = JSON.parse(event.data);
          if (message.type === 'audio') {
            setIsAiSpeaking(true);

            // Audio processing
            const binaryString = atob(message.data);
            const len = binaryString.length;
            const bytes = new Uint8Array(len);
            for (let i = 0; i < len; i++) {
              bytes[i] = binaryString.charCodeAt(i);
            }
            const int16Data = new Int16Array(bytes.buffer);
            const float32Data = new Float32Array(int16Data.length);
            for (let i = 0; i < int16Data.length; i++) {
                float32Data[i] = int16Data[i] / 32768.0;
            }

            const buffer = ctx.createBuffer(1, float32Data.length, 24000);
            buffer.copyToChannel(float32Data, 0);

            const source = ctx.createBufferSource();
            source.buffer = buffer;
            source.connect(ctx.destination);

            const currentTime = ctx.currentTime;
            const startTime = Math.max(currentTime, nextStartTimeRef.current);
            source.start(startTime);
            nextStartTimeRef.current = startTime + buffer.duration;

          } else if (message.type === 'turn_complete') {
            // STRICT HANDLING: Only update UI state.
            // DO NOT stop microphone, DO NOT close socket.
            setIsAiSpeaking(false);
          }
        } catch (e) {
          console.error("Error processing message", e);
        }
      };

      // 4. Get User Media
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 16000,
        }
      });
      mediaStreamRef.current = stream;

      // 5. Connect Microphone -> Worklet
      const source = ctx.createMediaStreamSource(stream);
      const worklet = new AudioWorkletNode(ctx, 'pcm-processor');

      worklet.port.onmessage = (event) => {
        const int16Data = event.data;

        // Volume visualization
        let sum = 0;
        for (let i = 0; i < int16Data.length; i++) {
            sum += (int16Data[i] / 32768.0) ** 2;
        }
        const rms = Math.sqrt(sum / int16Data.length);
        setVolume(Math.min(1, rms * 5));

        // Send to WebSocket if open
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(int16Data);
        }
      };

      source.connect(worklet);
      worklet.connect(ctx.destination);
      workletNodeRef.current = worklet;

    } catch (e) {
      console.error("Error connecting", e);
      setStatus('error');
      disconnect();
    }
  }, [disconnect]);

  // Cleanup ONLY on unmount.
  useEffect(() => {
    return () => {
        disconnect();
    };
  }, [disconnect]);

  return { connected, status, volume, isAiSpeaking, connect, disconnect };
};
