import { useState, useRef, useCallback, useEffect, useMemo } from 'react';
import type { ServerMessage } from '../types/websocket';
import { getWebSocketUrl } from '../utils/connection';
import { AudioStreamManager } from '../utils/AudioStreamManager';

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
  const audioManagerRef = useRef<AudioStreamManager | null>(null);
  const volumeRef = useRef<number>(0);

  const disconnect = useCallback(() => {
    console.log('Disconnecting Live API...');

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    if (audioManagerRef.current) {
      audioManagerRef.current.cleanup();
      audioManagerRef.current = null;
    }

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
      const wsUrl = getWebSocketUrl(agentId);
      const ws = new WebSocket(wsUrl);
      ws.binaryType = 'arraybuffer';
      wsRef.current = ws;

      ws.onopen = async () => {
        console.log('WebSocket Connected');

        try {
            // Initialize Audio Manager
            audioManagerRef.current = new AudioStreamManager(
                volumeRef,
                (data: ArrayBuffer) => {
                    if (ws.readyState === WebSocket.OPEN) {
                        ws.send(data);
                    }
                }
            );

            await audioManagerRef.current.start();

            setStatus('connected');
            setConnected(true);

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
            setIsAiSpeaking(true);

            if (audioManagerRef.current) {
                audioManagerRef.current.playAudioChunk(event.data);
            }
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

  // Optimization: Memoize return value to prevent re-renders of consuming components (App, etc.)
  // when internal state (like refs) hasn't changed.
  return useMemo(() => ({
    connected,
    status,
    isAiSpeaking,
    volumeRef,
    lastAiMessage,
    connect,
    disconnect,
    sendImage
  }), [
    connected,
    status,
    isAiSpeaking,
    lastAiMessage,
    connect,
    disconnect,
    sendImage
  ]);
};
