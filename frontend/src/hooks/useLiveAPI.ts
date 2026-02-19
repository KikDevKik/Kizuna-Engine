import { useState, useCallback, useRef, useEffect } from 'react';

// Use environment variable for WebSocket URL, defaulting to localhost
const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/live';

export interface UseLiveAPI {
  connected: boolean;
  status: 'disconnected' | 'connecting' | 'connected' | 'error';
  volumeRef: React.MutableRefObject<number>;
  isAiSpeaking: boolean;
  connect: () => Promise<void>;
  disconnect: () => void;
}

export const useLiveAPI = (): UseLiveAPI => {
  const [connected, setConnected] = useState(false);
  const [status, setStatus] = useState<'disconnected' | 'connecting' | 'connected' | 'error'>('disconnected');
  const volumeRef = useRef(0);
  const [isAiSpeaking, setIsAiSpeaking] = useState(false);

  // 1. References for persistent connection objects
  const socketRef = useRef<WebSocket | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const workletNodeRef = useRef<AudioWorkletNode | null>(null);
  const nextStartTimeRef = useRef<number>(0);
  const isConnectingRef = useRef<boolean>(false);

  // Telemetry ref
  const packetCountRef = useRef<number>(0);

  const disconnect = useCallback(() => {
    console.log("Disconnecting by user command...");
    console.trace("Disconnect called from:");
    if (socketRef.current) {
      // Only close if open to avoid errors
      if (socketRef.current.readyState === WebSocket.OPEN || socketRef.current.readyState === WebSocket.CONNECTING) {
          socketRef.current.close();
      }
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
    volumeRef.current = 0;
    setIsAiSpeaking(false);
    nextStartTimeRef.current = 0;
    isConnectingRef.current = false;
    packetCountRef.current = 0;
  }, []);

  const connect = useCallback(async () => {
    // Prevent multiple connections
    if (socketRef.current || isConnectingRef.current) {
        console.warn("Connection attempt ignored: already connected or connecting.");
        return;
    }

    try {
      isConnectingRef.current = true;
      setStatus('connecting');
      console.log("Initiating connection...");
      packetCountRef.current = 0;

      // 1. Initialize AudioContext
      const ctx = new AudioContext({ sampleRate: 16000 });
      audioContextRef.current = ctx;
      await ctx.resume();

      // 2. Load AudioWorklet
      try {
        // Cache Busting: Add timestamp to force reload
        await ctx.audioWorklet.addModule(`/pcm-processor.js?v=${Date.now()}`);
      } catch (e) {
        console.error("Failed to load audio worklet", e);
        throw e;
      }

      // 3. Setup WebSocket
      console.log(`Connecting to WebSocket at ${WS_URL}...`);
      const ws = new WebSocket(WS_URL);
      socketRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected (onopen event)');
        setConnected(true);
        setStatus('connected');
        isConnectingRef.current = false;
      };

      ws.onclose = (event) => {
        console.log(`WebSocket disconnected (onclose event). Code: ${event.code}, Reason: "${event.reason}", WasClean: ${event.wasClean}`);
        // DO NOT call disconnect() here automatically.
        // Just update UI status if needed, but keep objects alive per request "Immovable constant".
        // However, if the socket is closed, we can't really use it.
        // We will mark it as not connected in UI but NOT cleanup the AudioContext/MediaStream.
        setConnected(false);
        // setStatus('disconnected'); // Maybe keep 'connected' visual to show it *was* connected? No, 'disconnected' is honest.
      };

      ws.onerror = (error) => {
        console.error('WebSocket error (onerror event)', error);
        setStatus('error');
        // DO NOT call disconnect() here.
      };

      ws.onmessage = async (event) => {
        // console.log('WebSocket message received:', event.data.substring(0, 50) + "..."); // Reduce noise
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
            console.log("Turn complete signal received.");
            // STRICT HANDLING: Only update UI state.
            // DO NOT stop microphone, DO NOT close socket.
            setIsAiSpeaking(false);
            // Explicitly do NOT call disconnect()
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
        volumeRef.current = Math.min(1, rms * 5);

        // Send to WebSocket if open
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(int16Data);

          // Telemetry
          packetCountRef.current++;
          if (packetCountRef.current % 50 === 0) {
              console.log(`[UseLiveAPI] Sent ${packetCountRef.current} audio packets via WebSocket`);
          }
        }
      };

      source.connect(worklet);
      worklet.connect(ctx.destination);
      workletNodeRef.current = worklet;

    } catch (e) {
      console.error("Error connecting", e);
      setStatus('error');
      // DO NOT automatically disconnect here to allow inspection
      isConnectingRef.current = false;
    }
  }, [disconnect]);

  // AudioContext Watchdog
  useEffect(() => {
    let interval: number | undefined;
    if (connected && audioContextRef.current) {
        interval = window.setInterval(() => {
            if (audioContextRef.current?.state === 'suspended') {
                console.warn("[UseLiveAPI] AudioContext suspended. Attempting to resume...");
                audioContextRef.current.resume();
            }
        }, 2000);
    }
    return () => {
        if (interval) clearInterval(interval);
    };
  }, [connected]);

  // Cleanup ONLY on unmount - DISABLED per request for "immovable constant"
  // The user explicitly requested to REMOVE any automatic close triggers.
  // We will leave this empty or comment it out to prevent React Strict Mode from killing the connection.
  /*
  useEffect(() => {
    return () => {
        console.log("Component unmounting - cleanup skipped per 'immovable' requirement");
        // disconnect();
    };
  }, [disconnect]);
  */

  return { connected, status, volumeRef, isAiSpeaking, connect, disconnect };
};
