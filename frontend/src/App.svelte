<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from './lib/api';
  import { initWebSocket } from './lib/ws';
  import TrackerCard from './lib/components/TrackerCard.svelte';
  import NewTrackerInput from './lib/components/NewTrackerInput.svelte';
  import ChartsModal from './lib/components/ChartsModal.svelte';
  import type { Tracker } from './lib/types';

  let trackers: Tracker[] = [];
  let loading = true;
  let showCharts = false;

  onMount(async () => {
    initWebSocket({ onReconnect: refresh });
    trackers = await api.getTrackers();
    loading = false;
  });

  async function refresh() {
    trackers = await api.getTrackers();
  }

  async function handleCreate(e: CustomEvent<string>) {
    const tracker = await api.createTracker({ name: e.detail });
    trackers = [...trackers, tracker];
  }

  async function handleStart(e: CustomEvent<number>) {
    const id = e.detail;
    const now = new Date().toISOString();
    // Optimistic update: mark all stopped, target running
    trackers = trackers.map(t => ({
      ...t,
      is_running: t.id === id,
      running_since: t.id === id ? now : null,
      // preserve today_completed_seconds for stopped ones
      today_completed_seconds:
        t.id !== id && t.is_running
          ? t.today_completed_seconds + (Date.now() - new Date(t.running_since!).getTime()) / 1000
          : t.today_completed_seconds,
    }));
    try {
      const updated = await api.startTracker(id);
      trackers = trackers.map(t => (t.id === id ? updated : t));
    } catch {
      await refresh();
    }
  }

  async function handleStop(e: CustomEvent<number>) {
    const id = e.detail;
    trackers = trackers.map(t =>
      t.id === id ? { ...t, is_running: false, running_since: null } : t
    );
    try {
      const updated = await api.stopTracker(id);
      trackers = trackers.map(t => (t.id === id ? updated : t));
    } catch {
      await refresh();
    }
  }

  async function handleDelete(e: CustomEvent<number>) {
    const id = e.detail;
    trackers = trackers.filter(t => t.id !== id);
    await api.deleteTracker(id);
  }

  async function handleArchive(e: CustomEvent<number>) {
    const id = e.detail;
    trackers = trackers.filter(t => t.id !== id);
    await api.updateTracker(id, { archived: true });
  }

  async function handleRename(e: CustomEvent<{ id: number; name: string }>) {
    const { id, name } = e.detail;
    const updated = await api.updateTracker(id, { name });
    trackers = trackers.map(t => (t.id === id ? { ...t, name: updated.name } : t));
  }

  async function handleColorChange(e: CustomEvent<{ id: number; color: string }>) {
    const { id, color } = e.detail;
    const updated = await api.updateTracker(id, { color });
    trackers = trackers.map(t => (t.id === id ? { ...t, color: updated.color } : t));
  }
</script>

<div class="flex flex-col h-dvh max-w-sm mx-auto select-none">
  <!-- Header -->
  <header class="flex items-center justify-between px-4 py-3 border-b border-zinc-800">
    <h1 class="text-base font-light tracking-[0.25em] text-zinc-400 uppercase">Time Collector</h1>
    <button
      on:click={() => showCharts = true}
      class="p-1.5 rounded-lg hover:bg-zinc-800 text-zinc-500 hover:text-zinc-300 transition-colors"
      title="View charts"
    >
      <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round"
          d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
      </svg>
    </button>
  </header>

  <!-- Tracker list -->
  <main class="flex-1 overflow-y-auto py-1">
    {#if loading}
      <div class="flex items-center justify-center h-32 text-zinc-600 text-sm">Loading…</div>
    {:else if trackers.length === 0}
      <div class="flex flex-col items-center justify-center h-32 gap-2 text-zinc-600 text-sm">
        <svg class="w-8 h-8 opacity-40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <circle cx="12" cy="12" r="10" stroke-width="1.5"/>
          <path stroke-linecap="round" stroke-width="1.5" d="M12 6v6l4 2"/>
        </svg>
        Add a tracker below to get started.
      </div>
    {:else}
      {#each trackers as tracker (tracker.id)}
        <TrackerCard
          {tracker}
          on:start={handleStart}
          on:stop={handleStop}
          on:delete={handleDelete}
          on:archive={handleArchive}
          on:rename={handleRename}
          on:colorChange={handleColorChange}
        />
      {/each}
    {/if}
  </main>

  <!-- Footer input -->
  <footer class="border-t border-zinc-800 px-4 py-3">
    <NewTrackerInput on:create={handleCreate} />
  </footer>
</div>

{#if showCharts}
  <ChartsModal on:close={() => showCharts = false} />
{/if}
