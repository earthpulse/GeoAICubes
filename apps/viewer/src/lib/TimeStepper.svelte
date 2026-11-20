<script>
  /** @type {{ store: import('./types/inventory.ts').ZarrStoreInventory, timeIndex: number, onChange: (index: number) => void }} */
  let { store, timeIndex, onChange } = $props()

  const time = $derived(store.time)
  const show = $derived(
    time != null &&
      (time.count ?? 0) > 1 &&
      ((time.values?.length ?? 0) > 1 || (time.count ?? 0) > 1),
  )

  const maxIndex = $derived(Math.max(0, (time?.count ?? time?.values?.length ?? 1) - 1))

  const label = $derived.by(() => {
    const values = time?.values
    if (values && values[timeIndex]) {
      return values[timeIndex]
    }
    const count = time?.count ?? time?.values?.length ?? 1
    return `Step ${timeIndex + 1} / ${count}`
  })
</script>

{#if show && time}
  <section class="time-stepper" aria-labelledby="time-stepper-heading">
    <h2 id="time-stepper-heading">Time</h2>
    <p class="time-label">{label}</p>
    <div class="controls">
      <button
        type="button"
        disabled={timeIndex <= 0}
        onclick={() => onChange(Math.max(0, timeIndex - 1))}
        aria-label="Previous time step"
      >
        ‹
      </button>
      <input
        type="range"
        min="0"
        max={maxIndex}
        value={timeIndex}
        oninput={(e) => onChange(Number(e.currentTarget.value))}
      />
      <button
        type="button"
        disabled={timeIndex >= maxIndex}
        onclick={() => onChange(Math.min(maxIndex, timeIndex + 1))}
        aria-label="Next time step"
      >
        ›
      </button>
    </div>
  </section>
{/if}

<style>
  .time-stepper {
    margin-top: 0.75rem;
    padding-top: 0.75rem;
    border-top: 1px solid var(--border);
  }

  .time-stepper h2 {
    margin: 0 0 0.35rem;
    font-size: 0.875rem;
    font-weight: 600;
  }

  .time-label {
    margin: 0 0 0.35rem;
    font-size: 0.75rem;
    color: var(--text-muted);
    word-break: break-all;
  }

  .controls {
    display: flex;
    align-items: center;
    gap: 0.35rem;
  }

  .controls button {
    width: 1.75rem;
    height: 1.75rem;
    border: 1px solid var(--border);
    border-radius: 4px;
    background: var(--surface);
    cursor: pointer;
    font-size: 1.1rem;
    line-height: 1;
  }

  .controls button:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  .controls input[type='range'] {
    flex: 1;
  }
</style>