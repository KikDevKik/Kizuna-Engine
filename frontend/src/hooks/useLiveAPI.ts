import { useState, useRef, useCallback, useEffect, useMemo } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { listen } from '@tauri-apps/api/event';
import { useAuth } from './useAuth';

export type ConnectionState = 'idle' | 'connecting' | 'connected' | 'ready' | 'error';

interface ServerMessage {
    type: string;
    data?: string;
    action?: string;
    reason?: string;
    url?: string;
}

export interface UseLiveAPI {
    connected: boolean;
    status: ConnectionState;
    isAiSpeaking: boolean;
    isSevered: boolean;
    severanceReason: string | null;
    volumeRef: React.MutableRefObject<number>;
    lastAiMessage: string | null;
    connect: (agentId: string) => Promise<void>;
    disconnect: () => Promise<void>;
    sendImage: (base64: string) => Promise<void>;
    addSystemAudio: (track: MediaStreamTrack) => void;
    removeSystemAudio: () => void;
}

export const useLiveAPI = (): UseLiveAPI => {
    const { getToken } = useAuth();
    const [connected, setConnected] = useState(false);
    const [status, setStatus] = useState<ConnectionState>('idle');
    const [isAiSpeaking, setIsAiSpeaking] = useState(false);
    const [lastAiMessage, setLastAiMessage] = useState<string | null>(null);
    const [isSevered, setIsSevered] = useState(false);
    const [severanceReason, setSeveranceReason] = useState<string | null>(null);

    const volumeRef = useRef(0);
    const currentAgentId = useRef<string | null>(null);
    const shouldReconnect = useRef(false);
    const statusRef = useRef<ConnectionState>('idle');
    const unlistenFns = useRef<Array<() => void>>([]);

    const disconnect = useCallback(async () => {
        console.log("🛑 Disconnecting and cleaning up audio pipeline...");
        shouldReconnect.current = false;

        try {
            await invoke('stop_audio_pipeline');
        } catch (e) {
            console.error("Failed to stop audio pipeline:", e);
        }

        for (const unlisten of unlistenFns.current) {
            unlisten();
        }
        unlistenFns.current = [];

        setConnected(false);
        setIsAiSpeaking(false);
        setStatus('idle');
        statusRef.current = 'idle';
        currentAgentId.current = null;
        setSeveranceReason(null);
        setIsSevered(false);
    }, []);

    const setupListeners = useCallback(async () => {
        // Clear previous listeners just in case
        for (const unlisten of unlistenFns.current) {
            unlisten();
        }
        unlistenFns.current = [];

        const unlistenConnected = await listen('audio_connected', () => {
            console.log('Rust Audio Pipeline Connected');
            setStatus('connected');
            setConnected(true);
            statusRef.current = 'connected';
            // We can assume it's ready once connected since Rust handles audio init immediately
            setStatus('ready');
            statusRef.current = 'ready';
        });

        const unlistenDisconnected = await listen('audio_disconnected', () => {
            console.log('Rust Audio Pipeline Disconnected');
            if (shouldReconnect.current) {
                // Here we could implement reconnect logic by calling connect again
                // For now, let's just mark as disconnected.
                setConnected(false);
                setStatus('idle');
                statusRef.current = 'idle';
            } else {
                disconnect();
            }
        });

        const unlistenError = await listen<string>('audio_error', (event) => {
            console.error('Rust Audio Pipeline Error:', event.payload);
            setStatus('error');
            statusRef.current = 'error';
            disconnect();
        });

        const unlistenMessage = await listen<string>('ws_message_received', (event) => {
            try {
                const message = JSON.parse(event.payload) as ServerMessage;

                if (message.type === 'session_ready') {
                    setStatus('ready');
                    statusRef.current = 'ready';
                } else if (message.type === 'text') {
                    setLastAiMessage(message.data || null);
                } else if (message.type === 'turn_complete') {
                    setIsAiSpeaking(false);
                } else if (message.type === 'control' || message.type === 'CONTROL') {
                    if (message.action === 'hangup') {
                        console.warn(`Server initiated hangup: ${message.reason}`);
                        setSeveranceReason(message.reason || "Connection Terminated by Host");
                        setIsSevered(true);
                        shouldReconnect.current = false;
                        disconnect();
                    } else if (message.action === 'FLUSH_AUDIO') {
                        setIsAiSpeaking(false);
                    }
                } else if (message.type === 'action' && message.action === 'open_url') {
                    const url = message.url;
                    if (url) {
                        import('@tauri-apps/plugin-opener')
                            .then(({ openUrl }) => openUrl(url))
                            .catch((e: unknown) => console.error('openUrl FAILED:', e));
                    }
                }
            } catch (e) {
                console.error("Error processing text message from Rust:", e);
            }
        });

        unlistenFns.current = [
            unlistenConnected,
            unlistenDisconnected,
            unlistenError,
            unlistenMessage
        ];
    }, [disconnect]);

    const connect = useCallback(async (agentId: string) => {
        if (!agentId) return;

        currentAgentId.current = agentId;
        shouldReconnect.current = true;

        await disconnect();
        shouldReconnect.current = true;
        setIsSevered(false);
        setSeveranceReason(null);
        setStatus('connecting');
        statusRef.current = 'connecting';

        await setupListeners();

        try {
            const userLang = navigator.language || 'en';

            // Get the actual Firebase auth token
            const token = await getToken() || 'dev_token';

            await invoke('start_audio_pipeline', {
                agentId,
                lang: userLang,
                token
            });

        } catch (err) {
            console.error('Failed to start audio pipeline:', err);
            setStatus('error');
            statusRef.current = 'error';
            disconnect();
        }
    }, [disconnect, setupListeners, getToken]);

    const sendImage = useCallback(async (base64: string) => {
        if (connected && status === 'ready') {
            const payload = JSON.stringify({
                type: "image",
                data: base64
            });
            try {
                await invoke('send_ws_message', { payload });
            } catch (e) {
                console.error("Failed to send image via WS:", e);
            }
        }
    }, [connected, status]);

    const addSystemAudio = useCallback((_track: MediaStreamTrack) => {
        console.warn("System audio mixing is now handled by Rust (WASAPI Loopback on Windows). This JS function is a no-op.");
    }, []);

    const removeSystemAudio = useCallback(() => {
        console.warn("System audio mixing is now handled by Rust. This JS function is a no-op.");
    }, []);

    useEffect(() => {
        return () => {
            disconnect();
        };
    }, [disconnect]);

    return useMemo(() => ({
        connected,
        status,
        isAiSpeaking,
        isSevered,
        severanceReason,
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
        isSevered,
        severanceReason,
        lastAiMessage,
        connect,
        disconnect,
        sendImage,
        addSystemAudio,
        removeSystemAudio
    ]);
};
