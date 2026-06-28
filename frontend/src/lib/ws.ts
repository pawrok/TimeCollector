// Reconnect delays (ms): 2s, 4s, 8s, 16s, 30s, 30s, …
const BACKOFF = [2_000, 4_000, 8_000, 16_000, 30_000];

let ws: WebSocket | null = null;
let heartbeatId: ReturnType<typeof setInterval> | null = null;
let reconnectId: ReturnType<typeof setTimeout> | null = null;
let attempt = 0;
let destroyed = false;

type OnReconnect = () => void;
let onReconnect: OnReconnect | null = null;

function wsUrl(): string {
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${proto}//${location.host}/ws`;
}

function connect() {
  if (destroyed) return;
  ws = new WebSocket(wsUrl());

  ws.onopen = () => {
    attempt = 0; // reset backoff on successful connection
    heartbeatId = setInterval(() => {
      if (ws?.readyState === WebSocket.OPEN) ws.send('ping');
    }, 25_000);
    if (onReconnect) onReconnect(); // refresh tracker state
  };

  ws.onclose = () => {
    if (heartbeatId !== null) { clearInterval(heartbeatId); heartbeatId = null; }
    if (destroyed) return;
    const delay = BACKOFF[Math.min(attempt, BACKOFF.length - 1)];
    attempt++;
    reconnectId = setTimeout(connect, delay);
  };
}

export function initWebSocket(callbacks: { onReconnect: OnReconnect }) {
  onReconnect = callbacks.onReconnect;
  connect();
}

export function closeWebSocket() {
  destroyed = true;
  if (reconnectId !== null) { clearTimeout(reconnectId); reconnectId = null; }
  if (heartbeatId !== null) { clearInterval(heartbeatId); heartbeatId = null; }
  ws?.close();
  ws = null;
}
