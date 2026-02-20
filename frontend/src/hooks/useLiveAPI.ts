import { useState, useRef, useCallback, useEffect } from 'react';
import { createAudioBuffer } from '../utils/audioUtils';
import { ServerMessage } from '../types/websocket';

export interface UseLiveAPI {
  connected: boolean;
  status: 'disconnected' | 'connecting' | 'connected' | 'error';
  isAiSpeaking: boolean;
  volumeRef: React.MutableRefObject<number>;
  lastAiMessage: string | null;
  connect: (agentId: string) => Promise<void>;
  disconnect: () => void;
  sendImage: (base64: string) => void;
}

export const useLiveAPI = (): UseLiveAPI => {
  const [status, setStatus] = useState<'disconnected' | 'connecting' | 'connected' | 'error'>('disconnected');
  const [connected, setConnected] = useState(false);
  const [isAiSpeaking, setIsAiSpeaking] = useState(false);
  const [lastAiMessage, setLastAiMessage] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const workletNodeRef = useRef<AudioWorkletNode | null>(null);
  const sourceNodeRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const nextStartTimeRef = useRef<number>(0);
  const volumeRef = useRef<number>(0);
  const animationFrameRef = useRef<number | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);

  const disconnect = useCallback(() => {
    console.log('Disconnecting Live API...');

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    if (sourceNodeRef.current) {
      sourceNodeRef.current.disconnect();
      sourceNodeRef.current = null;
    }

    if (workletNodeRef.current) {
      workletNodeRef.current.disconnect();
      workletNodeRef.current = null;
    }

    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(track => track.stop());
      mediaStreamRef.current = null;
    }

    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }

    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }

    // Reset volume
    volumeRef.current = 0;

    setStatus('disconnected');
    setConnected(false);
    setIsAiSpeaking(false);
  }, []);

  const connect = useCallback(async (agentId: string) => {
    if (!agentId) return;

    // Cleanup any existing connection
    disconnect();

    setStatus('connecting');

    try {
      // Initialize WebSocket
      // Assuming localhost:8000 based on standard dev setup if proxy isn't configured
      const wsUrl = `ws://localhost:8000/ws/live?agent_id=${agentId}`;
      const ws = new WebSocket(wsUrl);
      ws.binaryType = 'arraybuffer';
      wsRef.current = ws;

      ws.onopen = async () => {
        console.log('WebSocket Connected');

        try {
          // Initialize Audio Context
          const ctx = new AudioContext({ sampleRate: 16000 });
          audioContextRef.current = ctx;
          await ctx.resume();

          // Load Audio Worklet
          await ctx.audioWorklet.addModule('/pcm-processor.js');

          // Get User Media
          const stream = await navigator.mediaDevices.getUserMedia({
            audio: {
              sampleRate: 16000,
              channelCount: 1,
              echoCancellation: true,
              autoGainControl: true,
              noiseSuppression: true
            }
          });
          mediaStreamRef.current = stream;

          // Create Source
          const source = ctx.createMediaStreamSource(stream);
          sourceNodeRef.current = source;

          // Create Worklet
          const worklet = new AudioWorkletNode(ctx, 'pcm-processor');
          workletNodeRef.current = worklet;

          // Connect Source -> Worklet
          // Note: Worklet does NOT connect to destination to prevent feedback loop
          source.connect(worklet);

          // Worklet -> WebSocket
          worklet.port.onmessage = (event) => {
            if (ws.readyState === WebSocket.OPEN) {
              ws.send(event.data);
            }
          };

          // Analyzer for Volume Visualization
          const analyser = ctx.createAnalyser();
          analyser.fftSize = 256;
          source.connect(analyser);
          analyserRef.current = analyser;

          // Volume Analysis Loop
          const updateVolume = () => {
            if (!analyserRef.current) return;
            const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
            analyserRef.current.getByteFrequencyData(dataArray);

            // Calculate average volume
            let sum = 0;
            for (let i = 0; i < dataArray.length; i++) {
              sum += dataArray[i];
            }
            const average = sum / dataArray.length;

            // Normalize to 0-1 range (approximate)
            volumeRef.current = Math.min(1, average / 128);

            animationFrameRef.current = requestAnimationFrame(updateVolume);
          };
          updateVolume();

          setStatus('connected');
          setConnected(true);
          nextStartTimeRef.current = ctx.currentTime;

        } catch (err) {
          console.error('Error initializing audio:', err);
          setStatus('error');
          disconnect();
        }
      };

      ws.onmessage = async (event) => {
        try {
          // 1. Binary Audio Data
          if (event.data instanceof ArrayBuffer) {
            if (!audioContextRef.current) return;

            setIsAiSpeaking(true);

            // Vista directa en memoria, sin el peso del Base64
            const int16Data = new Int16Array(event.data);
            const float32Data = new Float32Array(int16Data.length);

            // Normalización matemática directa
            for (let i = 0; i < int16Data.length; i++) {
                float32Data[i] = int16Data[i] / 32768.0;
            }

            // Inyección al AudioContext
            // createAudioBuffer defaults to 24000Hz which matches Gemini output
            const buffer = createAudioBuffer(audioContextRef.current, float32Data);
            const source = audioContextRef.current.createBufferSource();
            source.buffer = buffer;
            source.connect(audioContextRef.current.destination);

            const currentTime = audioContextRef.current.currentTime;
            const startTime = Math.max(currentTime, nextStartTimeRef.current);
            source.start(startTime);
            nextStartTimeRef.current = startTime + buffer.duration;
            
            return; 
          }

          // 2. Text / Control Messages
          if (typeof event.data === 'string') {
            const message = JSON.parse(event.data) as ServerMessage;

            if (message.type === 'text') {
                setLastAiMessage(message.data);
            } else if (message.type === 'turn_complete') {
              console.log("Turn complete signal received.");
              setIsAiSpeaking(false);
            }
          }
        } catch (e) {
          console.error("Error processing message", e);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setStatus('error');
      };

      ws.onclose = () => {
        console.log('WebSocket closed');
        disconnect();
      };

    } catch (err) {
      console.error('Connection failed:', err);
      setStatus('error');
    }
  }, [disconnect]);

  const sendImage = useCallback((base64: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      const payload = {
        type: "image",
        data: base64
      };
      wsRef.current.send(JSON.stringify(payload));
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    connected,
    status,
    isAiSpeaking,
    volumeRef,
    lastAiMessage,
    connect,
    disconnect,
    sendImage
  };
};
