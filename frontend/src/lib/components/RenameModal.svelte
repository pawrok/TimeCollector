<script lang="ts">
  import { createEventDispatcher, onMount } from 'svelte';

  export let currentName: string;

  const dispatch = createEventDispatcher<{ confirm: string; cancel: void }>();

  let value = currentName;
  let input: HTMLInputElement;

  onMount(() => {
    input?.focus();
    input?.select();
  });

  function submit() {
    const trimmed = value.trim();
    if (trimmed) dispatch('confirm', trimmed);
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter') submit();
    if (e.key === 'Escape') dispatch('cancel');
  }
</script>

<!-- svelte-ignore a11y-click-events-have-key-events a11y-no-static-element-interactions -->
<div
  class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
  on:click={e => e.target === e.currentTarget && dispatch('cancel')}
>
  <div class="bg-zinc-900 border border-zinc-700 rounded-xl p-6 w-72 shadow-2xl">
    <h2 class="text-xs font-semibold text-zinc-500 mb-3 uppercase tracking-widest">Rename tracker</h2>
    <input
      bind:this={input}
      bind:value
      on:keydown={handleKeydown}
      class="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-white text-sm outline-none focus:border-zinc-500 transition-colors"
      placeholder="Tracker name..."
    />
    <div class="flex gap-2 mt-4">
      <button
        on:click={submit}
        class="flex-1 py-2 rounded-lg text-sm font-medium bg-zinc-700 hover:bg-zinc-600 text-white transition-colors"
      >
        Apply
      </button>
      <button
        on:click={() => dispatch('cancel')}
        class="flex-1 py-2 rounded-lg text-sm bg-zinc-800 hover:bg-zinc-700 text-zinc-400 transition-colors"
      >
        Cancel
      </button>
    </div>
  </div>
</div>
