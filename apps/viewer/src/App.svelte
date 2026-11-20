<script>
  import { onMount, tick } from 'svelte'
  import { normalizeApiBase, fetchHealth } from './lib/api/client.ts'
  import { createInventoryState } from './lib/state/inventory.svelte.ts'
  import LayerList from './lib/LayerList.svelte'
  import MetadataPanel from './lib/MetadataPanel.svelte'
  import TimeStepper from './lib/TimeStepper.svelte'
  import VisualizationPanel from './lib/VisualizationPanel.svelte'
  import MapView from './lib/MapView.svelte'

  const apiBase = normalizeApiBase(import.meta.env.VITE_API_BASE_URL)
  const inv = createInventoryState(apiBase)

  let health = $state(null)
  let healthError = $state(null)
  let healthLoading = $state(true)
  let fitRequest = $state(0)
  let fitMode = $state(/** @type {'selected' | 'visible'} */ ('selected'))
  let didInitialFit = $state(false)

  const inventoryStatusLabel = $derived.by(() => {
    if (inv.inventoryLoading) {
      return 'Loading inventory…'
    }
    if (inv.inventoryError) {
      return 'Inventory failed'
    }
    const ok = inv.stores.filter((s) => s.status === 'ok').length
    const err = inv.stores.filter((s) => s.status === 'error').length
    return `${inv.stores.length} stores (${ok} ok, ${err} error)`
  })

  onMount(async () => {
    try {
      health = await fetchHealth(apiBase)
    } catch (e) {
      healthError = e instanceof Error ? e.message : String(e)
    } finally {
      healthLoading = false
    }
    await inv.loadInventory()
    await tick()
    if (!didInitialFit) {
      const firstOk = inv.stores.find((s) => s.status === 'ok' && s.extent)
      if (firstOk?.extent) {
        inv.selectStore(firstOk.id)
        fitMode = 'selected'
        fitRequest += 1
        didInitialFit = true
      }
    }
  })

  function requestFit(mode) {
    fitMode = mode
    fitRequest += 1
  }

  function selectedTimeIndex() {
    if (!inv.selectedStoreId) {
      return 0
    }
    return inv.timeIndexByStore[inv.selectedStoreId] ?? 0
  }

  function onTimeChange(index) {
    if (!inv.selectedStoreId) {
      return
    }
    inv.setTimeIndex(inv.selectedStoreId, index)
  }

  const canFitSelected = $derived(Boolean(inv.selectedStore?.extent))
  const canFitVisible = $derived(
    inv.mapLayers.some((l) => l.visible && l.store.extent),
  )
</script>

<div class="shell">
  <header class="header">
    <div class="header-titles">
      <h1>GeoAICubes Viewer</h1>
      <p class="tagline">Zarr discovery — map layers via API only</p>
    </div>
    <div class="header-meta">
      <p class="api-url">
        <span class="label">API</span>
        <code>{apiBase}</code>
      </p>
      <p class="status-line">
        <span class="pill" class:error={Boolean(healthError)}>
          {#if healthLoading}
            Health…
          {:else if healthError}
            API unreachable
          {:else}
            API ok
          {/if}
        </span>
        <span class="pill" class:error={Boolean(inv.inventoryError)}>
          {inventoryStatusLabel}
        </span>
      </p>
    </div>
  </header>

  {#if inv.inventoryError}
    <div class="banner error" role="alert">
      Inventory request failed: {inv.inventoryError}
    </div>
  {/if}

  <main class="main">
    <aside class="sidebar">
      <LayerList
        layers={inv.mapLayers}
        selectedStoreId={inv.selectedStoreId}
        onSelect={(id) => inv.selectStore(id)}
        onToggle={(layerId) => inv.toggleLayerVisibility(layerId)}
      />
      {#if inv.selectedStore}
        <TimeStepper
          store={inv.selectedStore}
          timeIndex={selectedTimeIndex()}
          onChange={onTimeChange}
        />
        <VisualizationPanel
          store={inv.selectedStore}
          layers={inv.mapLayers}
          onRenderChange={(layerId, state) => inv.setLayerRenderState(layerId, state)}
        />
      {/if}
      <MetadataPanel store={inv.selectedStore} />
    </aside>

    <div class="map-column">
      <div class="map-toolbar">
        <button
          type="button"
          disabled={!canFitSelected}
          onclick={() => requestFit('selected')}
        >
          Fit extent (selected)
        </button>
        <button
          type="button"
          disabled={!canFitVisible}
          onclick={() => requestFit('visible')}
        >
          Fit visible
        </button>
      </div>
      <MapView
        {apiBase}
        layers={inv.mapLayers}
        selectedStore={inv.selectedStore}
        {fitRequest}
        {fitMode}
      />
    </div>
  </main>
</div>