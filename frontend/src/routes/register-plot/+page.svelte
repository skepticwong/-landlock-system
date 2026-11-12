<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { browser } from '$app/environment';
  import { status } from '$lib/store';
  import Navbar from '$lib/components/Navbar.svelte';
  import PaymentModal from '$lib/components/PaymentModal.svelte';

  const API = 'http://localhost:5000';

  let formData = {
    plotName: '',
    area: '',
    location: '',
    description: '',
    coordinates: '',
    plotType: 'private'
  };

  // Only officials see the government/military/city options
  let isOfficial = false;
  let plotTypeLocked = false;

  function authHeaders() {
    return { 'Authorization': `Bearer ${localStorage.getItem('token')}` };
  }

  onMount(async () => {
    if (!browser) return;

    if (!localStorage.getItem('token')) {
      goto('/login');
      return;
    }

    // Determine whether the current user is a land official
    try {
      const res = await fetch(`${API}/api/user/me`, { headers: authHeaders() });
      if (res.ok) {
        const u = await res.json();
        isOfficial = !!(u.is_staff || u.is_superuser);
        if (!isOfficial) {
          // Citizens cannot choose state plot types
          plotTypeLocked = true;
          formData.plotType = 'private';
        }
      }
    } catch (err) {
      console.error('Error verifying role:', err);
    }

    // Initialize map for location selection
    initializeMap();
  });

  let isLoading = false;
  let error = '';
  let map: any = null;
  let mapPoints: any[] = [];
  let boundaryLayer: any = null;
  let pointMarkers: any[] = [];
  
  // Payment state
  let showPaymentModal = false;
  let paymentType = 'land_registration';
  let paymentAmount = 5000;
  let paymentDescription = 'Land Registration Fee';
  let pendingPlotData: any = null;

  import { initMap } from '$lib/map';
  import { tick } from 'svelte';
  import { calculatePolygonArea, formatArea, detectDistrict, detectVillage, loadDistrictBoundaries } from '$lib/geo';

  let autoArea: number | null = null;
  let autoDistrict: string | null = null;
  let autoVillage: { village: string, area_id: string, district_id: string } | null = null;

  function updateAutoInfo() {
    // Auto-calculate area in m² from the plotted boundary
    if (mapPoints.length >= 3) {
      autoArea = calculatePolygonArea(mapPoints);
      if (autoArea > 0) formData.area = autoArea.toFixed(1);
    } else {
      autoArea = null;
      formData.area = '';
    }
    // Auto-detect the district from the plotted location (centroid)
    if (mapPoints.length >= 1) {
      const centroid = {
        lat: mapPoints.reduce((s, p) => s + p.lat, 0) / mapPoints.length,
        lng: mapPoints.reduce((s, p) => s + p.lng, 0) / mapPoints.length
      };
      detectDistrict(centroid).then(d => {
        autoDistrict = d;
        if (d && !formData.location) formData.location = d;
      });
      detectVillage(centroid).then(v => {
        autoVillage = v;
        if (v) formData.location = v.village;
      });
    } else {
      autoDistrict = null;
      autoVillage = null;
    }
  }

  function initializeMap() {
    tick().then(async () => {
      const mapEl = document.getElementById('location-map');
      if (mapEl) {
        try {
          // Pre-fetch district boundaries so detection is instant on first click
          loadDistrictBoundaries();
          const mapModule = await import('$lib/map');
          map = await mapModule.initMap(mapEl, async (e: any) => {
            mapPoints = [...mapPoints, e.latlng];
            formData.coordinates = mapPoints.map(p => `${p.lat.toFixed(6)}, ${p.lng.toFixed(6)}`).join('; ');
            if (boundaryLayer && map) {
              map.removeLayer(boundaryLayer);
              boundaryLayer = null;
            }
            if (mapPoints.length >= 3) {
              boundaryLayer = mapModule.addPolyline(map, mapPoints, '#22c55e');
            }
            // Drop a numbered marker at the clicked point
            const L = (await import('leaflet')).default || (await import('leaflet'));
            const idx = mapPoints.length;
            const icon = L.divIcon({
              className: '',
              html: `<div style="width:24px;height:24px;border-radius:50%;background:#22c55e;border:2px solid white;box-shadow:0 1px 4px rgba(0,0,0,.35);display:flex;align-items:center;justify-content:center;color:white;font-size:12px;font-weight:700;">${idx}</div>`,
              iconSize: [24, 24],
              iconAnchor: [12, 12]
            });
            const marker = L.marker([e.latlng.lat, e.latlng.lng], { icon }).addTo(map);
            pointMarkers = [...pointMarkers, marker];
            // Keep view centred on the newest point
            map.panTo([e.latlng.lat, e.latlng.lng]);
            updateAutoInfo();
          });
          // Make sure the map is correctly sized after the container settles
          setTimeout(() => map && map.invalidateSize(), 200);
        } catch (err) {
          console.error('Failed to init map in register-plot', err);
        }
      }
    });
  }

  function clearMapPoints() {
    mapPoints = [];
    formData.coordinates = '';
    pointMarkers.forEach(m => map && map.removeLayer(m));
    pointMarkers = [];
    if (boundaryLayer && map) {
      map.removeLayer(boundaryLayer);
      boundaryLayer = null;
    }
    updateAutoInfo();
  }

  function undoLastPoint() {
    if (mapPoints.length === 0) return;
    mapPoints = mapPoints.slice(0, -1);
    const last = pointMarkers.pop();
    if (last && map) map.removeLayer(last);
    formData.coordinates = mapPoints.map(p => `${p.lat.toFixed(6)}, ${p.lng.toFixed(6)}`).join('; ');
    if (boundaryLayer && map) {
      map.removeLayer(boundaryLayer);
      boundaryLayer = null;
    }
    if (mapPoints.length >= 3) {
      import('$lib/map').then(mod => {
        boundaryLayer = mod.addPolyline(map, mapPoints, '#22c55e');
      });
    }
    updateAutoInfo();
  }

  async function handleSubmit() {
    if (!formData.plotName) {
      error = 'Please fill in all required fields';
      return;
    }

    if (mapPoints.length < 3) {
      error = 'Please plot at least 3 boundary points on the map (click the map to add each corner).';
      return;
    }

    // Store plot data and show payment modal
    pendingPlotData = {
      plot_name: formData.plotName,
      area: formData.area ? parseFloat(formData.area) : null,
      location: formData.location,
      description: formData.description,
      // Auto-detected geography so chiefs can match this plot to their jurisdiction
      district: autoDistrict || formData.location || null,
      village: autoVillage?.village || null,
      // State-held land (officials only) — locked after creation
      plot_type: formData.plotType || 'private',
      // Backend requires a 'points' array of boundary coordinates
      points: mapPoints.map(p => ({ lat: p.lat, lng: p.lng }))
    };
    
    // State plots are registered by officials directly — no citizen fee applies
    if (isOfficial && formData.plotType && formData.plotType !== 'private') {
      await submitPlot(null);
      return;
    }

    showPaymentModal = true;
  }

  async function submitPlot(payment: any | null) {
    isLoading = true;
    error = '';

    try {
      const response = await fetch(`${API}/api/plots`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          ...pendingPlotData,
          ...(payment ? { payment_id: payment.id } : {})
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Registration failed');
      }

      status.set('Plot registered successfully!');
      setTimeout(() => {
        goto('/dashboard');
      }, 1500);
    } catch (err: any) {
      error = err.message;
      status.set('Registration failed: ' + err.message);
    } finally {
      isLoading = false;
      pendingPlotData = null;
    }
  }

  function handleCancel() {
    goto('/dashboard');
  }

  // Called by PaymentModal after citizen registration fee is paid
  async function handlePaymentCompleted(event: any) {
    await submitPlot(event.detail.payment);
  }
