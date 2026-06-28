// Reconnect delays (ms): 2s, 4s, 8s, 16s, 30s, 30s, …
const BACKOFF = [2_000, 4_000, 8_000, 16_000, 30_000];

let ws: WebSocket | null = null;
let heartbeatId: ReturnType<typeof setInterval> | null = null;
let reconnectId: ReturnType<typeof setTimeout> | null = null;
let attempt = 0;
let destroyed = false;
let suspended = false; // true while page is hidden; suppresses auto-reconnect

type OnReconnect = () => void;
let onReconnect: OnReconnect | null = null;

function wsUrl(): string {
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${proto}//${location.host}/ws`;
}

function connect() {
  if (destroyed || suspended) return;
  ws = new WebSocket(wsUrl());

  ws.onopen = () => {
    attempt = 0;
    heartbeatId = setInterval(() => {
      if (ws?.readyState === WebSocket.OPEN) ws.send('ping');
    }, 25_000);
    if (onReconnect) onReconnect();
  };

  ws.onclose = () => {
    if (heartbeatId !== null) { clearInterval(heartbeatId); heartbeatId = null; }
    if (destroyed || suspended) return;
    const delay = BACKOFF[Math.min(attempt, BACKOFF.length - 1)];
    attempt++;
    reconnectId = setTimeout(connect, delay);
  };
}

function goBackground() {
  // Tell the server this is a deliberate background disconnect (screen off,
  // tab hidden) so it uses the long grace period instead of the short one.
  if (ws?.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'going_background' }));
  }
  suspended = true;
  if (reconnectId !== null) { clearTimeout(reconnectId); reconnectId = null; }
  if (heartbeatId !== null) { clearInterval(heartbeatId); heartbeatId = null; }
  ws?.close();
  ws = null;
}

function resume() {
  if (destroyed) return;
  suspended = false;
  attempt = 0; // reconnect immediately, no backoff delay
  connect();
}

export function initWebSocket(callbacks: { onReconnect: OnReconnect }) {
  onReconnect = callbacks.onReconnect;

  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      goBackground();
    } else {
      resume();
    }
  });

  connect();
}

export function closeWebSocket() {
  destroyed = true;
  if (reconnectId !== null) { clearTimeout(reconnectId); reconnectId = null; }
  if (heartbeatId !== null) { clearInterval(heartbeatId); heartbeatId = null; }
  ws?.close();
  ws = null;
}
