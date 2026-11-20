<script>
  /** @type {{ store: import('./types/inventory.ts').ZarrStoreInventory | null }} */
  let { store } = $props()

  /** @param {string} name */
  function hasTile(name) {
    if (!store) {
      return false
    }
    return Object.prototype.hasOwnProperty.call(store.tile_url_template, name)
  }
</script>

<section class="metadata" aria-labelledby="metadata-heading">
  <h2 id="metadata-heading">Metadata</h2>
  {#if !store}
    <p class="empty">Select a store from the layer list.</p>
  {:else}
    {#if store.status === 'error' && store.error}
      <div class="alert" role="alert">{store.error}</div>
    {/if}

    <dl class="fields">
      <div class="field">
        <dt>Status</dt>
        <dd>
          <span class="badge" class:error={store.status === 'error'}>{store.status}</span>
        </dd>
      </div>
      <div class="field">
        <dt>URI</dt>
        <dd><code>{store.uri}</code></dd>
      </div>
      <div class="field">
        <dt>Path</dt>
        <dd><code>{store.path}</code></dd>
      </div>
      <div class="field">
        <dt>CRS</dt>
        <dd>
          {#if store.crs}
            {store.crs}
          {:else}
            <span class="warn">Unknown CRS</span>
          {/if}
        </dd>
      </div>
      <div class="field">
        <dt>Extent</dt>
        <dd>
          {#if store.extent}
            <code
              >[{store.extent.bbox.join(', ')}] ({store.extent.crs})</code
            >
          {:else}
            <span class="warn">Cannot fit map to this store (extent missing)</span>
          {/if}
        </dd>
      </div>
      {#if store.time}
        <div class="field">
          <dt>Time</dt>
          <dd>
            dim <code>{store.time.dim}</code>
            {#if store.time.count != null}
              · count {store.time.count}
            {/if}
            {#if store.time.start}
              · {store.time.start} → {store.time.end ?? '…'}
            {/if}
          </dd>
        </div>
      {/if}
    </dl>

    {#if store.variables.length > 0}
      <h3 class="subhead">Variables</h3>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>dtype</th>
              <th>shape</th>
              <th>Tiles</th>
            </tr>
          </thead>
          <tbody>
            {#each store.variables as v (v.name)}
              <tr>
                <td>{v.name}</td>
                <td>{v.dtype}</td>
                <td>{v.shape.join('×')}</td>
                <td>
                  {#if hasTile(v.name)}
                    ok
                  {:else}
                    <span class="warn">no tile preview</span>
                  {/if}
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}

    <details class="advanced">
      <summary>Advanced</summary>
      <pre class="json-chunks">{JSON.stringify(
          { dims: store.dims, chunks: store.chunks, nodata: store.nodata },
          null,
          2,
        )}</pre>
    </details>
  {/if}
</section>

<style>
  .metadata h2 {
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

  .alert {
    margin: 0 0 0.75rem;
    padding: 0.5rem 0.65rem;
    font-size: 0.8125rem;
    line-height: 1.4;
    background: #fef2f2;
    border: 1px solid #fecaca;
    border-radius: 6px;
    color: var(--error);
  }

  .fields {
    margin: 0;
    display: grid;
    gap: 0.45rem;
  }

  .field {
    display: grid;
    grid-template-columns: 4.5rem 1fr;
    gap: 0.35rem;
    font-size: 0.8125rem;
  }

  dt {
    margin: 0;
    color: var(--text-muted);
  }

  dd {
    margin: 0;
    word-break: break-word;
  }

  code {
    font-size: 0.75rem;
    font-family: ui-monospace, Consolas, monospace;
    background: var(--bg);
    padding: 0.1rem 0.25rem;
    border-radius: 3px;
  }

  .badge {
    font-size: 0.75rem;
    text-transform: uppercase;
  }

  .badge.error {
    color: var(--error);
  }

  .warn {
    color: #b45309;
    font-size: 0.8125rem;
  }

  .subhead {
    margin: 0.75rem 0 0.35rem;
    font-size: 0.8125rem;
    font-weight: 600;
  }

  .table-wrap {
    overflow-x: auto;
  }

  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.75rem;
  }

  th,
  td {
    border: 1px solid var(--border);
    padding: 0.25rem 0.35rem;
    text-align: left;
  }

  th {
    background: var(--bg);
    font-weight: 600;
  }

  .advanced {
    margin-top: 0.75rem;
    font-size: 0.8125rem;
  }

  .json-chunks {
    margin: 0.5rem 0 0;
    padding: 0.5rem;
    font-size: 0.6875rem;
    background: #0f172a;
    color: #e2e8f0;
    border-radius: 6px;
    overflow-x: auto;
    max-height: 140px;
  }

</style>