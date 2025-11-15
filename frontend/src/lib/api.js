// src/lib/api.js
export async function fetchPlots() {
	try {
		const res = await fetch('http://localhost:5000/plots');
		if (!res.ok) throw new Error('Failed to load plots');
		const data = await res.json();
		return Array.isArray(data) ? data : [];
	} catch (err) {
		console.error('API Error:', err);
		throw err;
	}
}

export async function registerPlot(plotData) {
	const res = await fetch('http://localhost:5000/plots', {
		method: 'POST',
		body: JSON.stringify(plotData),
		headers: { 'Content-Type': 'application/json' }
	});

	const data = await res.json();
	if (!res.ok) throw new Error(data.error || 'Save failed');
	return data;
}