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

  const socketRef = useRef<WebSocket | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const workletNodeRef = useRef<AudioWorkletNode | null>(null);
  const nextStartTimeRef = useRef<number>(0);

  const disconnect = useCallback(() => {
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
    try {
      setStatus('connecting');

      // 1. Initialize AudioContext with 16kHz sample rate as requested for input
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
      // Use binaryType 'arraybuffer' isn't strictly needed for sending, but good for receiving if server sent binary
      // But server sends JSON with base64, so text is fine.

      ws.onopen = () => {
        setConnected(true);
        setStatus('connected');
        console.log('WebSocket connected');
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        disconnect();
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
            // Decode Base64 audio chunk
            const binaryString = atob(message.data);
            const len = binaryString.length;
            const bytes = new Uint8Array(len);
            for (let i = 0; i < len; i++) {
              bytes[i] = binaryString.charCodeAt(i);
            }

            // Convert to Int16 PCM (assuming Little Endian)
            const int16Data = new Int16Array(bytes.buffer);

            // Convert to Float32 for AudioBuffer
            const float32Data = new Float32Array(int16Data.length);
            for (let i = 0; i < int16Data.length; i++) {
                // Normalize Int16 to Float32 [-1.0, 1.0]
                float32Data[i] = int16Data[i] / 32768.0;
            }

            // Create AudioBuffer
            // Gemini typically returns 24kHz audio. We create a buffer with that rate.
            // The 16kHz context will handle resampling during playback.
            const buffer = ctx.createBuffer(1, float32Data.length, 24000);
            buffer.copyToChannel(float32Data, 0);

            // Schedule Playback (Queue)
            const source = ctx.createBufferSource();
            source.buffer = buffer;
            source.connect(ctx.destination);

            const currentTime = ctx.currentTime;
            // Schedule next start time. If we fell behind, start immediately.
            const startTime = Math.max(currentTime, nextStartTimeRef.current);
            source.start(startTime);

            // Update next start time
            nextStartTimeRef.current = startTime + buffer.duration;
          } else if (message.type === 'turn_complete') {
            setIsAiSpeaking(false);
          }
        } catch (e) {
          console.error("Error processing message", e);
        }
      };

      // 4. Get User Media (Microphone)
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 16000,
        }
      });
      mediaStreamRef.current = stream;

      // 5. Connect Microphone -> Worklet -> Destination (muted)
      const source = ctx.createMediaStreamSource(stream);
      const worklet = new AudioWorkletNode(ctx, 'pcm-processor');

      // Handle messages from Worklet (Int16 PCM data)
      worklet.port.onmessage = (event) => {
        const int16Data = event.data; // Int16Array

        // Calculate volume for visualization (simple RMS)
        let sum = 0;
        for (let i = 0; i < int16Data.length; i++) {
            sum += (int16Data[i] / 32768.0) ** 2;
        }
        const rms = Math.sqrt(sum / int16Data.length);
        setVolume(Math.min(1, rms * 5)); // Boost a bit for visibility

        if (ws.readyState === WebSocket.OPEN) {
          ws.send(int16Data);
        }
      };

      source.connect(worklet);
      // Connect to destination to keep the graph alive (but worklet outputs silence)
      worklet.connect(ctx.destination);
      workletNodeRef.current = worklet;

    } catch (e) {
      console.error("Error connecting", e);
      setStatus('error');
      disconnect(); // Cleanup partial setup
    }
  }, [disconnect]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return { connected, status, volume, isAiSpeaking, connect, disconnect };
};
