export const getWebSocketUrl = (agentId: string, lang: string = 'en'): string => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${window.location.host}/ws/live?agent_id=${agentId}&lang=${lang}`;
};
