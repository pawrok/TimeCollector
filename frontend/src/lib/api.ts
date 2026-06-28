import type { Tracker, DailyStat, TotalStat, TrackerCreate, TrackerUpdate } from './types';

const BASE = '/api';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  getTrackers: () => request<Tracker[]>('/trackers'),

  createTracker: (data: TrackerCreate) =>
    request<Tracker>('/trackers', { method: 'POST', body: JSON.stringify(data) }),

  updateTracker: (id: number, data: TrackerUpdate) =>
    request<Tracker>(`/trackers/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),

  deleteTracker: (id: number) =>
    request<void>(`/trackers/${id}`, { method: 'DELETE' }),

  startTracker: (id: number) =>
    request<Tracker>(`/trackers/${id}/start`, { method: 'POST' }),

  stopTracker: (id: number) =>
    request<Tracker>(`/trackers/${id}/stop`, { method: 'POST' }),

  stopAll: () =>
    request<void>('/trackers/stop-all', { method: 'POST' }),

  getDailyStats: (params?: { from?: string; to?: string }) => {
    const q = new URLSearchParams();
    if (params?.from) q.set('from_date', params.from);
    if (params?.to) q.set('to_date', params.to);
    return request<DailyStat[]>(`/stats/daily?${q}`);
  },

  getTotalStats: () => request<TotalStat[]>('/stats/totals'),
};
