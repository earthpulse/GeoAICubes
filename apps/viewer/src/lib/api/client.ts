import type { ZarrInventoryList, ZarrStoreInventory } from '../types/inventory.ts'

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

export function tileUrlForLayer(
  apiBase: string,
  template: string,
  store: import('../types/inventory.ts').ZarrStoreInventory,
  timeIndex: number,
): string {
  let url = resolveTileTemplate(apiBase, template)
  const values = store.time?.values
  if (values && values.length > timeIndex) {
    url = withTimeSelection(url, values[timeIndex])
  }
  return url
}