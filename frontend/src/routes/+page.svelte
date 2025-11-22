<script>
	// ... [your exact same <script> content here — no changes needed] ...
	import { onMount } from 'svelte';
	import { plots, status, currentUser } from '$lib/store.js';
	import { fetchPlots, registerPlot } from '$lib/api.js';
	import { initMap, addPolyline, addPolygon } from '$lib/map.js';

	let mapComponent;
	let existingPlots = [];
	let plotName = '';
	let ownerPhone = '';
	let points = [];
	let currentStatus = 'Loading map...';
	let polyline;
	let L;
	let mapReady = false;
	let isFullscreen = false;
	let mapHeight = 300;
	let isResizing = false;
	 let selectedPlotId = null;
  let plotLayers = [];

	const unsubscribe = status.subscribe(value => {
		currentStatus = value;
	});

	onMount(async () => {
		try {
			const leaflet = await import('leaflet');
			L = leaflet.default || leaflet;

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

				try {
					const data = await fetchPlots();
					plots.set(data);
					existingPlots = data;
					
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

		document.addEventListener('mousemove', handleResize);
		document.addEventListener('mouseup', stopResize);

		return () => {
			unsubscribe();
			document.removeEventListener('mousemove', handleResize);
			document.removeEventListener('mouseup', stopResize);
		};
	});

	function updatePolyline() {
		if (mapComponent && L && points.length > 0) {
			const latlngs = points.map(p => [p.lat, p.lng]);

			if (polyline) {
				polyline.setLatLngs(latlngs);
			} else {
				polyline = L.polyline(latlngs, { 
					color: '#0d9488', 
					weight: 4,
					opacity: 0.8,
					dashArray: '10, 5'
				}).addTo(mapComponent);
			}

			if (points.length >= 3) {
				if (polyline.polygon) {
					polyline.polygon.remove();
				}
				polyline.polygon = L.polygon(latlngs, {
					color: '#0d9488',
					fillColor: '#0d9488',
					fillOpacity: 0.2,
					weight: 2
				}).addTo(mapComponent);
			}

			mapComponent.panTo([points[points.length - 1].lat, points[points.length - 1].lng]);
		}
	}

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

	function calculateArea() {
		if (points.length < 3) return 0;
		let area = 0;
		for (let i = 0; i < points.length; i++) {
			const j = (i + 1) % points.length;
			area += points[i].lat * points[j].lng;
			area -= points[j].lat * points[i].lng;
		}
		area = Math.abs(area) / 2;
		const acres = area * 3044265;
		return acres.toFixed(2);
	}

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

	function toggleFullscreen() {
		isFullscreen = !isFullscreen;
		setTimeout(() => {
			if (mapComponent) mapComponent.invalidateSize();
		}, 100);
	}

	function startResize(e) {
		isResizing = true;
		e.preventDefault();
	}

	function handleResize(e) {
		if (!isResizing) return;
		const mapCard = document.querySelector('.map-card');
		if (!mapCard) return;
		const rect = mapCard.getBoundingClientRect();
		const newHeight = Math.max(300, Math.min(800, e.clientY - rect.top - 120));
		mapHeight = newHeight;
		if (mapComponent) mapComponent.invalidateSize();
	}

	function stopResize() {
		isResizing = false;
	}

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
			
			if (polyline) {
				polyline.remove();
				if (polyline.polygon) polyline.polygon.remove();
				polyline = null;
			}

			if (mapComponent && newPlot.points) {
				addPolygon(mapComponent, newPlot.points, newPlot.id, newPlot.plot_name);
			}

			status.set(`✅ Plot ${newPlot.id} registered successfully!`);
			plotName = '';
			ownerPhone = '';
			points = [];
		} catch (error) {
			status.set(`❌ Registration failed: ${error.message}`);
			console.error('Submit error:', error);
		}
	}
	
	// Add these functions with your other functions
  function calculateAreaFromPoints(points) {
    if (!points || points.length < 3) return 0;
    let area = 0;
    for (let i = 0; i < points.length; i++) {
      const j = (i + 1) % points.length;
      area += points[i].lat * points[j].lng;
      area -= points[j].lat * points[i].lng;
    }
    return (Math.abs(area) * 0.000247105).toFixed(2); // Convert to acres
  }

  function zoomToPlot(plot) {
    if (!plot?.points?.length || !mapComponent) return;
    
    selectedPlotId = plot.id;
    
    // Clear any existing highlight layers
    clearPlotHighlights();
    
    // Create a LatLngBounds object to contain the polygon
    const bounds = L.latLngBounds(plot.points.map(p => [p.lat, p.lng]));
    
    // Fit the map to the bounds with some padding
    mapComponent.fitBounds(bounds, {
      padding: [50, 50],
      maxZoom: 18
    });
    
    // Add highlight layer
    const highlight = L.polygon(
      plot.points.map(p => [p.lat, p.lng]),
      {
        color: '#0d9488',
        weight: 3,
        opacity: 0.8,
        fillColor: '#0d9488',
        fillOpacity: 0.2
      }
    ).addTo(mapComponent);
    
    plotLayers.push(highlight);
    
    // Add a popup
    highlight.bindPopup(`
      <div class="plot-popup">
        <h3>${plot.plot_name || 'Unnamed Plot'}</h3>
        <p>ID: ${plot.id}</p>
        <p>Status: <span class="status-${plot.status || 'pending'}">${plot.status || 'Pending'}</span></p>
        <p>Area: ${calculateAreaFromPoints(plot.points)} acres</p>
      </div>
    `).openPopup();
  }

  function clearPlotHighlights() {
    plotLayers.forEach(layer => {
      if (mapComponent && layer) {
        mapComponent.removeLayer(layer);
      }
    });
    plotLayers = [];
  }

  // Update your existing onMount to include plot loading
  onMount(async () => {
    // ... existing onMount code ...
    
    // Load existing plots
    await loadPlots();
    
    // ... rest of your onMount code ...
  });

  // Add this function to load plots
  async function loadPlots() {
    try {
      const data = await fetchPlots();
      if (data) {
        existingPlots = Array.isArray(data) ? data : [];
        plots.set(existingPlots);
      }
    } catch (error) {
      console.error('Error loading plots:', error);
      status.set('Error loading plots. Please try again.');
    }
  }
