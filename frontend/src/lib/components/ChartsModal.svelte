<script lang="ts">
  import { createEventDispatcher, onMount, onDestroy, tick } from 'svelte';
  import { Chart, registerables } from 'chart.js';
  import type { DailyStat, TotalStat } from '../types';
  import { api } from '../api';

  Chart.register(...registerables);

  const dispatch = createEventDispatcher<{ close: void }>();

  type View = 'last30' | 'month' | 'year' | 'alltime';

  const now = new Date();
  let view: View = 'last30';
  let selYear = now.getFullYear();
  let selMonth = now.getMonth(); // 0-based

  // Canvases are always in the DOM so bind:this never goes stale.
  let mainCanvas: HTMLCanvasElement;
  let donutCanvas: HTMLCanvasElement;
  let mainChart: Chart | null = null;
  let donutChart: Chart | null = null;

  let loading = true;
  let empty = false;
  let allTimeTotals: TotalStat[] = [];
  let loadGen = 0; // incremented on every load(); stale results are discarded

  const MONTHS_SHORT = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  const MONTHS_LONG  = ['January','February','March','April','May','June',
                        'July','August','September','October','November','December'];

  const GRID  = '#27272a';
  const TICK  = '#71717a';
  const LEG   = '#a1a1aa';
  const TITLE = '#d4d4d8';

  function pad(n: number) { return String(n).padStart(2, '0'); }

  function allDaysOfMonth(y: number, m: number): string[] {
    const last = new Date(y, m + 1, 0).getDate();
    return Array.from({ length: last }, (_, i) => `${y}-${pad(m + 1)}-${pad(i + 1)}`);
  }

  function destroyCharts() {
    mainChart?.destroy(); mainChart = null;
    donutChart?.destroy(); donutChart = null;
  }

  async function load() {
    const gen = ++loadGen;
    loading = true;
    empty = false;
    destroyCharts();

    try {
      if (view === 'last30') {
        const from = new Date();
        from.setDate(from.getDate() - 30);
        const [daily, totals] = await Promise.all([
          api.getDailyStats({ from: from.toISOString().slice(0, 10) }),
          api.getTotalStats(),
        ]);
        if (gen !== loadGen) return;
        empty = daily.length === 0;
        loading = false;
        await tick();
        if (!empty) {
          buildLine(daily, 'Daily hours — last 30 days',
            [...new Set(daily.map(d => d.date))].sort(), d => d.slice(5));
          const donutData = totals.filter(t => t.seconds > 0);
          if (donutData.length) buildDonut(donutData, 'Total hours by tracker');
        }

      } else if (view === 'month') {
        const from = `${selYear}-${pad(selMonth + 1)}-01`;
        const to   = new Date(selYear, selMonth + 1, 0).toISOString().slice(0, 10);
        const daily = await api.getDailyStats({ from, to });
        if (gen !== loadGen) return;
        const activeIds = new Set(daily.filter(d => d.seconds > 0).map(d => d.tracker_id));
        const filtered = daily.filter(d => activeIds.has(d.tracker_id));
        empty = filtered.length === 0;
        loading = false;
        await tick();
        if (!empty) {
          buildLine(filtered, `${MONTHS_LONG[selMonth]} ${selYear} — daily hours`,
            allDaysOfMonth(selYear, selMonth), d => String(parseInt(d.slice(8))));
          buildMonthDonut(filtered);
        }

      } else if (view === 'year') {
        const daily = await api.getDailyStats({ from: `${selYear}-01-01`, to: `${selYear}-12-31` });
        if (gen !== loadGen) return;
        empty = daily.length === 0;
        loading = false;
        await tick();
        if (!empty) buildYearBar(daily);

      } else {
        const totals = (await api.getTotalStats()).filter(t => t.seconds > 0);
        if (gen !== loadGen) return;
        allTimeTotals = totals.sort((a, b) => b.seconds - a.seconds);
        empty = allTimeTotals.length === 0;
        loading = false;
      }
    } catch {
      if (gen === loadGen) { loading = false; empty = true; }
    }
  }

  onMount(() => load());
  onDestroy(destroyCharts);

  // ── Chart builders ──────────────────────────────────────────────────

  function buildLine(
    data: DailyStat[],
    title: string,
    allDates: string[],
    labelFn: (d: string) => string,
  ) {
    const trackerIds = [...new Set(data.map(d => d.tracker_id))];
    const datasets = trackerIds.map(tid => {
      const pts = data.filter(d => d.tracker_id === tid);
      const map: Record<string, number> = {};
      pts.forEach(d => (map[d.date] = d.seconds / 3600));
      return {
        label: pts[0]?.tracker_name,
        data: allDates.map(d => +(map[d] ?? 0).toFixed(3)),
        borderColor: pts[0]?.color,
        backgroundColor: (pts[0]?.color ?? '#6EA1F0') + '20',
        tension: 0.3,
        fill: false,
        pointRadius: 2,
        pointHoverRadius: 5,
      };
    });
    mainChart = new Chart(mainCanvas, {
      type: 'line',
      data: { labels: allDates.map(labelFn), datasets },
      options: {
        responsive: true,
        plugins: {
          legend: { labels: { color: LEG, boxWidth: 12 } },
          title:  { display: true, text: title, color: TITLE },
          tooltip: { callbacks: { label: ctx => ` ${ctx.dataset.label}: ${(ctx.parsed.y as number).toFixed(2)}h` } },
        },
        scales: {
          x: { ticks: { color: TICK }, grid: { color: GRID } },
          y: { min: 0, ticks: { color: TICK }, grid: { color: GRID } },
        },
      },
    });
  }

  function buildDonut(data: { tracker_name: string; color: string; seconds: number }[], title: string) {
    donutChart = new Chart(donutCanvas, {
      type: 'doughnut',
      data: {
        labels: data.map(d => d.tracker_name),
        datasets: [{
          data: data.map(d => +(d.seconds / 3600).toFixed(2)),
          backgroundColor: data.map(d => d.color),
          borderColor: '#09090b',
          borderWidth: 3,
        }],
      },
      options: {
        responsive: true,
        plugins: {
          legend: { labels: { color: LEG, boxWidth: 12 } },
          title:  { display: true, text: title, color: TITLE },
          tooltip: { callbacks: { label: ctx => ` ${ctx.label}: ${(ctx.parsed as number).toFixed(1)}h` } },
        },
        cutout: '55%',
      },
    });
  }

  function buildMonthDonut(data: DailyStat[]) {
    const byTracker: Record<number, { tracker_name: string; color: string; seconds: number }> = {};
    data.forEach(d => {
      byTracker[d.tracker_id] ??= { tracker_name: d.tracker_name, color: d.color, seconds: 0 };
      byTracker[d.tracker_id].seconds += d.seconds;
    });
    buildDonut(Object.values(byTracker).filter(e => e.seconds > 0), `${MONTHS_LONG[selMonth]} breakdown`);
  }

  function buildYearBar(data: DailyStat[]) {
    const trackerMap: Record<number, { name: string; color: string; months: number[] }> = {};
    data.forEach(d => {
      trackerMap[d.tracker_id] ??= { name: d.tracker_name, color: d.color, months: new Array(12).fill(0) };
      trackerMap[d.tracker_id].months[parseInt(d.date.slice(5, 7)) - 1] += d.seconds / 3600;
    });
    const upToMonth = selYear === now.getFullYear() ? now.getMonth() : 11;
    mainChart = new Chart(mainCanvas, {
      type: 'bar',
      data: {
        labels: MONTHS_SHORT.slice(0, upToMonth + 1),
        datasets: Object.values(trackerMap).map(t => ({
          label: t.name,
          data: t.months.slice(0, upToMonth + 1).map(h => +h.toFixed(2)),
          backgroundColor: t.color + 'CC',
          borderColor: t.color,
          borderWidth: 1,
        })),
      },
      options: {
        responsive: true,
        plugins: {
          legend: { labels: { color: LEG, boxWidth: 12 } },
          title:  { display: true, text: `${selYear} — hours by month`, color: TITLE },
          tooltip: { callbacks: { label: ctx => ` ${ctx.dataset.label}: ${(ctx.parsed.y as number).toFixed(1)}h` } },
        },
        scales: {
          x: { stacked: true, ticks: { color: TICK }, grid: { color: GRID } },
          y: { stacked: true, min: 0, ticks: { color: TICK }, grid: { color: GRID } },
        },
      },
    });
  }

  // ── Navigation ───────────────────────────────────────────────────────

  function prevMonth() {
    if (selMonth === 0) { selMonth = 11; selYear--; } else selMonth--;
    load();
  }
  function nextMonth() {
    if (selYear === now.getFullYear() && selMonth === now.getMonth()) return;
    if (selMonth === 11) { selMonth = 0; selYear++; } else selMonth++;
    load();
  }
  function prevYear() { selYear--; load(); }
  function nextYear() {
    if (selYear < now.getFullYear()) { selYear++; load(); }
  }

  // $: so Svelte tracks selYear/selMonth as dependencies and updates the disabled attributes.
  $: isAtCurrentMonth = selYear === now.getFullYear() && selMonth === now.getMonth();
  $: isAtCurrentYear  = selYear === now.getFullYear();

  function switchView(v: View) { view = v; load(); }

  const VIEWS: { key: View; label: string }[] = [
    { key: 'last30',  label: 'Last 30d' },
    { key: 'month',   label: 'Month' },
    { key: 'year',    label: 'Year' },
    { key: 'alltime', label: 'All time' },
  ];

  $: maxSec = allTimeTotals[0]?.seconds ?? 1;
