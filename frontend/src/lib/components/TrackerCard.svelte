<script lang="ts">
  import { createEventDispatcher, onDestroy } from 'svelte';
  import type { Tracker } from '../types';
  import RenameModal from './RenameModal.svelte';

  export let tracker: Tracker;

  const dispatch = createEventDispatcher<{
    start: number;
    stop: number;
    delete: number;
    archive: number;
    rename: { id: number; name: string };
    colorChange: { id: number; color: string };
  }>();

  const COLORS = [
    '#6EA1F0', '#F06E6E', '#6EF09A', '#F0BD6E',
    '#BD6EF0', '#6EE8F0', '#F06EBD', '#F0E96E',
  ];

  let showMenu = false;
  let showRename = false;
  let intervalId: ReturnType<typeof setInterval> | null = null;
  let liveSeconds = tracker.today_completed_seconds;

  // Restart the live ticker whenever the tracker's running state changes.
  $: if (tracker.is_running && tracker.running_since) {
    startTicker();
  } else {
    stopTicker();
    liveSeconds = tracker.today_completed_seconds;
  }

  function startTicker() {
    stopTicker();
    const since = new Date(tracker.running_since!).getTime();
    const base = tracker.today_completed_seconds;
    const tick = () => { liveSeconds = base + (Date.now() - since) / 1000; };
    tick();
    intervalId = setInterval(tick, 1000);
  }

  function stopTicker() {
    if (intervalId !== null) {
      clearInterval(intervalId);
      intervalId = null;
    }
  }

  onDestroy(stopTicker);

  function fmt(secs: number): string {
    const h = Math.floor(secs / 3600);
    const m = Math.floor((secs % 3600) / 60);
    const s = Math.floor(secs % 60);
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  }
</script>

<div class="mx-3 my-2 rounded-xl border border-zinc-800 bg-zinc-900 p-4 transition-colors">
  <!-- Top row: name + menu -->
  <div class="flex items-center justify-between mb-3">
    <div class="flex items-center gap-2 min-w-0">
      <span
        class="w-2.5 h-2.5 rounded-full flex-shrink-0 ring-2 ring-offset-2 ring-offset-zinc-900 transition-all"
        style="background:{tracker.color}; ring-color:{tracker.is_running ? tracker.color : 'transparent'}"
      ></span>
      <span class="text-zinc-200 text-sm font-medium truncate">{tracker.name}</span>
    </div>

    <div class="relative">
      <button
        on:click={() => showMenu = !showMenu}
        class="px-2 py-0.5 rounded text-zinc-500 hover:text-zinc-200 hover:bg-zinc-800 transition-colors text-lg leading-none tracking-widest"
      >···</button>

      {#if showMenu}
        <!-- svelte-ignore a11y-click-events-have-key-events a11y-no-static-element-interactions -->
        <div class="fixed inset-0 z-10" on:click={() => showMenu = false}></div>
        <div class="absolute right-0 top-8 z-20 w-44 rounded-xl border border-zinc-700 bg-zinc-900 shadow-2xl py-1 overflow-hidden">
          <button
            on:click={() => { showRename = true; showMenu = false; }}
            class="w-full px-4 py-2 text-left text-sm text-zinc-300 hover:bg-zinc-800 transition-colors"
          >Rename</button>
          <div class="px-4 py-2 border-t border-zinc-800">
            <p class="text-xs text-zinc-600 mb-2">Color</p>
            <div class="flex flex-wrap gap-1.5">
              {#each COLORS as c}
                <button
                  on:click={() => { dispatch('colorChange', { id: tracker.id, color: c }); showMenu = false; }}
                  class="w-5 h-5 rounded-full border-2 transition-all hover:scale-110"
                  style="background:{c}; border-color:{tracker.color === c ? 'white' : 'transparent'}"
                ></button>
              {/each}
            </div>
          </div>
          <div class="border-t border-zinc-800">
            <button
              on:click={() => { dispatch('archive', tracker.id); showMenu = false; }}
              class="w-full px-4 py-2 text-left text-sm text-zinc-400 hover:bg-zinc-800 transition-colors"
            >Archive</button>
            <button
              on:click={() => { dispatch('delete', tracker.id); showMenu = false; }}
              class="w-full px-4 py-2 text-left text-sm text-red-400 hover:bg-zinc-800 transition-colors"
            >Delete</button>
          </div>
        </div>
      {/if}
    </div>
  </div>

  <!-- Timer -->
  <div class="text-center py-2">
    <span
      class="text-4xl font-mono tracking-widest tabular-nums transition-colors"
      style="color:{tracker.is_running ? tracker.color : '#52525b'}"
    >{fmt(liveSeconds)}</span>
  </div>

  <!-- Start/Stop button -->
  <div class="flex justify-center mt-3">
    <button
      on:click={() => tracker.is_running ? dispatch('stop', tracker.id) : dispatch('start', tracker.id)}
      class="flex items-center gap-2 px-8 py-2 rounded-full text-sm font-medium transition-all border"
      style="
        background:{tracker.is_running ? tracker.color + '18' : '#27272a'};
        color:{tracker.is_running ? tracker.color : '#71717a'};
        border-color:{tracker.is_running ? tracker.color + '50' : '#3f3f46'}
      "
    >
      {#if tracker.is_running}
        <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24">
          <rect x="5" y="3" width="5" height="18" rx="1"/>
          <rect x="14" y="3" width="5" height="18" rx="1"/>
        </svg>
        Stop
      {:else}
        <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24">
          <polygon points="5,3 19,12 5,21"/>
        </svg>
        Start
      {/if}
    </button>
  </div>
</div>

{#if showRename}
  <RenameModal
    currentName={tracker.name}
    on:confirm={e => { dispatch('rename', { id: tracker.id, name: e.detail }); showRename = false; }}
    on:cancel={() => showRename = false}
  />
{/if}
