<script>
  /** @type {{ layers: import('./types/inventory.ts').MapLayer[], selectedStoreId: string | null, onSelect: (id: string) => void, onToggle: (layerId: string) => void }} */
  let { layers, selectedStoreId, onSelect, onToggle } = $props()

  /** @param {import('./types/inventory.ts').MapLayer} layer */
  function rowLabel(layer) {
    if (!layer.variable) {
      return layer.storeId
    }
    const sameStore = layers.filter(
      (l) => l.storeId === layer.storeId && l.variable,
    )
    if (sameStore.length > 1) {
      return `${layer.storeId} · ${layer.variable}`
    }
    return layer.storeId
  }

  /** @param {import('./types/inventory.ts').MapLayer} layer */
  function canToggle(layer) {
    return layer.status === 'ok' && Boolean(layer.tileUrlTemplate && layer.variable)
  }

  /** @param {string | null | undefined} err */
  function truncateError(err) {
    if (!err) {
      return ''
    }
    return err.length > 80 ? `${err.slice(0, 77)}…` : err
  }
</script>

<section class="layer-list" aria-labelledby="layer-list-heading">
  <h2 id="layer-list-heading">Layers</h2>
  {#if layers.length === 0}
    <p class="empty">No stores in inventory.</p>
  {:else}
    <ul class="rows">
      {#each layers as layer (layer.layerId)}
        <li
          class:selected={layer.storeId === selectedStoreId}
          class:placeholder={!layer.variable}
        >
          <button
            type="button"
            class="row-main"
            onclick={() => onSelect(layer.storeId)}
          >
            <span class="row-label">{rowLabel(layer)}</span>
            <span class="badge" class:error={layer.status === 'error'}>
              {layer.status}
            </span>
          </button>
          {#if layer.variable}
            <label class="vis-toggle" title="Toggle map overlay">
              <input
                type="checkbox"
                checked={layer.visible}
                disabled={!canToggle(layer)}
                onchange={() => onToggle(layer.layerId)}
              />
              <span class="sr-only">Show {layer.variable}</span>
            </label>
          {/if}
          {#if layer.status === 'error' && layer.store.error}
            <p class="row-error" title={layer.store.error}>
              {truncateError(layer.store.error)}
            </p>
          {/if}
        </li>
      {/each}
    </ul>
  {/if}
</section>

<style>
  .layer-list h2 {
    margin: 0 0 0.5rem;
    font-size: 0.9375rem;
    font-weight: 600;
    color: var(--text-h);
  }

  .empty {
    margin: 0;
    font-size: 0.875rem;
    color: var(--text-muted);
  }

  .rows {
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
    max-height: 220px;
    overflow-y: auto;
  }

  li {
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 0.35rem 0.5rem;
    background: var(--bg);
  }

  li.selected {
    border-color: var(--accent);
    box-shadow: 0 0 0 1px color-mix(in srgb, var(--accent) 35%, transparent);
  }

  li.placeholder {
    opacity: 0.95;
  }

  .row-main {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
    width: 100%;
    padding: 0;
    border: none;
    background: none;
    font: inherit;
    text-align: left;
    cursor: pointer;
    color: var(--text);
  }

  .row-label {
    font-size: 0.8125rem;
    word-break: break-all;
    flex: 1;
  }

  .badge {
    font-size: 0.6875rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    padding: 0.1rem 0.35rem;
    border-radius: 4px;
    background: #e2e8f0;
    color: #334155;
    flex-shrink: 0;
  }

  .badge.error {
    background: #fee2e2;
    color: var(--error);
  }

  .vis-toggle {
    display: inline-flex;
    margin-top: 0.25rem;
    cursor: pointer;
  }

  .vis-toggle input:disabled {
    cursor: not-allowed;
  }

  .row-error {
    margin: 0.25rem 0 0;
    font-size: 0.75rem;
    color: var(--error);
    line-height: 1.3;
  }

  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    border: 0;
  }
</style>