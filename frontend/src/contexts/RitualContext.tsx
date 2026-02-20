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

    try {
      // Empty history triggers initial question from backend
      const response = await fetch('/api/agents/ritual', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify([])
      });

      if (!response.ok) throw new Error('Failed to initiate ritual');

      const data = await response.json();

      // Backend returns { is_complete, message, agent }
      if (data.message) {
        setMessages([{ role: 'system', content: data.message }]);
      }
    } catch (err: any) {
      setError(err.message || 'Connection to the Void failed.');
      setStatus('error');
    } finally {
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

    try {
      const response = await fetch('/api/agents/ritual', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newHistory)
      });

      if (!response.ok) throw new Error('The Void is silent.');

      const data = await response.json();

      if (data.is_complete) {
        setStatus('complete');
        // We don't add a final system message here usually, or maybe a "Ritual Complete" message?
        // The backend might return a message even on completion?
        // Let's check the backend logic again.
        // Backend: returns { is_complete: True, agent: ... }
        // It does NOT return a message field on completion in the code I read.
        // So we stop here. The UI will handle the completion animation.
      } else if (data.message) {
        setMessages(prev => [...prev, { role: 'system', content: data.message }]);
      }
    } catch (err: any) {
      setError(err.message || 'Ritual interrupted.');
      setStatus('error');
    } finally {
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
