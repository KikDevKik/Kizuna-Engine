import React, { createContext, useContext, useState, useCallback, type ReactNode } from 'react';

export interface RitualMessage {
  role: 'system' | 'user';
  content: string;
}

export interface RitualState {
  messages: RitualMessage[];
  status: 'idle' | 'active' | 'complete' | 'error';
  isLoading: boolean;
  error: string | null;
}

interface RitualContextType extends RitualState {
  sendMessage: (content: string) => Promise<void>;
  startRitual: () => Promise<void>;
  resetRitual: () => void;
}

const RitualContext = createContext<RitualContextType | undefined>(undefined);

const RITUAL_TIMEOUT_MS = 45000; // 45s Timeout

export const RitualProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [messages, setMessages] = useState<RitualMessage[]>([]);
  const [status, setStatus] = useState<'idle' | 'active' | 'complete' | 'error'>('idle');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const resetRitual = useCallback(() => {
    setMessages([]);
    setStatus('idle');
    setIsLoading(false);
    setError(null);
  }, []);

  const startRitual = useCallback(async () => {
    // Only start if idle or empty to avoid overwriting existing state
    if (messages.length > 0) return;

    setIsLoading(true);
    setStatus('active');
    setError(null);

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), RITUAL_TIMEOUT_MS);

    try {
      // Empty history triggers initial question from backend
      // Using absolute URL to avoid Proxy method stripping or 404s
      const locale = navigator.language || 'en';
      const response = await fetch('http://localhost:8000/api/agents/ritual', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept-Language': locale
        },
        body: JSON.stringify([]),
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
          if (response.status === 405) {
             throw new Error('Method Not Allowed (405). Check backend routing.');
          }
          throw new Error(`Failed to initiate ritual: ${response.status}`);
      }

      const data = await response.json();

      // Backend returns { is_complete, message, agent }
      if (data.message) {
        setMessages([{ role: 'system', content: data.message }]);
      }
    } catch (err: any) {
      if (err.name === 'AbortError') {
          setError('The Void is silent (Timeout). Check the roster, the soul may have been forged properly.');
      } else {
          setError(err.message || 'Connection to the Void failed.');
      }
      setStatus('error');
    } finally {
      clearTimeout(timeoutId);
      setIsLoading(false);
    }
  }, [messages.length]);

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim()) return;

    // Optimistically add user message
    const userMsg: RitualMessage = { role: 'user', content };
    const newHistory = [...messages, userMsg];

    setMessages(newHistory);
    setIsLoading(true);
    setError(null);

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), RITUAL_TIMEOUT_MS);

    try {
      const locale = navigator.language || 'en';
      const response = await fetch('http://localhost:8000/api/agents/ritual', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept-Language': locale
        },
        body: JSON.stringify(newHistory),
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (!response.ok) throw new Error('The Void is silent.');

      const data = await response.json();

      if (data.is_complete) {
        setStatus('complete');
      } else if (data.message) {
        setMessages(prev => [...prev, { role: 'system', content: data.message }]);
      }
    } catch (err: any) {
        if (err.name === 'AbortError') {
            setError('The Void is silent (Timeout). Check the roster, the soul may have been forged properly.');
        } else {
            setError(err.message || 'Ritual interrupted.');
        }
      setStatus('error');
    } finally {
      clearTimeout(timeoutId);
      setIsLoading(false);
    }
  }, [messages]);

  return (
    <RitualContext.Provider value={{
      messages,
      status,
      isLoading,
      error,
      sendMessage,
      startRitual,
      resetRitual
    }}>
      {children}
    </RitualContext.Provider>
  );
};

export const useRitual = () => {
  const context = useContext(RitualContext);
  if (!context) {
    throw new Error('useRitual must be used within a RitualProvider');
  }
  return context;
};
