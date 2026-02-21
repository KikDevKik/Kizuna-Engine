export const getWebSocketUrl = (agentId: string): string => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${window.location.host}/ws/live?agent_id=${agentId}`;
};
