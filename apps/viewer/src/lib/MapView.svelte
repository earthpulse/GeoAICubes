<script>
  import { onMount } from 'svelte'
  import L from 'leaflet'
  import { tileUrlForLayer } from './api/client.ts'
  import { extentToLatLngBounds, unionLatLngBounds } from './geo/extent.ts'

  /**
   * @type {{
   *   apiBase: string,
   *   layers: import('./types/inventory.ts').MapLayer[],
   *   selectedStore: import('./types/inventory.ts').ZarrStoreInventory | null,
   *   fitRequest: number,
   *   fitMode: 'selected' | 'visible',
   * }}
   */
  let { apiBase, layers, selectedStore, fitRequest, fitMode } = $props()

  let mapEl = $state(null)
  /** @type {L.Map | null} */
  let map = $state(null)
  /** @type {Map<string, { layer: L.TileLayer, url: string }>} */
  let overlayById = new Map()

  onMount(() => {
    if (!mapEl) {
      return
    }
    map = L.map(mapEl, {
      center: [41.9, 2.4],
      zoom: 8,
    })
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
      maxZoom: 19,
    }).addTo(map)

    return () => {
      map?.remove()
      map = null
      overlayById.clear()
    }
  })

  $effect(() => {
    if (!map) {
      return
    }
    const visible = layers.filter(
      (l) => l.visible && l.status === 'ok' && l.tileUrlTemplate && l.variable,
    )
    const visibleIds = new Set(visible.map((l) => l.layerId))

    for (const [id, entry] of overlayById.entries()) {
      if (!visibleIds.has(id)) {
        map.removeLayer(entry.layer)
        overlayById.delete(id)
      }
    }

    for (const layer of visible) {
      const url = tileUrlForLayer(apiBase, layer)
      const existing = overlayById.get(layer.layerId)
      if (existing?.url === url) {
        continue
      }
      if (existing) {
        map.removeLayer(existing.layer)
        overlayById.delete(layer.layerId)
      }
      const tileLayer = L.tileLayer(url, {
        opacity: 0.85,
        attribution: 'GeoAICubes API / TiTiler',
      })
      tileLayer.addTo(map)
      overlayById.set(layer.layerId, { layer: tileLayer, url })
    }
  })

  $effect(() => {
    const _ = fitRequest
    if (!map) {
      return
    }
    if (fitMode === 'selected' && selectedStore?.extent) {
      const b = extentToLatLngBounds(selectedStore.extent)
      if (b) {
        map.fitBounds(b, { padding: [24, 24] })
      }
    } else if (fitMode === 'visible') {
      const boundsList = []
      const seen = new Set()
      for (const layer of layers) {
        if (!layer.visible || layer.status !== 'ok') {
          continue
        }
        if (seen.has(layer.storeId)) {
          continue
        }
        seen.add(layer.storeId)
        const ext = layer.store.extent
        if (ext) {
          const b = extentToLatLngBounds(ext)
          if (b) {
            boundsList.push(b)
          }
        }
      }
      const union = unionLatLngBounds(boundsList)
      if (union) {
        map.fitBounds(union, { padding: [24, 24] })
      }
    }
  })

</script>

<div class="map-root" bind:this={mapEl} role="application" aria-label="Leaflet map"></div>

<style>
  .map-root {
    width: 100%;
    height: 100%;
    min-height: 360px;
    border-radius: 8px;
    border: 1px solid var(--border);
    overflow: hidden;
    background: var(--map-bg);
    position: relative;
  }

  :global(.leaflet-container) {
    font-family: inherit;
  }
</style>