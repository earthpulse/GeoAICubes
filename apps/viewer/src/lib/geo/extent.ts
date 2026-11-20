import proj4 from 'proj4'
import type { InventoryExtent } from '../types/inventory.ts'

/** ETRS89 / UTM zone 31N — demo GeoDataCube CRS. */
proj4.defs(
  'EPSG:25831',
  '+proj=utm +zone=31 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs +type=crs',
)

export type LatLngBounds = [[number, number], [number, number]]

function normalizeCrs(crs: string): string {
  if (crs.startsWith('EPSG:')) {
    return crs
  }
  return crs
}

/** Convert inventory extent to Leaflet `fitBounds` argument (WGS84 lat/lng). */
export function extentToLatLngBounds(extent: InventoryExtent): LatLngBounds | null {
  const [minx, miny, maxx, maxy] = extent.bbox
  const crs = normalizeCrs(extent.crs)

  if (crs === 'EPSG:4326' || crs === 'WGS84') {
    return [
      [miny, minx],
      [maxy, maxx],
    ]
  }

  try {
    const sw = proj4(crs, 'EPSG:4326', [minx, miny])
    const ne = proj4(crs, 'EPSG:4326', [maxx, maxy])
    return [
      [sw[1], sw[0]],
      [ne[1], ne[0]],
    ]
  } catch {
    return null
  }
}

export function unionLatLngBounds(boundsList: LatLngBounds[]): LatLngBounds | null {
  if (boundsList.length === 0) {
    return null
  }
  let minLat = Infinity
  let minLng = Infinity
  let maxLat = -Infinity
  let maxLng = -Infinity
  for (const [[sLat, sLng], [nLat, nLng]] of boundsList) {
    minLat = Math.min(minLat, sLat, nLat)
    minLng = Math.min(minLng, sLng, nLng)
    maxLat = Math.max(maxLat, sLat, nLat)
    maxLng = Math.max(maxLng, sLng, nLng)
  }
  return [
    [minLat, minLng],
    [maxLat, maxLng],
  ]
}