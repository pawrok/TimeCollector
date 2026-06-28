<script lang="ts">
  import { createEventDispatcher } from 'svelte';

  const dispatch = createEventDispatcher<{ create: string }>();

  let name = '';
  let inputEl: HTMLInputElement;

  function submit() {
    const trimmed = name.trim();
    if (!trimmed) return;
    dispatch('create', trimmed);
    name = '';
    inputEl?.focus();
  }
</script>

<div class="flex items-center gap-2">
  <input
    bind:this={inputEl}
    bind:value={name}
    on:keydown={e => e.key === 'Enter' && submit()}
    placeholder="New tracker name..."
    class="flex-1 bg-transparent border-b border-zinc-800 focus:border-zinc-500 outline-none text-sm text-zinc-300 placeholder-zinc-600 py-1.5 transition-colors"
  />
  <button
    on:click={submit}
    disabled={!name.trim()}
    class="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-800 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
    title="Add tracker"
  >
    <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
    </svg>
  </button>
</div>