</script>

<!-- svelte-ignore a11y-click-events-have-key-events a11y-no-static-element-interactions -->
<div
  class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm"
  on:click={e => e.target === e.currentTarget && dispatch('close')}
>
  <div class="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 w-full max-w-2xl mx-4 shadow-2xl max-h-[90vh] flex flex-col gap-4">

    <!-- Header -->
    <div class="flex items-center justify-between">
      <h2 class="text-xs font-semibold text-zinc-500 uppercase tracking-widest">Statistics</h2>
      <div class="flex items-center gap-3">
        <a href="/api/export/excel" class="text-xs text-zinc-500 hover:text-zinc-300 transition-colors" download>xlsx</a>
        <a href="/api/export/csv"   class="text-xs text-zinc-500 hover:text-zinc-300 transition-colors" download>csv</a>
        <button on:click={() => dispatch('close')} class="p-1 rounded-lg hover:bg-zinc-800 text-zinc-500 hover:text-zinc-300 transition-colors">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- Tabs -->
    <div class="flex gap-1 bg-zinc-800/50 rounded-lg p-1 text-xs">
      {#each VIEWS as { key, label }}
        <button
          on:click={() => switchView(key)}
          class="flex-1 py-1.5 rounded-md font-medium transition-colors"
          class:bg-zinc-700={view === key}
          class:text-white={view === key}
          class:text-zinc-500={view !== key}
          class:hover:text-zinc-300={view !== key}
        >{label}</button>
      {/each}
    </div>

    <!-- Period controls -->
    {#if view === 'month'}
      <div class="flex items-center justify-center gap-4">
        <button on:click={prevMonth} class="p-1 rounded hover:bg-zinc-800 text-zinc-400 hover:text-white transition-colors">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7"/></svg>
        </button>
        <span class="text-sm text-zinc-300 w-36 text-center">{MONTHS_LONG[selMonth]} {selYear}</span>
        <button on:click={nextMonth} disabled={isAtCurrentMonth} class="p-1 rounded hover:bg-zinc-800 text-zinc-400 hover:text-white transition-colors disabled:opacity-30 disabled:cursor-not-allowed">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7"/></svg>
        </button>
      </div>
    {:else if view === 'year'}
      <div class="flex items-center justify-center gap-4">
        <button on:click={prevYear} class="p-1 rounded hover:bg-zinc-800 text-zinc-400 hover:text-white transition-colors">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7"/></svg>
        </button>
        <span class="text-sm text-zinc-300 w-20 text-center">{selYear}</span>
        <button on:click={nextYear} disabled={isAtCurrentYear} class="p-1 rounded hover:bg-zinc-800 text-zinc-400 hover:text-white transition-colors disabled:opacity-30 disabled:cursor-not-allowed">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7"/></svg>
        </button>
      </div>
    {/if}

    <!-- Content -->
    <div class="overflow-y-auto flex-1 space-y-6">
      {#if loading}
        <div class="flex items-center justify-center h-48 text-zinc-600 text-sm">Loading…</div>
      {:else if empty}
        <div class="flex flex-col items-center justify-center h-48 text-zinc-600 text-sm gap-2">
          <svg class="w-8 h-8 opacity-40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
          </svg>
          No tracked time for this period.
        </div>
      {/if}

      <!-- Canvases: always in DOM so bind:this is always valid -->
      <canvas
        bind:this={mainCanvas}
        style:display={loading || empty || view === 'alltime' ? 'none' : 'block'}
      ></canvas>
      <canvas
        bind:this={donutCanvas}
        class="max-h-64 mx-auto"
        style:display={loading || empty || view === 'year' || view === 'alltime' ? 'none' : 'block'}
      ></canvas>

      <!-- All-time raw table -->
      {#if !loading && !empty && view === 'alltime'}
        <div class="space-y-3">
          {#each allTimeTotals as t}
            <div class="flex items-center gap-3">
              <span class="w-2.5 h-2.5 rounded-full flex-shrink-0" style="background:{t.color}"></span>
              <span class="w-28 text-sm text-zinc-300 truncate flex-shrink-0">{t.tracker_name}</span>
              <div class="flex-1 h-1.5 rounded-full bg-zinc-800">
                <div class="h-1.5 rounded-full transition-all" style="width:{(t.seconds / maxSec) * 100}%; background:{t.color}"></div>
              </div>
              <span class="text-sm text-zinc-400 w-16 text-right flex-shrink-0 tabular-nums">{(t.seconds / 3600).toFixed(1)} h</span>
            </div>
          {/each}
        </div>
      {/if}
    </div>

  </div>
</div>
