import type { ZarrInventoryList, MapLayer, ZarrStoreInventory } from '../types/inventory.ts'
import { buildTileUrlFromTemplate } from '../render/buildTileUrl.ts'

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status?: number,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

export function normalizeApiBase(raw: string | undefined): string {
  return (raw || 'http://localhost:8000').replace(/\/$/, '')
}

export async function fetchHealth(apiBase: string): Promise<unknown> {
  const res = await fetch(`${apiBase}/health`)
  if (!res.ok) {
    throw new ApiError(`${res.status} ${res.statusText}`, res.status)
  }
  return res.json()
}

export async function fetchInventory(apiBase: string): Promise<ZarrInventoryList> {
  const res = await fetch(`${apiBase}/api/v1/inventory/zarr`)
  if (!res.ok) {
    throw new ApiError(`${res.status} ${res.statusText}`, res.status)
  }
  return res.json()
}

export async function fetchStore(
  apiBase: string,
  storeId: string,
): Promise<ZarrStoreInventory> {
  const res = await fetch(`${apiBase}/api/v1/inventory/zarr/${encodeURIComponent(storeId)}`)
  if (!res.ok) {
    throw new ApiError(`${res.status} ${res.statusText}`, res.status)
  }
  return res.json()
}

/** Resolve inventory tile path template against API origin (no double slashes). */
export function resolveTileTemplate(apiBase: string, template: string): string {
  if (/^https?:\/\//i.test(template)) {
    return template
  }
  const path = template.startsWith('/') ? template : `/${template}`
  return `${apiBase}${path}`
}

/**
 * Apply optional time selection via `sel=time=` (TiTiler contract).
 * Replaces an existing `sel=time=…` in the query when present.
 */
export function withTimeSelection(resolvedUrl: string, timeLabel: string | null): string {
  if (!timeLabel) {
    return resolvedUrl
  }
  const qIndex = resolvedUrl.indexOf('?')
  if (qIndex === -1) {
    return `${resolvedUrl}?sel=time=${encodeURIComponent(timeLabel)}`
  }
  const base = resolvedUrl.slice(0, qIndex)
  const query = resolvedUrl.slice(qIndex + 1)
  const parts = query.split('&').filter((p) => p && !p.startsWith('sel=time='))
  parts.push(`sel=time=${encodeURIComponent(timeLabel)}`)
  return `${base}?${parts.join('&')}`
}

export function tileUrlForLayer(apiBase: string, layer: MapLayer): string {
  const cap = layer.store.render_capabilities?.[layer.variable]
  if (!cap) {
    let url = resolveTileTemplate(apiBase, layer.tileUrlTemplate)
    const values = layer.store.time?.values
    if (values && values.length > layer.timeIndex) {
      url = withTimeSelection(url, values[layer.timeIndex])
    }
    return url
  }
  return resolveTileTemplate(
    apiBase,
    buildTileUrlFromTemplate(
      layer.tileUrlTemplate,
      cap,
      layer.renderState,
      layer.store,
      layer.variable,
      layer.timeIndex,
    ),
  )
}