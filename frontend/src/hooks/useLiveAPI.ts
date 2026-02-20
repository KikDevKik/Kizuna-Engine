import { useState, useCallback, useRef, useEffect } from 'react';

// Use environment variable for WebSocket URL, defaulting to localhost
const BASE_WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/live';

export interface UseLiveAPI {
  connected: boolean;
  status: 'disconnected' | 'connecting' | 'connected' | 'error';
  volumeRef: React.MutableRefObject<number>;
  isAiSpeaking: boolean;
  lastAiMessage: string | null;
  connect: (agentId: string) => Promise<void>;
  disconnect: () => void;
  sendImage: (base64Image: string) => void;
}

export const useLiveAPI = (): UseLiveAPI => {
  const [connected, setConnected] = useState(false);
  const [status, setStatus] = useState<'disconnected' | 'connecting' | 'connected' | 'error'>('disconnected');
  const volumeRef = useRef(0);
  const [isAiSpeaking, setIsAiSpeaking] = useState(false);
  const [lastAiMessage, setLastAiMessage] = useState<string | null>(null);

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
    if (socketRef.current) {
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

  const sendImage = useCallback((base64Image: string) => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      const payload = {
        type: "image",
        data: base64Image
      };
      socketRef.current.send(JSON.stringify(payload));
    } else {
      console.warn("Cannot send image: WebSocket is not open.");
    }
  }, []);

  const connect = useCallback(async (agentId: string) => {
    // GUARD CLAUSE: Prevent connection without agent ID
    if (!agentId) {
        console.error("Cannot connect: No agent ID provided.");
        setStatus('error');
        return;
    }

    // Prevent multiple connections
    if (socketRef.current || isConnectingRef.current) {
        console.warn("Connection attempt ignored: already connected or connecting.");
        return;
    }

    try {
      isConnectingRef.current = true;
      setStatus('connecting');
      console.log(`Initiating connection to agent: ${agentId}...`);
      packetCountRef.current = 0;

      // 1. Initialize AudioContext
      const AudioContext = window.AudioContext || (window as any).webkitAudioContext;
      const ctx = new AudioContext({ sampleRate: 16000 });
      if (ctx.sampleRate !== 16000) {
        console.error("🚨 ALERTA CRÍTICA: El navegador forzó una frecuencia de " + ctx.sampleRate + "Hz en lugar de 16000Hz. El audio se enviará corrupto.");
      }
      audioContextRef.current = ctx;
      await ctx.resume();

      // 2. Load AudioWorklet
      try {
        await ctx.audioWorklet.addModule(`/pcm-processor.js?v=${Date.now()}`);
      } catch (e) {
        console.error("Failed to load audio worklet", e);
        throw e;
      }

      // 3. Setup WebSocket with Query Param
      const wsUrl = `${BASE_WS_URL}?agent_id=${encodeURIComponent(agentId)}`;
      console.log(`Connecting to WebSocket at ${wsUrl}...`);
      const ws = new WebSocket(wsUrl);
      ws.binaryType = "arraybuffer"; // Optimize: Handle raw binary audio frames
      socketRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected (onopen event)');
        setConnected(true);
        setStatus('connected');
        isConnectingRef.current = false;
      };

      ws.onclose = (event) => {
        console.log(`WebSocket disconnected (onclose event). Code: ${event.code}, Reason: "${event.reason}"`);
        setConnected(false);
        // Do not verify status here to avoid flickering logic, relies on parent to handle state
      };

      ws.onerror = (error) => {
        console.error('WebSocket error (onerror event)', error);
        setStatus('error');
      };

      ws.onmessage = async (event) => {
        try {
          if (event.data instanceof ArrayBuffer) {
            // --- BINARY AUDIO FLOW (Optimized) ---
            setIsAiSpeaking(true);

            // Direct view into the buffer (No base64 decode needed)
            const int16Data = new Int16Array(event.data);
            const float32Data = new Float32Array(int16Data.length);

            // Standard Int16 -> Float32 normalization
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
            return;
          }

          // --- TEXT / CONTROL FLOW ---
          const message = JSON.parse(event.data);

          if (message.type === 'text') {
              setLastAiMessage(message.data);
          } else if (message.type === 'turn_complete') {
            console.log("Turn complete signal received.");
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
          noiseSuppression: true,
          echoCancellation: true,
          autoGainControl: true,
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
          packetCountRef.current++;
        }
      };

      source.connect(worklet);
      worklet.connect(ctx.destination);
      workletNodeRef.current = worklet;

    } catch (e) {
      console.error("Error connecting", e);
      setStatus('error');
      isConnectingRef.current = false;
    }
  }, [disconnect]);

  // AudioContext Watchdog
  useEffect(() => {
    let interval: number | undefined;
    if (connected && audioContextRef.current) {
        interval = window.setInterval(() => {
            const ctx = audioContextRef.current;
            if (!ctx) return;
            if (ctx.state === 'suspended') {
                console.warn("[UseLiveAPI] AudioContext suspended. Attempting to resume...");
                ctx.resume();
            }
        }, 2000);
    }
    return () => {
        if (interval) clearInterval(interval);
    };
  }, [connected]);

  return { connected, status, volumeRef, isAiSpeaking, lastAiMessage, connect, disconnect, sendImage };
};
