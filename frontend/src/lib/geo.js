 // src/lib/geo.js
// Geospatial helpers: polygon area (m²) and district auto-detection
// using Malawi district boundary polygons served by the backend.

const EARTH_RADIUS = 6378137; // meters (WGS84)

let districtBoundaries = /** @type {Record<string, number[][]> | null} */ (null);
let loadingPromise = /** @type {Promise<any> | null} */ (null);

let areaBoundaries = /** @type {any[] | null} */ (null);
let areaBoundariesPromise = /** @type {Promise<any[]> | null} */ (null);

/**
 * Load district boundary polygons from the backend (cached).
 */
export async function loadDistrictBoundaries() {
  if (districtBoundaries) return districtBoundaries;
  if (!loadingPromise) {
    loadingPromise = fetch(
      "http://localhost:5000/api/admin/district-boundaries",
    )
      .then((r) => (r.ok ? r.json() : {}))
      .then((data) => {
        districtBoundaries = data || {};
        return districtBoundaries;
      })
      .catch(() => {
        districtBoundaries = {};
        return districtBoundaries;
      });
  }
  return loadingPromise;
}

/**
 * Ray-casting point-in-polygon test.
 * @param {number} lng
 * @param {number} lat
 * @param {number[][]} polygon - array of [lng, lat] pairs (GeoJSON order)
 */
function pointInPolygon(lng, lat, polygon) {
  let inside = false;
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const xi = polygon[i][0],
      yi = polygon[i][1];
    const xj = polygon[j][0],
      yj = polygon[j][1];
    const intersects =
      yi > lat !== yj > lat && lng < ((xj - xi) * (lat - yi)) / (yj - yi) + xi;
    if (intersects) inside = !inside;
  }
  return inside;
}

/**
 * Load boundary vectors for all chief areas (villages, TAs, districts) from
 * the public endpoint. Chief areas and villages are the same thing: a village
 * vector is simply a chief area with a drawn boundary.
 * Each item: { id, area_type, area_id, area_name, district_id, villages, boundary: [[lng,lat],...] }
 */
export async function loadAreaBoundaries() {
  if (areaBoundaries) return areaBoundaries;
  if (!areaBoundariesPromise) {
    areaBoundariesPromise = /** @type {Promise<any[]>} */ (
      fetch('http://localhost:5000/api/public/area-boundaries')
        .then((r) => (r.ok ? r.json() : []))
        .then((data) => {
          areaBoundaries = data || [];
          return areaBoundaries;
        })
        .catch(() => {
          areaBoundaries = [];
          return areaBoundaries;
        })
    );
  }
  return areaBoundariesPromise;
}

/** Invalidate the cached area boundaries so the next load re-fetches. */
export function invalidateAreaBoundaries() {
  areaBoundaries = null;
  areaBoundariesPromise = null;
}

/**
 * Detect which village-level chief area a point falls inside.
 * @param {{lat: number, lng: number}} point
 * @returns {Promise<{village: string, area_id: string, district_id: string} | null>}
 */
export async function detectVillage(point) {
  const areas = await loadAreaBoundaries();
  for (const area of areas || []) {
    if (area.area_type !== 'village') continue;
    if (!Array.isArray(area.boundary) || area.boundary.length < 3) continue;
    if (pointInPolygon(point.lng, point.lat, area.boundary)) {
      return {
        village: area.area_name,
        area_id: area.area_id,
        district_id: area.district_id || ''
      };
    }
  }
  return null;
}

/**
 * Detect which Malawi district a point falls inside.
 * @param {{lat: number, lng: number}} point
 * @returns {Promise<string|null>} district name or null
 */
export async function detectDistrict(point) {
  const boundaries = await loadDistrictBoundaries();
  for (const [districtId, polygon] of Object.entries(boundaries)) {
    if (!Array.isArray(polygon) || polygon.length < 3) continue;
    if (pointInPolygon(point.lng, point.lat, polygon)) {
      // Capitalise the id for display: "lilongwe" -> "Lilongwe"
      return districtId.charAt(0).toUpperCase() + districtId.slice(1);
    }
  }
  return null;
}

/**
 * Approximate geodesic area of a polygon in square metres.
 * @param {{lat: number, lng: number}[]} points
 */
export function calculatePolygonArea(points) {
  if (!points || points.length < 3) return 0;

  const R = EARTH_RADIUS;
  let total = 0;

  for (let i = 0; i < points.length; i++) {
    const p1 = points[i];
    const p2 = points[(i + 1) % points.length];
    // Convert to radians
    const lat1 = (p1.lat * Math.PI) / 180;
    const lat2 = (p2.lat * Math.PI) / 180;
    const dLng = ((p2.lng - p1.lng) * Math.PI) / 180;
    // Spherical excess contribution of this edge
    total += dLng * (2 + Math.sin(lat1) + Math.sin(lat2));
  }

  total = (total * R * R) / 2;
  return Math.abs(total);
}

/**
 * Format an area in m² for display, always in metric (m² / ha).
 * @param {number} sqMeters
 */
export function formatArea(sqMeters) {
  if (!sqMeters || sqMeters <= 0) return "—";
  if (sqMeters >= 10000) {
    return `${(sqMeters / 10000).toLocaleString(undefined, { maximumFractionDigits: 2 })} ha (${sqMeters.toLocaleString(undefined, { maximumFractionDigits: 0 })} m²)`;
  }
  return `${sqMeters.toLocaleString(undefined, { maximumFractionDigits: 1 })} m²`;
}