</script>

<svelte:head>
  <title>Register Plot - LandLock</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</svelte:head>

<div class="register-plot-container">
  <Navbar userType="official" activeLink="/register-plot" userName="Official" showNotification={false} />

  <main class="main-content">
    <div class="page-header">
      <h1>Register New Plot</h1>
      <p>Add your land plot to the registry</p>
    </div>

    {#if error}
      <div class="error-message">
        {error}
      </div>
    {/if}

    <form class="registration-form" on:submit|preventDefault={handleSubmit}>
      <div class="form-grid">
        <div class="form-group">
          <label for="plotName">Plot Name *</label>
          <input
            id="plotName"
            type="text"
            bind:value={formData.plotName}
            placeholder="Enter plot name"
            required
          />
        </div>

        <div class="form-group">
          <label for="area">Area (m²) <span class="auto-tag" style="color:#007A3D;font-weight:600;">✓ auto-calculated</span></label>
          <input
            id="area"
            type="number"
            bind:value={formData.area}
            placeholder="Plotted automatically from map boundary"
            step="0.1"
          />
          {#if autoArea !== null}
            <small class="auto-hint">Boundary area: <strong>{formatArea(autoArea)}</strong> — you may override if you have a surveyed figure.</small>
          {:else}
            <small class="auto-hint">Plot at least 3 boundary points on the map below and the area is calculated automatically.</small>
          {/if}
        </div>

        <div class="form-group">
          <label for="location">District / Location <span class="auto-tag" style="color:#007A3D;font-weight:600;">✓ auto-detected</span></label>
          <input
            id="location"
            type="text"
            bind:value={formData.location}
            placeholder="Detected from map boundary"
          />
          {#if autoDistrict}
            <small class="auto-hint">Plot falls inside <strong>{autoDistrict} district</strong> (detected from plotted boundary). You may change it if needed.</small>
          {:else}
            <small class="auto-hint">Detected automatically once you plot the boundary on the map below.</small>
          {/if}
        </div>

        <div class="form-group">
          <label for="coordinates">GPS Coordinates</label>
          <input
            id="coordinates"
            type="text"
            bind:value={formData.coordinates}
            placeholder="Latitude, Longitude"
          />
        </div>

        <div class="form-group">
          <label for="plotType">Plot Type</label>
          <select
            id="plotType"
            bind:value={formData.plotType}
            disabled={plotTypeLocked}
          >
            <option value="private">Private / Citizen Land</option>
            {#if isOfficial}
              <option value="government">Government Land</option>
              <option value="military">Military Land</option>
              <option value="city">City / Municipal Land</option>
            {/if}
          </select>
          {#if isOfficial && formData.plotType !== 'private'}
            <small class="auto-hint" style="color:#b91c1c;">
              ⚠ State land will be locked: no one (including its owner) will be able to edit, sell, lease or transfer it. Only officials can manage it.
            </small>
          {/if}
        </div>
      </div>

      <div class="form-group">
        <label for="description">Description</label>
        <textarea
          id="description"
          bind:value={formData.description}
          placeholder="Describe the plot, landmarks, etc."
          rows="4"
        ></textarea>
      </div>

      <div class="map-section" style="margin-bottom: 2rem;">
        <h3>Select Plot Location</h3>
        <p class="text-sm text-gray-500 mb-2">Click on the map to plot each corner of the plot boundary. Add at least 3 points to form the boundary.</p>
        {#if mapPoints.length > 0}
          <div class="points-status">
            <span class="points-badge {mapPoints.length >= 3 ? 'ok' : ''}">{mapPoints.length} point{mapPoints.length !== 1 ? 's' : ''} plotted{mapPoints.length >= 3 ? ' — boundary ready' : ' — need at least 3'}</span>
            {#if autoArea !== null}
              <span class="points-badge area-badge">Area: {formatArea(autoArea)}</span>
            {/if}
            {#if autoDistrict}
              <span class="points-badge area-badge">📍 {autoDistrict}</span>
            {/if}
            {#if autoVillage}
              <span class="points-badge area-badge">🏘 {autoVillage.village}</span>
            {/if}
            <button type="button" class="map-btn" on:click={undoLastPoint}>↶ Undo last</button>
            <button type="button" class="map-btn" on:click={clearMapPoints}>Clear all</button>
          </div>
        {/if}
        <div id="location-map" class="map-large" style="z-index: 1;"></div>
      </div>

      <div class="form-actions">
        <button type="button" class="btn-cancel" on:click={handleCancel}>
          Cancel
        </button>
        <button type="submit" class="btn-submit" disabled={isLoading}>
          {isLoading ? 'Registering...' : 'Register Plot'}
        </button>
      </div>
    </form>
  </main>

  <PaymentModal
    bind:isOpen={showPaymentModal}
    paymentType={paymentType}
    amount={paymentAmount}
    description={paymentDescription}
    on:paymentCompleted={handlePaymentCompleted}
  />
</div>

<style>
  :global(body) {
    margin: 0;
    padding: 0;
    font-family: 'Inter', sans-serif;
    background: #f8faf9;
  }

  .register-plot-container {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  .main-content {
    max-width: 1400px;
    margin: 0 auto;
    padding: 2rem;
    width: 100%;
    flex: 1;
  }

  .page-header {
    text-align: center;
    margin-bottom: 2rem;
  }

  .page-header h1 {
    font-size: 2rem;
    font-weight: 700;
    color: #1e293b;
    margin: 0 0 0.5rem 0;
  }

  .page-header p {
    color: #64748b;
    font-size: 1rem;
  }

  .error-message {
    background: #fee2e2;
    color: #dc2626;
    padding: 1rem;
    border-radius: 8px;
    margin-bottom: 1.5rem;
    border: 1px solid #fecaca;
  }

  .registration-form {
    background: white;
    border-radius: 12px;
    padding: 2rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    border: 1px solid #e2e8f0;
    margin-bottom: 2rem;
  }

  .form-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1.5rem;
    margin-bottom: 1.5rem;
  }

  .form-group {
    display: flex;
    flex-direction: column;
  }

  .form-group label {
    font-weight: 600;
    color: #374151;
    margin-bottom: 0.5rem;
    font-size: 0.875rem;
  }

  .form-group input,
  .form-group textarea {
    padding: 0.75rem;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    font-size: 1rem;
    transition: border-color 0.2s;
  }

  .form-group input:focus,
  .form-group textarea:focus {
    outline: none;
    border-color: var(--color-primary);
    box-shadow: 0 0 0 3px rgba(0, 122, 61, 0.15);
  }

  .form-group textarea {
    resize: vertical;
  }

  .form-actions {
    display: flex;
    gap: 1rem;
    justify-content: flex-end;
    margin-top: 2rem;
  }

  .btn-cancel {
    padding: 0.75rem 1.5rem;
    border: 1px solid #d1d5db;
    background: white;
    color: #374151;
    border-radius: 6px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
  }

  .btn-cancel:hover {
    background: #f3f4f6;
  }

  .btn-submit {
    padding: 0.75rem 1.5rem;
    border: none;
    background: var(--color-primary);
    color: white;
    border-radius: 6px;
    font-weight: 500;
    cursor: pointer;
    transition: background-color 0.2s;
  }

  .btn-submit:hover:not(:disabled) {
    background: var(--color-primary-hover);
  }

  .btn-submit:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .map-section {
    background: white;
    border-radius: 12px;
    padding: 2rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    border: 1px solid #e2e8f0;
  }

  .map-section h3 {
    font-size: 1.125rem;
    font-weight: 600;
    color: #374151;
    margin: 0 0 1rem 0;
  }

  .map-large {
    cursor: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='28' height='28' viewBox='0 0 24 24' fill='%2322c55e' stroke='white' stroke-width='1.5'><path d='M12 19l7-7 3 3-7 7-3-3z'/><path d='M18 13l-1.5-7.5L2 2l3.5 14.5L13 18l5-5z'/><circle cx='11' cy='11' r='2'/></svg>") 2 2, crosshair;
    height: 70vh;
    min-height: 550px;
    width: 100%;
    background: #f3f4f6;
    border: 2px solid #e2e8f0;
    border-radius: 8px;
  }

  .points-status {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 0.75rem;
    flex-wrap: wrap;
  }

  .points-badge {
    padding: 0.35rem 0.75rem;
    border-radius: 999px;
    font-size: 0.8125rem;
    font-weight: 600;
    background: #fef3c7;
    color: #92400e;
  }

  .points-badge.ok {
    background: #dcfce7;
    color: #166534;
  }

  .area-badge {
    background: #e0f2fe;
    color: #075985;
  }

  .auto-hint {
    margin-top: 0.35rem;
    font-size: 0.8125rem;
    color: #64748b;
  }

  .auto-tag {
    font-size: 0.75rem;
    text-transform: none;
    letter-spacing: 0;
  }

  .map-btn {
    padding: 0.35rem 0.75rem;
    border: 1px solid #d1d5db;
    background: white;
    color: #374151;
    border-radius: 6px;
    font-size: 0.8125rem;
    font-weight: 500;
    cursor: pointer;
  }

  .map-btn:hover {
    background: #f3f4f6;
  }

  @media (max-width: 768px) {
    .register-plot-container {
      margin: 1rem auto;
    }

    .form-grid {
      grid-template-columns: 1fr;
    }

    .form-actions {
      flex-direction: column;
    }

    .btn-cancel,
    .btn-submit {
      width: 100%;
    }
  }
</style>
