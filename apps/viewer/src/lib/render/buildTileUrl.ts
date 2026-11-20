import type {
  LayerRenderState,
  RenderCapability,
  RenderMode,
  ZarrStoreInventory,
} from '../types/inventory.ts'

const BAND_DIMS = new Set(['band', 'bands', 'wavelength'])
const KEEP_PARAMS = new Set(['url', 'variable', 'coord_crs'])

function parseQuery(template: string): Map<string, string[]> {
  const out = new Map<string, string[]>()
  const qIndex = template.indexOf('?')
  if (qIndex === -1) {
    return out
  }
  const query = template.slice(qIndex + 1)
  for (const part of query.split('&')) {
    if (!part) {
      continue
    }
    const eq = part.indexOf('=')
    if (eq === -1) {
      continue
    }
    const key = decodeURIComponent(part.slice(0, eq))
    const value = decodeURIComponent(part.slice(eq + 1))
    const list = out.get(key) ?? []
    list.push(value)
    out.set(key, list)
  }
  return out
}

function defaultRescale(dtype: string, count: number): [number, number][] {
  const n = dtype.toLowerCase()
  let pair: [number, number]
  if (n === 'uint8' || n === 'int8' || (n.startsWith('uint') && !n.includes('16'))) {
    pair = [0, 255]
  } else if (n.includes('16')) {
    pair = [0, 65535]
  } else {
    pair = [0, 3000]
  }
  return Array.from({ length: count }, () => pair)
}

function bandDimName(cap: RenderCapability): string | null {
  const found = cap.extra_dims.find((d) => BAND_DIMS.has(d.name))
  return found?.name ?? null
}

function timeDimName(cap: RenderCapability): string | null {
  const found = cap.extra_dims.find((d) => d.kind === 'datetime')
  return found?.name ?? null
}

function appendVisParams(
  pairs: [string, string][],
  cap: RenderCapability,
  state: LayerRenderState,
  timeLabel: string | null,
  variable: string,
  store: ZarrStoreInventory,
) {
  const defaults = cap.defaults
  const mode: RenderMode = state.mode
  const sel: Record<string, string[]> = { ...defaults.sel }

  const tDim = timeDimName(cap)
  if (timeLabel && tDim) {
    sel[tDim] = [timeLabel]
  }

  const bDim = state.bandDim ?? bandDimName(cap)
  if (bDim && state.bandSelection.length > 0) {
    sel[bDim] =
      mode === 'single' ? [state.bandSelection[0]] : state.bandSelection.slice(0, 3)
  }

  for (const dim of Object.keys(sel)) {
    for (const value of sel[dim]) {
      pairs.push(['sel', `${dim}=${value}`])
    }
  }

  const varRow = store.variables.find((v) => v.name === variable)
  const dtype = varRow?.dtype ?? 'float32'

  if (mode === 'rgb' && bDim) {
    const count = sel[bDim]?.length ?? 3
    const bidx =
      defaults.bidx && defaults.bidx.length >= count
        ? defaults.bidx.slice(0, count)
        : Array.from({ length: count }, (_, i) => i + 1)
    for (const idx of bidx) {
      pairs.push(['bidx', String(idx)])
    }
    const rescale =
      defaults.rescale.length >= count
        ? defaults.rescale.slice(0, count)
        : defaultRescale(dtype, count)
    for (const [lo, hi] of rescale) {
      pairs.push(['rescale', `${lo},${hi}`])
    }
    return
  }

  if (mode === 'categorical') {
    if (defaults.colormap) {
      pairs.push(['colormap', JSON.stringify(defaults.colormap)])
    } else if (defaults.colormap_name) {
      pairs.push(['colormap_name', defaults.colormap_name])
    } else {
      const [lo, hi] = defaults.rescale[0] ?? [0, 255]
      pairs.push(['rescale', `${lo},${hi}`])
    }
    return
  }

  const [lo, hi] = defaults.rescale[0] ?? [0, 3000]
  pairs.push(['rescale', `${lo},${hi}`])
}

export function initialRenderState(cap: RenderCapability): LayerRenderState {
  const bandDim = cap.extra_dims.find((d) => BAND_DIMS.has(d.name))
  const mode = cap.defaults.mode
  let bandSelection: string[] = []
  if (bandDim) {
    const fromSel = cap.defaults.sel[bandDim.name]
    if (fromSel?.length) {
      bandSelection = mode === 'single' ? [fromSel[0]] : fromSel.slice(0, 3)
    } else if (bandDim.labels.length) {
      bandSelection =
        mode === 'single'
          ? [bandDim.labels[0]]
          : bandDim.labels.slice(0, Math.min(3, bandDim.labels.length))
    }
  }
  return {
    mode,
    bandDim: bandDim?.name ?? null,
    bandSelection,
  }
}

export function buildTileUrlFromTemplate(
  template: string,
  cap: RenderCapability | undefined,
  state: LayerRenderState | undefined,
  store: ZarrStoreInventory,
  variable: string,
  timeIndex: number,
): string {
  if (!cap || !state) {
    return template.replace(/\{z\}/g, '{z}')
  }

  const qIndex = template.indexOf('?')
  const path = qIndex === -1 ? template : template.slice(0, qIndex)
  const parsed = parseQuery(template)
  const pairs: [string, string][] = []

  for (const key of KEEP_PARAMS) {
    const values = parsed.get(key)
    if (values) {
      for (const v of values) {
        pairs.push([key, v])
      }
    }
  }

  let timeLabel: string | null = null
  const values = store.time?.values
  if (values && values.length > timeIndex) {
    timeLabel = values[timeIndex]
  } else if (store.time?.start && timeIndex === 0) {
    timeLabel = store.time.start
  }

  appendVisParams(pairs, cap, state, timeLabel, variable, store)

  const query = pairs
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
    .join('&')
  return `${path}?${query}`
}