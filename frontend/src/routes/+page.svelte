<script>
	import { onMount } from 'svelte';
	let points = [];
	let status = 'Click "Add Corner" to start recording your land boundary.';
	let plotName = '';
	let ownerPhone = '';

	// Map variables
	let map;
	let polyline;
	let L; // Store Leaflet library reference

	// Initialize map when component mounts
	onMount(async () => {
		try {
			// Import Leaflet
			L = await import('leaflet');

			// Add Leaflet CSS
			const link = document.createElement('link');
			link.rel = 'stylesheet';
			link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
			document.head.appendChild(link);

			// Wait a bit for CSS to load
			await new Promise(resolve => setTimeout(resolve, 100));

			// Initialize map
			map = L.map('map').setView([-13.9833, 33.7833], 13);

			L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
				attribution: '&copy; OpenStreetMap contributors',
				maxZoom: 19
			}).addTo(map);

			// Click listener to add point
			map.on('click', (e) => {
				const { lat, lng } = e.latlng;
				points = [...points, { lat, lng }];
				status = `Point added: ${lat.toFixed(6)}, ${lng.toFixed(6)}`;
				updatePolyline();
			});

			status = 'Map ready! Click on the map or use GPS to add boundary points.';
		} catch (error) {
			status = `Error initializing map: ${error.message}`;
			console.error('Map initialization error:', error);
		}
	});

	// Update polyline on map
	function updatePolyline() {
		if (map && L && points.length > 0) {
			const latlngs = points.map(p => [p.lat, p.lng]);

			if (polyline) {
				polyline.setLatLngs(latlngs);
			} else {
				polyline = L.polyline(latlngs, { color: '#10b981', weight: 4 }).addTo(map);
			}

			// Keep map centered on latest point
			map.panTo([points[points.length - 1].lat, points[points.length - 1].lng]);
		}
	}

	// Manual "Add Point" button (alternative to clicking map)
	async function addPoint() {
		if (!navigator.geolocation) {
			status = '❌ GPS not supported on this device.';
			return;
		}

		status = '📍 Getting your location...';
		navigator.geolocation.getCurrentPosition(
			(pos) => {
				const { latitude, longitude } = pos.coords;
				points = [...points, { lat: latitude, lng: longitude }];
				status = `✅ Point added: ${latitude.toFixed(6)}, ${longitude.toFixed(6)}`;
				updatePolyline();
			},
			(err) => {
				status = `❌ Error: ${err.message}`;
			},
			{ enableHighAccuracy: true, timeout: 10000 }
		);
	}

	// Calculate approximate area using shoelace formula
	function calculateArea() {
		if (points.length < 3) return 0;
		
		let area = 0;
		for (let i = 0; i < points.length; i++) {
			const j = (i + 1) % points.length;
			area += points[i].lat * points[j].lng;
			area -= points[j].lat * points[i].lng;
		}
		area = Math.abs(area) / 2;
		
		// Convert to acres (very rough approximation)
		const acres = area * 3044265;
		return acres.toFixed(2);
	}

	// Clear points
	function clearPoints() {
		points = [];
		if (polyline) {
			polyline.setLatLngs([]);
		}
		status = 'All points cleared. Start adding new boundary points.';
	}

	// Submit plot to backend
	async function submitPlot() {
		if (points.length < 3) {
			alert('Please add at least 3 corners to define your plot.');
			return;
		}
		if (!plotName || !ownerPhone) {
			alert('Please enter a plot name and your phone number.');
			return;
		}

		try {
			const res = await fetch('http://localhost:5000/plots', {
				method: 'POST',
				body: JSON.stringify({
					owner_phone: ownerPhone,
					plot_name: plotName,
					points,
					area_acres: calculateArea()
				}),
				headers: { 'Content-Type': 'application/json' }
			});

			const data = await res.json();
			if (res.ok) {
				alert(`Success! Plot ${data.id} registered.`);
				points = [];
				plotName = '';
				if (polyline) {
					polyline.setLatLngs([]);
				}
				status = 'Plot submitted successfully! You can register a new plot now.';
			} else {
				alert('Error: ' + data.error);
			}
		} catch (error) {
			alert('Network error: ' + error.message);
			console.error('Submit error:', error);
		}
	}
</script>

<svelte:head>
	<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" 
		integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" 
		crossorigin=""/>
	<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
</svelte:head>

