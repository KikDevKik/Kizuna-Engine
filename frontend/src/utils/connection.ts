export const getWebSocketUrl = (agentId: string, lang: string = 'en', token?: string): string => {
  const base = import.meta.env.VITE_BACKEND_URL || '';
  const protocol = base.startsWith('https') ? 'wss:' : 'ws:';
  const host = base ? base.replace(/^https?:\/\//, '') : window.location.host;
  const tokenParam = token ? `&token=${token}` : '';
  return `${protocol}//${host}/ws/live?agent_id=${agentId}&lang=${lang}${tokenParam}`;
};
