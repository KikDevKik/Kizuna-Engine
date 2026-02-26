import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

export interface Agent {
  id: string;
  name: string;
  role: string;
  avatar_path?: string | null;
  systemStatus?: string; // Frontend-only state (ONLINE, OFFLINE)
  voice_name?: string;
  traits?: Record<string, any>;
}

interface RosterContextType {
  myAgents: Agent[];
  isLoading: boolean;
  error: string | null;
  refreshAgents: () => Promise<void>;
}

const RosterContext = createContext<RosterContextType | undefined>(undefined);

export const useRoster = () => {
  const context = useContext(RosterContext);
  if (!context) {
    throw new Error('useRoster must be used within a RosterProvider');
  }
  return context;
};

export const RosterProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [myAgents, setMyAgents] = useState<Agent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAgents = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Fetch "My Agents" (Filtered by InteractedWith on backend)
      const res = await fetch('http://localhost:8000/api/agents/');

      if (!res.ok) {
        throw new Error(`Failed to fetch agents: ${res.statusText}`);
      }

      const data = await res.json();

      if (!Array.isArray(data)) {
        throw new Error("Invalid API response format");
      }

      // Transform data
      const loadedAgents: Agent[] = data.map((a: any) => ({
        id: a.id,
        name: a.name,
        role: a.role || 'UNKNOWN',
        avatar_path: a.avatar_path,
        systemStatus: 'ONLINE', // Default status
        voice_name: a.voice_name,
        traits: a.traits
      }));

      // Sort alphabetically
      loadedAgents.sort((a, b) => a.name.localeCompare(b.name));

      setMyAgents(loadedAgents);

    } catch (err: any) {
      console.error("Error fetching roster:", err);
      setError(err.message);
      // Fallback empty state
      setMyAgents([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Initial Load
  useEffect(() => {
    fetchAgents();
  }, [fetchAgents]);

  return (
    <RosterContext.Provider value={{ myAgents, isLoading, error, refreshAgents: fetchAgents }}>
      {children}
    </RosterContext.Provider>
  );
};