<div class="min-h-screen bg-gradient-to-br from-emerald-50 via-green-50 to-teal-50">
	<!-- Header -->
	<header class="bg-white shadow-sm border-b border-emerald-100">
		<div class="max-w-5xl mx-auto px-4 py-6">
			<div class="flex items-center justify-center gap-3">
				<div class="w-12 h-12 bg-gradient-to-br from-emerald-500 to-green-600 rounded-xl flex items-center justify-center shadow-lg">
					<span class="text-2xl">🌍</span>
				</div>
				<div>
					<h1 class="text-3xl font-bold bg-gradient-to-r from-emerald-600 to-green-600 bg-clip-text text-transparent">
						LandLock
					</h1>
					<p class="text-sm text-gray-500 font-medium">Secure Land Registry for Malawi</p>
				</div>
			</div>
		</div>
	</header>

	<main class="max-w-5xl mx-auto p-4 py-8">
		<!-- Status Banner -->
		<div class="bg-white border border-blue-200 rounded-2xl p-4 mb-6 shadow-sm">
			<div class="flex items-start gap-3">
				<div class="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
					<span class="text-xl">ℹ️</span>
				</div>
				<div class="flex-1">
					<p class="font-semibold text-gray-800 text-sm mb-1">Current Status</p>
					<p class="text-gray-600 text-sm leading-relaxed">{status}</p>
				</div>
			</div>
		</div>

		<!-- Form Card -->
		<div class="bg-white rounded-2xl shadow-lg p-8 mb-6 border border-gray-100">
			<h2 class="text-xl font-bold text-gray-800 mb-6 flex items-center gap-2">
				<span class="text-2xl">📝</span>
				Plot Information
			</h2>
			
			<div class="space-y-5">
				<div>
					<label class="block text-sm font-semibold text-gray-700 mb-2">Plot Name</label>
					<input
						type="text"
						placeholder="e.g., Family Farm, Main Homestead"
						bind:value={plotName}
						class="w-full p-4 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 focus:outline-none transition-all text-gray-700 placeholder-gray-400"
					/>
				</div>

				<div>
					<label class="block text-sm font-semibold text-gray-700 mb-2">Phone Number</label>
					<input
						type="tel"
						placeholder="265888123456"
						bind:value={ownerPhone}
						class="w-full p-4 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 focus:outline-none transition-all text-gray-700 placeholder-gray-400"
					/>
				</div>

				<div class="pt-2">
					<button 
						on:click={addPoint} 
						class="w-full bg-gradient-to-r from-emerald-500 to-green-600 hover:from-emerald-600 hover:to-green-700 text-white font-bold py-4 px-6 rounded-xl transition-all transform hover:scale-[1.02] active:scale-[0.98] shadow-lg hover:shadow-xl"
					>
						<span class="flex items-center justify-center gap-2">
							<span class="text-xl">📍</span>
							Add Corner (Use GPS)
						</span>
					</button>
				</div>

				<div class="relative">
					<div class="absolute inset-0 flex items-center">
						<div class="w-full border-t border-gray-300"></div>
					</div>
					<div class="relative flex justify-center text-sm">
						<span class="px-4 bg-white text-gray-500 font-medium">or click directly on the map</span>
					</div>
				</div>
				
				{#if points.length > 0}
					<button 
						on:click={clearPoints} 
						class="w-full bg-red-50 hover:bg-red-100 text-red-600 font-semibold py-3 px-4 rounded-xl transition-all border-2 border-red-200"
					>
						<span class="flex items-center justify-center gap-2">
							<span class="text-lg">🗑️</span>
							Clear All Points
						</span>
					</button>
				{/if}
			</div>
		</div>

		<!-- Map Card -->
		<div class="bg-white rounded-2xl shadow-lg p-6 mb-6 border border-gray-100">
			<h2 class="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
				<span class="text-2xl">🗺️</span>
				Interactive Map
			</h2>
			<div id="map" class="w-full h-96 rounded-xl overflow-hidden border-2 border-gray-200 shadow-inner"></div>
		</div>

		<!-- Points Summary -->
		{#if points.length > 0}
			<div class="bg-gradient-to-br from-white to-emerald-50 rounded-2xl shadow-lg p-6 border-2 border-emerald-200 mb-6">
				<div class="flex items-start justify-between mb-4">
					<div>
						<h3 class="text-xl font-bold text-gray-800 flex items-center gap-2">
							<span class="text-2xl">📐</span>
							Boundary Summary
						</h3>
						<p class="text-sm text-gray-600 mt-1">{points.length} corner points recorded</p>
					</div>
					<div class="bg-emerald-500 text-white px-4 py-2 rounded-xl font-bold shadow-md">
						{calculateArea()} acres
					</div>
				</div>
				
				<div class="bg-white rounded-xl p-4 border border-emerald-100">
					<div class="grid gap-2 max-h-48 overflow-y-auto">
						{#each points as p, i}
							<div class="flex items-center gap-3 p-3 bg-gray-50 rounded-lg border border-gray-200 hover:border-emerald-300 transition-colors">
								<div class="w-8 h-8 bg-emerald-500 text-white rounded-full flex items-center justify-center font-bold text-sm flex-shrink-0">
									{i + 1}
								</div>
								<div class="flex-1 text-sm">
									<span class="font-semibold text-gray-700">Lat:</span> 
									<span class="text-gray-600">{p.lat.toFixed(6)}</span>
									<span class="mx-2 text-gray-400">|</span>
									<span class="font-semibold text-gray-700">Lng:</span> 
									<span class="text-gray-600">{p.lng.toFixed(6)}</span>
								</div>
							</div>
						{/each}
					</div>
				</div>
			</div>
		{/if}

		<!-- Submit Button -->
		{#if points.length >= 3}
			<button 
				on:click={submitPlot} 
				class="w-full bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white font-bold py-5 px-6 rounded-2xl transition-all transform hover:scale-[1.02] active:scale-[0.98] shadow-xl hover:shadow-2xl"
			>
				<span class="flex items-center justify-center gap-3">
					<span class="text-2xl">✅</span>
					<span class="text-lg">Submit Plot for Review</span>
				</span>
			</button>
		{/if}

		<!-- Footer Info -->
		<div class="mt-8 text-center">
			<p class="text-sm text-gray-500">
				🔒 Your land data is securely recorded and protected
			</p>
		</div>
	</main>
</div>

<style>
	:global(body) {
		margin: 0;
		padding: 0;
		font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
	}
	
	#map { 
		height: 384px;
		position: relative;
	}
	
	:global(.leaflet-container) { 
		height: 100%; 
		width: 100%; 
		z-index: 1;
	}

	/* Custom scrollbar for points list */
	.overflow-y-auto::-webkit-scrollbar {
		width: 8px;
	}

	.overflow-y-auto::-webkit-scrollbar-track {
		background: #f1f1f1;
		border-radius: 10px;
	}

	.overflow-y-auto::-webkit-scrollbar-thumb {
		background: #10b981;
		border-radius: 10px;
	}

	.overflow-y-auto::-webkit-scrollbar-thumb:hover {
		background: #059669;
	}
</style>