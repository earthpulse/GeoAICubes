/** Mirrors D2 `ZarrStoreInventory` / list shapes (Step 1 viewer). */

export type StoreStatus = 'ok' | 'error'

export interface InventoryVariable {
  name: string
  dtype: string
  shape: number[]
}

export interface InventoryExtent {
  bbox: [number, number, number, number]
  crs: string
}

export interface InventoryTime {
  dim: string
  values: string[] | null
  start: string | null
  end: string | null
  count: number | null
}

export interface ZarrStoreInventory {
  id: string
  uri: string
  path: string
  status: StoreStatus
  error: string | null
  dims: string[]
  variables: InventoryVariable[]
  crs: string | null
  extent: InventoryExtent | null
  time: InventoryTime | null
  nodata: Record<string, unknown>
  chunks: Record<string, Record<string, number>>
  tile_url_template: Record<string, string>
}

export interface ZarrInventoryList {
  stores: ZarrStoreInventory[]
  count: number
}

/** Derived client model (not in API). */
export interface MapLayer {
  layerId: string
  storeId: string
  variable: string
  tileUrlTemplate: string
  status: StoreStatus
  visible: boolean
  timeIndex: number
  store: ZarrStoreInventory
}