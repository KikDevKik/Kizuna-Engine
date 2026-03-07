const ws = new WebSocket('ws://127.0.0.1:8000/ws/live?agent_id=kizuna&lang=en');

ws.addEventListener('open', () => {
  console.log('connected');
});

ws.addEventListener('close', (event) => {
  console.log('disconnected', event.code, event.reason);
});

ws.addEventListener('message', (event) => {
  console.log('message', event.data);
});

ws.addEventListener('error', (event) => {
  console.log('error', event.error);
});
