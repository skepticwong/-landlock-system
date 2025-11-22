<script context="module">
	export const load = async () => {
		return {
			redirect: '/dashboard',
			status: 302
		};
	};
</script>

<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { browser } from '$app/environment';

	onMount(() => {
		if (browser) {
			goto('/dashboard');
		}
	});
</script>
	let isFullscreen = false;
	let mapHeight = 500; // Default height in pixels
	let isResizing = false;

	// Subscribe to status store
	const unsubscribe = status.subscribe(value => {
		currentStatus = value;
	});

	// Load existing plots on mount
	onMount(async () => {
		try {
			// Import Leaflet
			const leaflet = await import('leaflet');
			L = leaflet.default || leaflet;

			// Initialize map first
			const mapElement = document.getElementById('map');
			if (mapElement) {
				mapComponent = await initMap(mapElement, (e) => {
					const { lat, lng } = e.latlng;
					points = [...points, { lat, lng }];
					status.set(`Point ${points.length} added at (${lat.toFixed(4)}, ${lng.toFixed(4)})`);
					updatePolyline();
				});
				
				mapReady = true;
				status.set('Map ready! Click on the map or use GPS to add boundary points.');

				// Then try to load existing plots
				try {
					const data = await fetchPlots();
					plots.set(data);
					existingPlots = data;
					
					// Add existing plots to map
					if (existingPlots && existingPlots.length > 0) {
						existingPlots.forEach(plot => {
							if (plot.points && plot.points.length > 0) {
								addPolygon(mapComponent, plot.points, plot.id, plot.plot_name);
							}
						});
						status.set(`Map ready! ${existingPlots.length} existing plots loaded.`);
					}
				} catch (error) {
					console.warn('Could not load existing plots:', error);
					status.set('Map ready! (Could not load existing plots - check if backend is running)');
				}
			}
		} catch (error) {
			status.set('Map initialization failed: ' + error.message);
			console.error('Initialization error:', error);
		}

		// Add resize event listeners
		document.addEventListener('mousemove', handleResize);
		document.addEventListener('mouseup', stopResize);

		// Cleanup subscription on destroy
		return () => {
			unsubscribe();
			document.removeEventListener('mousemove', handleResize);
			document.removeEventListener('mouseup', stopResize);
		};
	});

	// Update polyline to show boundaries as drawing
	function updatePolyline() {
		if (mapComponent && L && points.length > 0) {
			const latlngs = points.map(p => [p.lat, p.lng]);

			if (polyline) {
				// Update existing polyline
				polyline.setLatLngs(latlngs);
			} else {
				// Create new polyline with styling
				polyline = L.polyline(latlngs, { 
					color: '#10b981', 
					weight: 4,
					opacity: 0.8,
					dashArray: '10, 5' // Dashed line to show it's being drawn
				}).addTo(mapComponent);
			}

			// If we have 3+ points, also show filled polygon preview
			if (points.length >= 3) {
				// Remove old polygon if exists
				if (polyline.polygon) {
					polyline.polygon.remove();
				}
				
				// Add semi-transparent polygon
				polyline.polygon = L.polygon(latlngs, {
					color: '#10b981',
					fillColor: '#10b981',
					fillOpacity: 0.2,
					weight: 2
				}).addTo(mapComponent);
			}

			// Keep map centered on latest point
			mapComponent.panTo([points[points.length - 1].lat, points[points.length - 1].lng]);
		}
	}

	// Add point using GPS
	async function addPoint() {
		if (!navigator.geolocation) {
			status.set('❌ GPS not supported on this device.');
			return;
		}

		status.set('📍 Getting your location...');
		navigator.geolocation.getCurrentPosition(
			(pos) => {
				const { latitude, longitude } = pos.coords;
				points = [...points, { lat: latitude, lng: longitude }];
				status.set(`✅ Point ${points.length} added: ${latitude.toFixed(6)}, ${longitude.toFixed(6)}`);
				updatePolyline();
			},
			(err) => {
				status.set(`❌ GPS Error: ${err.message}`);
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
		
		// Convert to acres (rough approximation)
		const acres = area * 3044265;
		return acres.toFixed(2);
	}

	// Clear all points
	function clearPoints() {
		points = [];
		if (polyline) {
			polyline.setLatLngs([]);
			if (polyline.polygon) {
				polyline.polygon.remove();
				polyline.polygon = null;
			}
		}
		status.set('All points cleared. Start adding new boundary points.');
	}

	// Toggle fullscreen map
	function toggleFullscreen() {
		isFullscreen = !isFullscreen;
		// Give map time to resize, then invalidate size
		setTimeout(() => {
			if (mapComponent) {
				mapComponent.invalidateSize();
			}
		}, 100);
	}

	// Handle map resize
	function startResize(e) {
		isResizing = true;
		e.preventDefault();
	}

	function handleResize(e) {
		if (!isResizing) return;
		
		const mapCard = document.querySelector('.map-card');
		if (!mapCard) return;
		
		const rect = mapCard.getBoundingClientRect();
		const newHeight = Math.max(300, Math.min(1000, e.clientY - rect.top - 80));
		
		mapHeight = newHeight;
		
		// Invalidate map size after resize
		if (mapComponent) {
			mapComponent.invalidateSize();
		}
	}

	function stopResize() {
		isResizing = false;
	}

	// Submit plot
	async function submitPlot() {
		if (!plotName || !ownerPhone) {
			status.set('❌ Please fill in all required fields');
			return;
		}

		if (points.length < 3) {
			status.set('❌ Please add at least 3 boundary points');
			return;
		}

		try {
			const plotData = {
				owner_phone: ownerPhone,
				plot_name: plotName,
				points: points,
				area_acres: calculateArea()
			};

			status.set('📤 Submitting plot...');
			const newPlot = await registerPlot(plotData);
			plots.update(p => [...p, newPlot]);
			
			// Remove drawing polyline/polygon
			if (polyline) {
				polyline.remove();
				if (polyline.polygon) {
					polyline.polygon.remove();
				}
				polyline = null;
			}

			// Add permanent polygon to map
			if (mapComponent && newPlot.points) {
				addPolygon(mapComponent, newPlot.points, newPlot.id, newPlot.plot_name);
			}

			status.set(`✅ Plot ${newPlot.id} registered successfully!`);
			
			// Reset form
			plotName = '';
			ownerPhone = '';
			points = [];
		} catch (error) {
			status.set(`❌ Registration failed: ${error.message}`);
			console.error('Submit error:', error);
</script>

<svelte:head>
	<title>LandLock - Redirecting...</title>
</svelte:head>

<main class="min-h-screen flex items-center justify-center bg-gradient-to-br from-emerald-50 via-green-50 to-teal-50">
	<div class="text-center p-8">
		<div class="animate-pulse">
			<svg class="mx-auto h-12 w-12 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
			</svg>
			<div class="mt-4">
				<h2 class="text-2xl font-bold bg-gradient-to-r from-emerald-600 to-green-600 bg-clip-text text-transparent">
					LandLock
				<div class="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
					<span class="text-xl">ℹ️</span>
				</div>
				<div class="flex-1">
					<p class="font-semibold text-gray-800 text-sm mb-1">Current Status</p>
					<p class="text-gray-600 text-sm leading-relaxed">{currentStatus}</p>
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

		<!-- Map Card with Fullscreen -->
		<div class="bg-white rounded-2xl shadow-lg p-6 mb-6 border border-gray-100 map-card" class:fullscreen-map={isFullscreen}>
			<div class="flex items-center justify-between mb-4">
				<h2 class="text-xl font-bold text-gray-800 flex items-center gap-2">
					<span class="text-2xl">🗺️</span>
					Interactive Map
					{#if mapReady}
						<span class="ml-2 text-xs bg-green-100 text-green-700 px-3 py-1 rounded-full font-semibold">Active</span>
					{/if}
				</h2>
				
				<button
					on:click={toggleFullscreen}
					class="flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors text-sm font-semibold text-gray-700"
				>
					{#if isFullscreen}
						<span>⤓</span> Exit Fullscreen
					{:else}
						<span>⤢</span> Fullscreen
					{/if}
				</button>
			</div>
			
			<div class="map-container" style="height: {mapHeight}px;">
				<div id="map" class="w-full h-full rounded-xl overflow-hidden border-2 border-gray-200 shadow-inner" class:fullscreen-map-container={isFullscreen}></div>
				
				{#if !isFullscreen}
					<div 
						class="resize-handle"
						on:mousedown={startResize}
						role="button"
						tabindex="0"
						aria-label="Resize map"
					>
						<div class="resize-indicator">
							<span>⋮</span>
						</div>
					</div>
				{/if}
			</div>
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
		user-select: none;
	}
	
	.map-container {
		position: relative;
		width: 100%;
	}

	#map { 
		width: 100%;
		height: 100%;
		position: relative;
		background: #f3f4f6;
		transition: height 0.1s ease;
	}

	.resize-handle {
		position: absolute;
		bottom: 0;
		left: 0;
		right: 0;
		height: 20px;
		cursor: ns-resize;
		display: flex;
		align-items: center;
		justify-content: center;
		background: linear-gradient(to bottom, transparent, rgba(0,0,0,0.05));
		border-radius: 0 0 0.75rem 0.75rem;
	}

	.resize-handle:hover {
		background: linear-gradient(to bottom, transparent, rgba(16, 185, 129, 0.1));
	}

	.resize-indicator {
		background: #10b981;
		color: white;
		padding: 2px 12px;
		border-radius: 8px;
		font-size: 12px;
		font-weight: bold;
		pointer-events: none;
		box-shadow: 0 2px 4px rgba(0,0,0,0.1);
	}

	.fullscreen-map-container {
		height: calc(100vh - 200px) !important;
	}

	.fullscreen-map {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		z-index: 9999;
		max-width: 100%;
		margin: 0;
		border-radius: 0 !important;
		padding: 1rem;
		background: white;
	}
	
	:global(.leaflet-container) { 
		height: 100% !important; 
		width: 100% !important; 
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