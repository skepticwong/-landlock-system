// src/lib/map.js
let L; // Store Leaflet reference

export async function initMap(mapElement, onMapClick) {
	const leaflet = await import('leaflet');
	L = leaflet.default || leaflet;

	const map = L.map(mapElement).setView([-13.9833, 33.7833], 13);

	L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
		attribution: '&copy; OpenStreetMap contributors',
		maxZoom: 19
	}).addTo(map);

	if (onMapClick) {
		map.on('click', onMapClick);
	}

	return map;
}

export function addPolyline(map, points, color = '#22c55e') {
	if (!map || !L || points.length < 2) return null;

	// Create a copy of points and add the first point at the end to close the loop
	const latlngs = [...points, points[0]].map(p => [p.lat, p.lng]);
	
	// Create a semi-transparent polygon for the fill
	const fillColor = color === '#22c55e' ? 'rgba(34, 197, 94, 0.2)' : 'rgba(29, 78, 216, 0.2)';
	
	// Add the filled polygon
	L.polygon(latlngs, {
		color: 'transparent',
		fillColor: fillColor,
		fillOpacity: 0.3,
		weight: 0
	}).addTo(map);
	
	// Add the dashed border on top
	return L.polyline(latlngs, { 
		color: color, 
		weight: 3,
		dashArray: '5, 5',
		fill: false,
		interactive: false
	}).addTo(map);
}

export function addPolygon(map, points, id, name) {
	if (!map || !L || points.length === 0) return null;

	const latlngs = points.map(p => [p.lat, p.lng]);
	const polygon = L.polygon(latlngs, {
		color: '#1d4ed8',
		fillColor: '#3b82f6',
		fillOpacity: 0.3,
		weight: 2
	}).addTo(map);

	polygon.bindTooltip(`${name} (ID: ${id})`, {
		direction: 'center',
		className: 'font-semibold'
	});

	return polygon;
}  