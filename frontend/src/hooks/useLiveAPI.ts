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
  addSystemAudio: (track: MediaStreamTrack) => void;
  removeSystemAudio: () => void;
}

export const useLiveAPI = (): UseLiveAPI => {
  const [status, setStatus] = useState<'disconnected' | 'connecting' | 'connected' | 'error'>('disconnected');
  const [connected, setConnected] = useState(false);
  const [isAiSpeaking, setIsAiSpeaking] = useState(false);
  const [lastAiMessage, setLastAiMessage] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const audioManagerRef = useRef<AudioStreamManager | null>(null);
  const recognitionRef = useRef<any>(null); // TRUE ECHO: Native Speech Recognition
  const volumeRef = useRef<number>(0);
  const connectionTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const disconnect = useCallback(() => {
    console.log('Disconnecting Live API...');

    if (connectionTimeoutRef.current) {
        clearTimeout(connectionTimeoutRef.current);
        connectionTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    if (audioManagerRef.current) {
      audioManagerRef.current.cleanup();
      audioManagerRef.current = null;
    }

    // Stop Speech Recognition
    if (recognitionRef.current) {
        recognitionRef.current.onend = null;
        recognitionRef.current.stop();
        recognitionRef.current = null;
    }

    setStatus('disconnected');
    setConnected(false);
    setIsAiSpeaking(false);
  }, []);

  // TRUE ECHO PROTOCOL: Native Browser Speech Recognition
  useEffect(() => {
    if (connected && wsRef.current) {
        const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

        if (SpeechRecognition) {
            const recognition = new SpeechRecognition();
            recognition.continuous = true;
            recognition.interimResults = false;
            recognition.lang = 'en-US';

            recognition.onresult = (event: any) => {
                const lastResult = event.results[event.results.length - 1];
                if (lastResult.isFinal) {
                    const transcript = lastResult[0].transcript;
                    console.log("True Echo Transcript:", transcript);

                    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
                        wsRef.current.send(JSON.stringify({
                            type: "native_transcript",
                            text: transcript
                        }));
                    }
                }
            };

            recognition.onerror = (event: any) => {
                // benign errors like 'no-speech' are common
                if (event.error !== 'no-speech') {
                    console.error("Speech recognition error:", event.error);
                }
            };

            recognition.onend = () => {
                 // Auto-restart if still connected
                 // Check connected state via ref or relying on closure, but connected is in dependency array
                 // so this effect runs on change.
                 // We can check wsRef.current state.
                 if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
                     try {
                         recognition.start();
                     } catch (e) {
                         // Ignore if already started
                     }
                 }
            };

            try {
                recognition.start();
                recognitionRef.current = recognition;
                console.log("True Echo Protocol: Listening...");
            } catch (e) {
                console.error("Failed to start SpeechRecognition:", e);
            }
        } else {
            console.warn("True Echo Protocol: Browser does not support SpeechRecognition.");
        }
    } else {
        // Cleanup if connected becomes false (handled by disconnect too, but safe here)
        if (recognitionRef.current) {
            recognitionRef.current.onend = null;
            recognitionRef.current.stop();
            recognitionRef.current = null;
        }
    }

    return () => {
         if (recognitionRef.current) {
            recognitionRef.current.onend = null;
            recognitionRef.current.stop();
            recognitionRef.current = null;
        }
    };
  }, [connected]);

  const connect = useCallback(async (agentId: string) => {
    if (!agentId) return;

    // Cleanup any existing connection
    disconnect();

    setStatus('connecting');

    // 15s Connection Timeout
    connectionTimeoutRef.current = setTimeout(() => {
        console.error("Connection timed out (15s). Backend may be slow or unresponsive.");
        if (wsRef.current && wsRef.current.readyState !== WebSocket.OPEN) {
            wsRef.current.close();
        }
        setStatus('error');
    }, 15000);

    try {
      // Initialize WebSocket
      const wsUrl = getWebSocketUrl(agentId);
      const ws = new WebSocket(wsUrl);
      ws.binaryType = 'arraybuffer';
      wsRef.current = ws;

      ws.onopen = async () => {
        console.log('WebSocket Connected');
        if (connectionTimeoutRef.current) {
            clearTimeout(connectionTimeoutRef.current);
            connectionTimeoutRef.current = null;
        }

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
        if (connectionTimeoutRef.current) {
            clearTimeout(connectionTimeoutRef.current);
            connectionTimeoutRef.current = null;
        }
        setStatus('error');
      };

      ws.onclose = (event) => {
        console.log(`WebSocket closed: ${event.code} (Reason: ${event.reason})`);
        if (connectionTimeoutRef.current) {
            clearTimeout(connectionTimeoutRef.current);
            connectionTimeoutRef.current = null;
        }

        // Handle Abnormal Closures (1006, 1011) by setting Error state
        // This gives UI feedback that connection was dropped, rather than just "stopped".
        if (event.code === 1006 || event.code === 1011) {
            console.warn("Abnormal closure. Setting status to error.");

            // Clean up without resetting status to 'disconnected' (which disconnect() does)
            if (wsRef.current) {
                wsRef.current = null;
            }
            if (audioManagerRef.current) {
                audioManagerRef.current.cleanup();
                audioManagerRef.current = null;
            }
            setConnected(false);
            setIsAiSpeaking(false);
            setStatus('error');
        } else {
            disconnect();
        }
      };

    } catch (err) {
      console.error('Connection failed:', err);
      if (connectionTimeoutRef.current) {
          clearTimeout(connectionTimeoutRef.current);
          connectionTimeoutRef.current = null;
      }
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

  const addSystemAudio = useCallback((track: MediaStreamTrack) => {
    if (audioManagerRef.current) {
        audioManagerRef.current.addSystemAudioTrack(track);
    } else {
        console.warn("Audio Manager not initialized. Cannot add system audio.");
    }
  }, []);

  const removeSystemAudio = useCallback(() => {
    if (audioManagerRef.current) {
        audioManagerRef.current.removeSystemAudioTrack();
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
    sendImage,
    addSystemAudio,
    removeSystemAudio
  }), [
    connected,
    status,
    isAiSpeaking,
    lastAiMessage,
    connect,
    disconnect,
    sendImage,
    addSystemAudio,
    removeSystemAudio
  ]);
};
