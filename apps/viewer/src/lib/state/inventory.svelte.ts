import { fetchInventory, fetchStore } from '../api/client.ts'
import type { MapLayer, ZarrStoreInventory } from '../types/inventory.ts'

export function buildMapLayers(stores: ZarrStoreInventory[]): MapLayer[] {
  const layers: MapLayer[] = []
  for (const store of stores) {
    const templates = store.tile_url_template ?? {}
    for (const [variable, tileUrlTemplate] of Object.entries(templates)) {
      layers.push({
        layerId: `${store.id}::${variable}`,
        storeId: store.id,
        variable,
        tileUrlTemplate,
        status: store.status,
        visible: false,
        timeIndex: 0,
        store,
      })
    }
    if (store.status === 'error' || Object.keys(templates).length === 0) {
      layers.push({
        layerId: `${store.id}::__store__`,
        storeId: store.id,
        variable: '',
        tileUrlTemplate: '',
        status: store.status,
        visible: false,
        timeIndex: 0,
        store,
      })
    }
  }
  return layers
}

export function defaultSelectedStoreId(stores: ZarrStoreInventory[]): string | null {
  if (stores.length === 0) {
    return null
  }
  const ok = stores.find((s) => s.status === 'ok')
  return (ok ?? stores[0]).id
}

export interface InventoryState {
  stores: ZarrStoreInventory[]
  mapLayers: MapLayer[]
  selectedStoreId: string | null
  inventoryError: string | null
  inventoryLoading: boolean
  timeIndexByStore: Record<string, number>
}

export function createInventoryState(apiBase: string): InventoryState {
  let stores = $state<ZarrStoreInventory[]>([])
  let mapLayers = $state<MapLayer[]>([])
  let selectedStoreId = $state<string | null>(null)
  let inventoryError = $state<string | null>(null)
  let inventoryLoading = $state(true)
  let timeIndexByStore = $state<Record<string, number>>({})

  async function loadInventory() {
    inventoryLoading = true
    inventoryError = null
    try {
      const list = await fetchInventory(apiBase)
      stores = list.stores
      mapLayers = buildMapLayers(stores)
      selectedStoreId = defaultSelectedStoreId(stores)
      const nextTime: Record<string, number> = { ...timeIndexByStore }
      for (const s of stores) {
        if (nextTime[s.id] === undefined) {
          nextTime[s.id] = 0
        }
      }
      timeIndexByStore = nextTime
      await enrichTimeValuesWhereNeeded()
    } catch (e) {
      inventoryError = e instanceof Error ? e.message : String(e)
      stores = []
      mapLayers = []
      selectedStoreId = null
    } finally {
      inventoryLoading = false
    }
  }

  async function enrichTimeValuesWhereNeeded() {
    const tasks = stores
      .filter(
        (s) =>
          s.status === 'ok' &&
          s.time &&
          (s.time.count ?? 0) > 1 &&
          (!s.time.values || s.time.values.length === 0),
      )
      .map(async (s) => {
        try {
          const detail = await fetchStore(apiBase, s.id)
          if (detail.time?.values?.length) {
            stores = stores.map((row) => (row.id === s.id ? detail : row))
            mapLayers = mapLayers.map((layer) =>
              layer.storeId === s.id ? { ...layer, store: detail } : layer,
            )
          }
        } catch {
          /* keep index-only stepper */
        }
      })
    await Promise.all(tasks)
  }

  function selectStore(storeId: string) {
    selectedStoreId = storeId
  }

  function toggleLayerVisibility(layerId: string) {
    mapLayers = mapLayers.map((layer) =>
      layer.layerId === layerId ? { ...layer, visible: !layer.visible } : layer,
    )
  }

  function setTimeIndex(storeId: string, index: number) {
    timeIndexByStore = { ...timeIndexByStore, [storeId]: index }
    mapLayers = mapLayers.map((layer) =>
      layer.storeId === storeId ? { ...layer, timeIndex: index } : layer,
    )
  }

  const selected = $derived(stores.find((s) => s.id === selectedStoreId) ?? null)

  const visibleLayers = $derived(
    mapLayers.filter(
      (l) =>
        l.visible &&
        l.status === 'ok' &&
        l.tileUrlTemplate &&
        l.variable &&
        l.layerId.endsWith(`::${l.variable}`),
    ),
  )

  return {
    get stores() {
      return stores
    },
    get mapLayers() {
      return mapLayers
    },
    get selectedStoreId() {
      return selectedStoreId
    },
    get selectedStore() {
      return selected
    },
    get inventoryError() {
      return inventoryError
    },
    get inventoryLoading() {
      return inventoryLoading
    },
    get timeIndexByStore() {
      return timeIndexByStore
    },
    get visibleRenderableLayers() {
      return visibleLayers
    },
    loadInventory,
    selectStore,
    toggleLayerVisibility,
    setTimeIndex,
  }
}