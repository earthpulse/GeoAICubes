/** Mirrors D2 `ZarrStoreInventory` / list shapes (Step 1 viewer). */

export type StoreStatus = 'ok' | 'error'

export type RenderMode = 'rgb' | 'single' | 'categorical'

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

export interface ExtraDimInfo {
  name: string
  kind: 'nominal' | 'ordinal' | 'datetime'
  labels: string[]
}

export interface RenderDefaults {
  mode: RenderMode
  sel: Record<string, string[]>
  bidx: number[] | null
  rescale: [number, number][]
  colormap_name: string | null
  colormap: Record<number, number[]> | null
}

export interface LegendEntry {
  value: number
  label: string
  color: string
}

export interface RenderCapability {
  modes: RenderMode[]
  variable: string
  extra_dims: ExtraDimInfo[]
  defaults: RenderDefaults
  legend: LegendEntry[]
  primary?: boolean
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
  render_capabilities: Record<string, RenderCapability>
}

export interface ZarrInventoryList {
  stores: ZarrStoreInventory[]
  count: number
}

export interface LayerRenderState {
  mode: RenderMode
  bandDim: string | null
  bandSelection: string[]
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
  renderState: LayerRenderState
}