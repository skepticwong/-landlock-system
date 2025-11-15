// src/lib/map.js
export async function initMap(mapElement, onMapClick) {
	const L = await import('leaflet');

	const map = L.map(mapElement).setView([-13.24, 34.3], 15);

	L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
		attribution: '&copy; OpenStreetMap contributors'
	}).addTo(map);

	map.on('click', onMapClick);

	return map;
}

export function addPolyline(map, points, color = '#22c55e') {
	if (!map || points.length === 0) return null;

	const latlngs = points.map(p => [p.lat, p.lng]);
	return L.polyline(latlngs, { color, weight: 3 }).addTo(map);
}

export function addPolygon(map, points, id, name) {
	const latlngs = points.map(p => [p.lat, p.lng]);
	const polygon = L.polygon(latlngs, {
		color: '#1d4ed8',
		fillColor: '#3b82f6',
		fillOpacity: 0.3,
		weight: 2
	}).addTo(map);

	polygon.bindTooltip(`${name} (${id})`, {
		direction: 'center',
		className: 'font-semibold'
	});

	return polygon;
}