</script>

<svelte:head>
	<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" crossorigin=""/>
	<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
</svelte:head>

<div class="app-container">
	<header class="app-header">
		<div class="header-content">
			<div class="logo-circle">
				<span>🌍</span>
			</div>
			<div>
				<h1>LandLock</h1>
				<p>Secure Land Registry for Malawi</p>
			</div>
		</div>
	</header>

	<main class="main-content">
		<div class="status-banner">
			<div class="status-icon">ℹ️</div>
			<div class="status-text">
				<div class="status-title">Current Status</div>
				<div>{currentStatus}</div>
			</div>
		</div>

		<div class="card">
			<h2><span>📝</span> Plot Information</h2>
			<div class="form-group">
				<label>Plot Name</label>
				<input type="text" placeholder="e.g., Family Farm, Main Homestead" bind:value={plotName} />
			</div>
			<div class="form-group">
				<label>Phone Number</label>
				<input type="tel" placeholder="265888123456" bind:value={ownerPhone} />
			</div>
			<button class="btn-primary" on:click={addPoint}>
				<span>📍</span> Add Corner (Use GPS)
			</button>

			<div class="divider">or click directly on the map</div>

			{#if points.length > 0}
				<button class="btn-clear" on:click={clearPoints}>
					<span>🗑️</span> Clear All Points
				</button>
			{/if}
		</div>
<div class="card">
  <h2><span>📋</span> My Plots</h2>
  <div class="plot-list">
    {#if existingPlots && existingPlots.length > 0}
      {#each existingPlots as plot}
        <div 
          class="plot-item" 
          class:active={selectedPlotId === plot.id}
          on:click={() => zoomToPlot(plot)}
        >
          <div class="plot-info">
            <h3>{plot.plot_name || 'Unnamed Plot'}</h3>
            <div class="plot-meta">
              <span>ID: {plot.id}</span>
              <span>{plot.points?.length || 0} points</span>
              <span>{calculateAreaFromPoints(plot.points || [])} acres</span>
            </div>
          </div>
          <div class="plot-status {plot.status || 'pending'}">
            {plot.status || 'Pending'}
          </div>
        </div>
      {/each}
    {:else}
      <div class="empty-state">
        <p>No plots found. Start by adding your first plot!</p>
      </div>
    {/if}
  </div>
</div>
		<div class="card map-card" class:fullscreen={isFullscreen}>
			<div class="map-header">
				<h2><span>🗺️</span> Interactive Map {#if mapReady}<span class="badge">Active</span>{/if}</h2>
				<button class="btn-secondary" on:click={toggleFullscreen}>
					{#if isFullscreen}<span>⤓</span> Exit Fullscreen{:else}<span>⤢</span> Fullscreen{/if}
				</button>
			</div>
			<div class="map-wrapper" style="height: {mapHeight}px;">
				<div id="map"></div>
				{#if !isFullscreen}
					<div class="resize-handle" on:mousedown={startResize}></div>
				{/if}
			</div>
		</div>

		{#if points.length > 0}
			<div class="summary-card">
				<div class="summary-header">
					<div>
						<h2><span>📐</span> Boundary Summary</h2>
						<p>{points.length} corner points recorded</p>
					</div>
					<div class="acre-badge">{calculateArea()} acres</div>
				</div>
				<div class="points-list">
					{#each points as p, i}
						<div class="point-item">
							<span class="point-number">{i + 1}</span>
							<span><strong>Lat:</strong> {p.lat.toFixed(6)} | <strong>Lng:</strong> {p.lng.toFixed(6)}</span>
						</div>
					{/each}
				</div>
			</div>
		{/if}

		{#if points.length >= 3}
			<button class="btn-submit" on:click={submitPlot}>
				<span>✅</span> Submit Plot for Review
			</button>
		{/if}

		<div class="footer-note">🔒 Your land data is securely recorded and protected</div>
	</main>
</div>

<style>
	/* =============== BASE =============== */
	:global(body) {
		margin: 0;
		padding: 0;
		font-family: 'Inter', sans-serif;
		background: #f0fdf4;
		color: #1e293b;
	}

	.app-container {
		min-height: 100vh;
		background: linear-gradient(to bottom, #f0fdf4, #e6f7ee);
	}

	/* =============== HEADER =============== */
	.app-header {
		background: white;
		box-shadow: 0 2px 6px rgba(0,0,0,0.05);
		border-bottom: 1px solid #e2e8f0;
		padding: 1.5rem 1rem;
	}
	.header-content {
		max-width: 1200px;
		margin: 0 auto;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 1rem;
	}
	.logo-circle {
		width: 3rem;
		height: 3rem;
		border-radius: 0.75rem;
		background: linear-gradient(135deg, #0d9488, #0b7a71);
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 1.5rem;
		box-shadow: 0 4px 8px rgba(13,148,136,0.25);
		color: white;
	}
	.app-header h1 {
		font-size: 1.875rem;
		font-weight: 700;
		background: linear-gradient(90deg, #0d9488, #0b7a71);
		background-clip: text;
		-webkit-background-clip: text;
		color: transparent;
	}
	.app-header p {
		font-size: 0.875rem;
		color: #64748b;
		font-weight: 600;
	}

	/* =============== LAYOUT =============== */
	.main-content {
		max-width: 1200px;
		margin: 2rem auto;
		padding: 0 1rem;
	}

	/* =============== CARDS =============== */
	.card {
		background: white;
		border-radius: 16px;
		box-shadow: 0 4px 12px rgba(0,0,0,0.04);
		border: 1px solid #e2e8f0;
		padding: 1.5rem;
		margin-bottom: 1.5rem;
	}

	/* =============== STATUS =============== */
	.status-banner {
		background: #f0f9ff;
		border: 1px solid #bae6fd;
		border-radius: 12px;
		padding: 1rem;
		display: flex;
		gap: 1rem;
		margin-bottom: 1.5rem;
	}
	.status-icon {
		width: 2.25rem;
		height: 2.25rem;
		border-radius: 50%;
		background: #dbeafe;
		display: flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
		font-size: 1.25rem;
	}
	.status-title {
		font-weight: 600;
		color: #1e3a8a;
		font-size: 0.875rem;
		margin-bottom: 0.25rem;
	}
	.status-text > div {
		font-size: 0.875rem;
		color: #1e40af;
	}

	/* =============== FORM =============== */
	.card h2 {
		font-size: 1.25rem;
		font-weight: 700;
		margin-bottom: 1.25rem;
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	.form-group {
		margin-bottom: 1.25rem;
	}
	.form-group label {
		display: block;
		font-weight: 600;
		font-size: 0.875rem;
		margin-bottom: 0.5rem;
		color: #334155;
	}
	.form-group input {
		width: 100%;
		padding: 0.875rem 1rem;
		border: 2px solid #e2e8f0;
		border-radius: 12px;
		font-size: 1rem;
		background: #f8fafc;
		transition: border-color 0.2s;
	}
	.form-group input:focus {
		outline: none;
		border-color: #0d9488;
		box-shadow: 0 0 0 3px rgba(13,148,136,0.15);
	}

	/* =============== BUTTONS =============== */
	.btn-primary {
		width: 100%;
		padding: 1rem;
		background: linear-gradient(135deg, #0d9488, #0b7a71);
		color: white;
		border: none;
		border-radius: 12px;
		font-weight: 600;
		font-size: 1rem;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.75rem;
		box-shadow: 0 4px 10px rgba(13,148,136,0.3);
		transition: all 0.2s;
	}
	.btn-primary:hover {
		background: linear-gradient(135deg, #0b7a71, #09615b);
		transform: translateY(-2px);
		box-shadow: 0 6px 14px rgba(13,148,136,0.4);
	}

	.btn-clear {
		width: 100%;
		padding: 0.9rem;
		background: white;
		color: #dc2626;
		border: 2px solid #fecaca;
		border-radius: 12px;
		font-weight: 600;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.75rem;
		transition: background 0.2s;
	}
	.btn-clear:hover {
		background: #fef2f2;
	}

	.btn-secondary {
		padding: 0.5rem 1rem;
		background: #f1f5f9;
		color: #475569;
		border: none;
		border-radius: 8px;
		font-weight: 600;
		font-size: 0.9rem;
		cursor: pointer;
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	.btn-secondary:hover {
		background: #e2e8f0;
	}

	.btn-submit {
		width: 100%;
		padding: 1.1rem;
		background: linear-gradient(135deg, #2563eb, #1d4ed8);
		color: white;
		border: none;
		border-radius: 16px;
		font-weight: 700;
		font-size: 1.1rem;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.75rem;
		box-shadow: 0 6px 16px rgba(37,99,235,0.3);
		transition: all 0.2s;
		margin-bottom: 2rem;
	}
	.btn-submit:hover {
		background: linear-gradient(135deg, #1d4ed8, #1e40af);
		transform: translateY(-2px);
		box-shadow: 0 8px 20px rgba(37,99,235,0.4);
	}

	/* =============== DIVIDER =============== */
	.divider {
		position: relative;
		text-align: center;
		color: #64748b;
		font-size: 0.875rem;
		font-weight: 500;
		margin: 1.5rem 0;
	}
	.divider::before {
		content: '';
		position: absolute;
		top: 50%;
		left: 0;
		right: 0;
		border-top: 1px solid #cbd5e1;
		z-index: 1;
	}
	.divider::after {
		content: attr(data-text);
		content: "or click directly on the map";
		background: white;
		padding: 0 0.75rem;
		position: relative;
		z-index: 2;
	}

	/* =============== MAP =============== */
	.map-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
		flex-wrap: wrap;
		gap: 0.5rem;
	}
	.badge {
		font-size: 0.75rem;
		background: #dcfce7;
		color: #166534;
		padding: 0.25rem 0.75rem;
		border-radius: 9999px;
		font-weight: 600;
	}
	.map-wrapper {
		position: relative;
		border-radius: 12px;
		overflow: hidden;
		border: 2px solid #e2e8f0;
		background: #f1f5f6;
	}
	#map {
		width: 100%;
		height: 100%;
		background: #f8fafc;
	}
	.resize-handle {
		position: absolute;
		bottom: 0;
		left: 0;
		right: 0;
		height: 24px;
		cursor: ns-resize;
		background: rgba(255,255,255,0.7);
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 18px;
		color: #0d9488;
		font-weight: bold;
	}

	/* Fullscreen */
	.fullscreen {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		z-index: 9999;
		margin: 0;
		border-radius: 0;
		padding: 1rem;
		max-width: 100%;
	}
	.fullscreen .map-wrapper {
		height: calc(100vh - 160px) !important;
	}

	/* =============== SUMMARY =============== */
	.summary-card {
		background: #f0fdf4;
		border: 1px solid #bbf7d0;
		border-radius: 16px;
		padding: 1.5rem;
		margin-bottom: 1.5rem;
	}
	.summary-header {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		margin-bottom: 1rem;
		flex-wrap: wrap;
		gap: 1rem;
	}
	.acre-badge {
		background: #0d9488;
		color: white;
		padding: 0.5rem 1rem;
		border-radius: 12px;
		font-weight: 700;
		font-size: 1.125rem;
		box-shadow: 0 4px 8px rgba(13,148,136,0.2);
	}
	.points-list {
		background: white;
		border-radius: 12px;
		padding: 1rem;
		border: 1px solid #e2e8f0;
		max-height: 12rem;
		overflow-y: auto;
	}
	.point-item {
		display: flex;
		gap: 0.75rem;
		padding: 0.75rem;
		background: #f8fafc;
		border-radius: 8px;
		font-size: 0.875rem;
		margin-bottom: 0.5rem;
	}
	.point-item:last-child {
		margin-bottom: 0;
	}
	.point-number {
		width: 24px;
		height: 24px;
		border-radius: 50%;
		background: #0d9488;
		color: white;
		display: flex;
		align-items: center;
		justify-content: center;
		font-weight: 600;
		font-size: 0.875rem;
		flex-shrink: 0;
	}

	/* =============== FOOTER =============== */
	.footer-note {
		text-align: center;
		font-size: 0.875rem;
		color: #64748b;
		margin-top: 1rem;
	}

	/* =============== LEAFLET FIX =============== */
	:global(.leaflet-container) {
		background: #f8fafc !important;
	}
	 .plot-list {
    display: grid;
    gap: 0.75rem;
    margin-top: 1rem;
  }

  .plot-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem;
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    cursor: pointer;
    transition: all 0.2s;
  }

  .plot-item:hover {
    border-color: #0d9488;
    box-shadow: 0 2px 8px rgba(13, 148, 136, 0.1);
    transform: translateY(-1px);
  }

  .plot-item.active {
    border-color: #0d9488;
    background: #f0fdf4;
  }

  .plot-info h3 {
    font-weight: 600;
    margin: 0 0 0.25rem 0;
    color: #1e293b;
  }

  .plot-meta {
    display: flex;
    gap: 1rem;
    font-size: 0.875rem;
    color: #64748b;
  }

  .plot-status {
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: capitalize;
  }

  .plot-status.pending {
    background: #fef3c7;
    color: #92400e;
  }

  .plot-status.approved {
    background: #dcfce7;
    color: #166534;
  }

  .plot-status.rejected {
    background: #fee2e2;
    color: #991b1b;
  }

  .empty-state {
    text-align: center;
    padding: 2rem;
    color: #64748b;
    background: #f8fafc;
    border-radius: 12px;
    border: 1px dashed #e2e8f0;
  }
</style>