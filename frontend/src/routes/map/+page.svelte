<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { browser } from '$app/environment';
  import Navbar from '$lib/components/Navbar.svelte';
  import { MapPin, List, Map, Search, ChevronRight, Calendar, User, Layers } from 'lucide-svelte';

  const API = 'http://localhost:5000';

  // ─── State ─────────────────────────────────────────────────────────────────
  let currentUser: any = null;
  let plots: any[] = [];
  let districts: string[] = [];
  let isLoading = true;
  let viewMode: 'map' | 'list' = 'map';
  let filterStatus = 'all';
  let filterDistrict = 'all';
  let searchQuery = '';
  let leafletMap: any = null;
  let markers: any[] = [];

  const statuses = [
    { value: 'all',      label: 'All Plots',  color: '#64748b' },
    { value: 'pending',  label: 'Pending',    color: '#f59e0b' },
    { value: 'approve',  label: 'Approved',   color: '#10b981' },
    { value: 'verified', label: 'Verified',   color: '#007A3D' },
    { value: 'reject',   label: 'Rejected',   color: '#ef4444' },
  ];

  // ─── Auth ───────────────────────────────────────────────────────────────────
  function authHeaders() {
    return { 'Authorization': `Bearer ${localStorage.getItem('token')}` };
  }

  // ─── Data fetching ──────────────────────────────────────────────────────────
  async function fetchPlots() {
    try {
      const res = await fetch(`${API}/api/official/caseload`, { headers: authHeaders() });
      if (res.ok) {
        plots = await res.json();
      }
    } catch (err) {
      console.error('Error fetching plots:', err);
    }
  }

  async function fetchDistricts() {
    try {
      const res = await fetch(`${API}/api/districts`);
      if (res.ok) districts = await res.json();
    } catch (err) {
      console.error('Error fetching districts:', err);
    }
  }

  // ─── Filtering ──────────────────────────────────────────────────────────────
  $: filtered = plots.filter(p => {
    const byStatus   = filterStatus === 'all'    || p.status === filterStatus;
    const byDistrict = filterDistrict === 'all'  || (p.district || '').toLowerCase() === filterDistrict.toLowerCase();
    const q = searchQuery.toLowerCase();
    const bySearch   = !q || p.plot_name?.toLowerCase().includes(q) ||
                       p.claimant?.toLowerCase().includes(q) ||
                       (p.district || '').toLowerCase().includes(q) ||
                       (p.village || '').toLowerCase().includes(q);
    return byStatus && byDistrict && bySearch;
  });

  // ─── Status helpers ─────────────────────────────────────────────────────────
  function getStatusColor(s: string) {
    return statuses.find(x => x.value === s)?.color ?? '#64748b';
  }

  function getStatusLabel(s: string) {
    const map: Record<string, string> = {
      pending: 'Pending', approve: 'Approved', verified: 'Verified', reject: 'Rejected'
    };
    return map[s] ?? s;
  }

  // ─── Map ─────────────────────────────────────────────────────────────────────
  async function initMap() {
    if (!browser) return;
    const mapEl = document.getElementById('leaflet-map');
    if (!mapEl) return;

    const L = (await import('leaflet')).default;
    if (leafletMap) { leafletMap.remove(); leafletMap = null; }

    leafletMap = L.map('leaflet-map', {
      center: [-13.2543, 34.3015],
      zoom: 7,
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors'
    }).addTo(leafletMap);

    renderMarkers(L);
  }

  function renderMarkers(L: any) {
    if (!leafletMap) return;
    markers.forEach(m => m.remove());
    markers = [];

    filtered.forEach(plot => {
      const pts = plot.points;
      if (!pts || pts.length === 0) return;

      // Use centroid of polygon points
      const latSum = pts.reduce((s: number, p: any) => s + p.lat, 0);
      const lngSum = pts.reduce((s: number, p: any) => s + p.lng, 0);
      const lat = latSum / pts.length;
      const lng = lngSum / pts.length;
      if (!lat || !lng) return;

      const color = getStatusColor(plot.status);

      // Draw boundary polygon
      const latlngs = pts.map((p: any) => [p.lat, p.lng]);
      const polygon = L.polygon(latlngs, {
        color: color,
        fillColor: color,
        fillOpacity: 0.15,
        weight: 2,
        dashArray: '5, 5'
      }).addTo(leafletMap);
      polygon.plotId = plot.id;

      const popupContent = `
        <div style="min-width:200px;font-family:system-ui,sans-serif;">
          <div style="font-weight:700;font-size:14px;margin-bottom:6px;">${plot.plot_name || 'Unnamed Plot'}</div>
          <div style="font-size:12px;color:#64748b;margin-bottom:3px;"><b>Owner:</b> ${plot.claimant || '—'}</div>
          <div style="font-size:12px;color:#64748b;margin-bottom:3px;"><b>District:</b> ${plot.district || '—'}</div>
          <div style="font-size:12px;color:#64748b;margin-bottom:3px;"><b>Village:</b> ${plot.village || '—'}</div>
          <div style="margin-top:6px;">
            <span style="background:${color};color:white;padding:2px 8px;border-radius:999px;font-size:11px;font-weight:600;">
              ${getStatusLabel(plot.status)}
            </span>
          </div>
        </div>
      `;

      polygon.bindPopup(popupContent);

      // Draw marker icon at centroid
      const icon = L.divIcon({
        className: '',
        html: `<div style="
          width:28px;height:28px;border-radius:50%;
          background:${color};border:3px solid white;
          box-shadow:0 2px 6px rgba(0,0,0,0.3);
          display:flex;align-items:center;justify-content:center;
        "></div>`,
        iconSize: [28, 28],
        iconAnchor: [14, 14],
      });

      const marker = L.marker([lat, lng], { icon }).addTo(leafletMap);
      marker.plotId = plot.id;
      marker.isMarker = true;
      marker.bindPopup(popupContent);

      markers.push(polygon);
      markers.push(marker);
    });
  }

  // Re-render markers whenever filters change while in map mode
  $: if (browser && leafletMap && viewMode === 'map') {
    import('leaflet').then(mod => renderMarkers(mod.default));
  }

  // Switch to map view → init or re-init
  async function switchToMap() {
    viewMode = 'map';
    await new Promise(r => setTimeout(r, 50)); // wait for DOM
    await initMap();
  }

  async function viewPlotOnMap(plot: any) {
    const pts = plot.points;
    if (!pts || pts.length === 0) return;

    const latSum = pts.reduce((s: number, p: any) => s + p.lat, 0);
    const lngSum = pts.reduce((s: number, p: any) => s + p.lng, 0);
    const lat = latSum / pts.length;
    const lng = lngSum / pts.length;
    if (!lat || !lng) return;

    viewMode = 'map';
    await new Promise(r => setTimeout(r, 100)); // wait for DOM update

    if (!leafletMap) {
      await initMap();
    }

    if (leafletMap) {
      leafletMap.setView([lat, lng], 15);
      const targetMarker = markers.find(m => m.plotId === plot.id && m.isMarker);
      if (targetMarker) {
        targetMarker.openPopup();
      }
    }
  }

  // ─── onMount ────────────────────────────────────────────────────────────────
  onMount(async () => {
    if (!browser) return;
    if (!localStorage.getItem('token')) { goto('/login'); return; }

    try {
      const res = await fetch(`${API}/api/user/me`, { headers: authHeaders() });
      if (res.ok) {
        currentUser = await res.json();
        if (!currentUser.is_superuser && !currentUser.is_staff) {
          goto('/dashboard'); return;
        }
      } else {
        goto('/login'); return;
      }
    } catch { goto('/login'); return; }

    isLoading = true;
    await Promise.all([fetchPlots(), fetchDistricts()]);
    isLoading = false;

    // Give DOM time to paint before init
    setTimeout(() => initMap(), 100);
  });

  // Formatted date
  function fmtDate(iso: string) {
    if (!iso) return '—';
    return new Date(iso).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
  }
</script>

<svelte:head>
  <title>Map View – LandLock</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
</svelte:head>

<div class="page">
  <Navbar
    userType="official"
    activeLink="/map"
    userName={currentUser?.full_name || 'Official'}
  />

  <div class="content">
    <!-- ── Top bar ─────────────────────────────────────────── -->
    <div class="topbar">
      <div class="topbar-left">
        <h1 class="page-title">
          <MapPin class="title-icon" />
          Plots Map View
        </h1>
        <p class="page-subtitle">Browse all registered plots by district and status</p>
      </div>

      <!-- View toggle -->
      <div class="view-toggle">
        <button
          class="toggle-btn {viewMode === 'map' ? 'active' : ''}"
          on:click={switchToMap}
          title="Map view"
        >
          <Map size={16} /> Map
        </button>
        <button
          class="toggle-btn {viewMode === 'list' ? 'active' : ''}"
          on:click={() => (viewMode = 'list')}
          title="List view"
        >
          <List size={16} /> List
        </button>
      </div>
    </div>

    <!-- ── Filter bar ──────────────────────────────────────── -->
    <div class="filter-bar">
      <!-- Status chips -->
      <div class="status-chips">
        {#each statuses as s}
          <button
            class="chip {filterStatus === s.value ? 'chip-active' : ''}"
            style="--chip-color: {s.color}"
            on:click={() => (filterStatus = s.value)}
          >
            <span class="chip-dot" style="background:{s.color}"></span>
            {s.label}
            <span class="chip-count">
              {s.value === 'all' ? plots.length : plots.filter(p => p.status === s.value).length}
            </span>
          </button>
        {/each}
      </div>

      <!-- District + search -->
      <div class="right-filters">
        <div class="search-wrap">
          <Search size={15} class="search-icon" />
          <input
            class="search-input"
            type="text"
            placeholder="Search plots…"
            bind:value={searchQuery}
          />
        </div>
        <select class="district-select" bind:value={filterDistrict}>
          <option value="all">All Districts</option>
          {#each districts as d}
            <option value={d.toLowerCase()}>{d}</option>
          {/each}
        </select>
      </div>
    </div>

    <!-- ── Result count ────────────────────────────────────── -->
    <div class="result-bar">
      <span class="result-count">{filtered.length} plot{filtered.length !== 1 ? 's' : ''}</span>
      {#if filterStatus !== 'all' || filterDistrict !== 'all' || searchQuery}
        <button class="clear-btn" on:click={() => { filterStatus='all'; filterDistrict='all'; searchQuery=''; }}>
          Clear filters
        </button>
      {/if}
    </div>

    {#if isLoading}
      <div class="loader">
        <div class="spinner"></div>
        <p>Loading plots…</p>
      </div>

    {:else if viewMode === 'map'}
      <!-- ── Map view ────────────────────────────────────────── -->
      <div class="map-wrap">
        <!-- Legend -->
        <div class="legend">
          {#each statuses.filter(s => s.value !== 'all') as s}
            <div class="legend-item">
              <span class="legend-dot" style="background:{s.color}"></span>
              {s.label}
            </div>
          {/each}
        </div>
        <div id="leaflet-map" class="leaflet-map"></div>
        {#if filtered.length === 0}
          <div class="map-empty">No plots match the current filters</div>
        {/if}
      </div>

    {:else}
      <!-- ── List view ───────────────────────────────────────── -->
      {#if filtered.length === 0}
        <div class="empty-state">
          <MapPin size={48} class="empty-icon" />
          <h3>No plots found</h3>
          <p>Try changing the status filter or district</p>
        </div>
      {:else}
        <div class="list-grid">
          {#each filtered as plot (plot.id)}
            <div class="plot-card">
              <div class="card-top">
                <div class="card-info">
                  <div class="plot-id">MLW-{plot.id}</div>
                  <h3 class="plot-name">{plot.plot_name || 'Unnamed Plot'}</h3>
                </div>
                <span
                  class="status-badge"
                  style="background:{getStatusColor(plot.status)}20;color:{getStatusColor(plot.status)};border-color:{getStatusColor(plot.status)}40"
                >
                  {getStatusLabel(plot.status)}
                </span>
              </div>

              <div class="card-meta">
                <div class="meta-row">
                  <User size={13} class="meta-icon" />
                  <span>{plot.claimant || '—'}</span>
                </div>
                <div class="meta-row">
                  <Layers size={13} class="meta-icon" />
                  <span>{plot.district || '—'}{plot.village ? `, ${plot.village}` : ''}</span>
                </div>
                <div class="meta-row">
                  <Calendar size={13} class="meta-icon" />
                  <span>{fmtDate(plot.submittedDate)}</span>
                </div>
              </div>

              {#if plot.points?.length}
                <div class="coord-note-wrapper">
                  <div class="coord-note">
                    <MapPin size={11} />
                    {plot.points.length} boundary point{plot.points.length !== 1 ? 's' : ''}
                  </div>
                  <button class="view-map-btn" on:click|stopPropagation={() => viewPlotOnMap(plot)}>
                    View on Map →
                  </button>
                </div>
              {/if}
            </div>
          {/each}
        </div>
      {/if}
    {/if}
  </div>
</div>

<style>
  /* ── Base ────────────────────────────────────────────────── */
  .page {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    background: #f8fafc;
  }

  .content {
    max-width: 1400px;
    margin: 0 auto;
    padding: 2rem;
    width: 100%;
    flex: 1;
  }

  /* ── Top bar ─────────────────────────────────────────────── */
  .topbar {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 1.5rem;
    gap: 1rem;
    flex-wrap: wrap;
  }

  .page-title {
    font-size: 1.875rem;
    font-weight: 700;
    color: #0f172a;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.25rem;
  }

  .title-icon {
    color: #007A3D;
    width: 26px;
    height: 26px;
  }

  .page-subtitle {
    color: #64748b;
    font-size: 0.9375rem;
  }

  /* ── View toggle ─────────────────────────────────────────── */
  .view-toggle {
    display: flex;
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 4px;
    gap: 2px;
    flex-shrink: 0;
    align-self: flex-start;
    margin-top: 4px;
  }

  .toggle-btn {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 0.4rem 0.9rem;
    border-radius: 7px;
    border: none;
    background: transparent;
    color: #64748b;
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
  }

  .toggle-btn.active {
    background: #007A3D;
    color: white;
    box-shadow: 0 1px 4px rgba(0,122,61,0.35);
  }

  /* ── Filter bar ──────────────────────────────────────────── */
  .filter-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1rem;
    flex-wrap: wrap;
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 0.875rem 1.25rem;
  }

  .status-chips {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  .chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 0.35rem 0.8rem;
    border-radius: 999px;
    border: 1.5px solid #e2e8f0;
    background: #f8fafc;
    color: #475569;
    font-size: 0.8125rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.18s;
  }

  .chip:hover {
    border-color: var(--chip-color);
    color: var(--chip-color);
  }

  .chip-active {
    background: var(--chip-color);
    border-color: var(--chip-color);
    color: white !important;
  }

  .chip-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
  }

  .chip-active .chip-dot {
    background: rgba(255,255,255,0.7) !important;
  }

  .chip-count {
    background: rgba(0,0,0,0.08);
    border-radius: 999px;
    padding: 0 6px;
    font-size: 0.75rem;
    font-weight: 600;
  }

  .chip-active .chip-count {
    background: rgba(255,255,255,0.25);
  }

  /* ── Right filters ───────────────────────────────────────── */
  .right-filters {
    display: flex;
    gap: 0.625rem;
    align-items: center;
    flex-shrink: 0;
  }

  .search-wrap {
    position: relative;
    display: flex;
    align-items: center;
  }

  .search-wrap :global(.search-icon) {
    position: absolute;
    left: 10px;
    color: #94a3b8;
    pointer-events: none;
  }

  .search-input {
    padding: 0.45rem 0.75rem 0.45rem 2rem;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    font-size: 0.875rem;
    width: 220px;
    outline: none;
    transition: border-color 0.2s;
    background: #f8fafc;
  }

  .search-input:focus {
    border-color: #007A3D;
    background: white;
  }

  .district-select {
    padding: 0.45rem 0.75rem;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    font-size: 0.875rem;
    background: #f8fafc;
    cursor: pointer;
    outline: none;
    transition: border-color 0.2s;
  }

  .district-select:focus {
    border-color: #007A3D;
  }

  /* ── Result bar ──────────────────────────────────────────── */
  .result-bar {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1rem;
  }

  .result-count {
    font-size: 0.875rem;
    color: #64748b;
    font-weight: 500;
  }

  .clear-btn {
    font-size: 0.8125rem;
    color: #ef4444;
    background: none;
    border: none;
    cursor: pointer;
    font-weight: 500;
    padding: 0;
  }

  .clear-btn:hover { text-decoration: underline; }

  /* ── Loader ──────────────────────────────────────────────── */
  .loader {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 5rem 2rem;
    color: #64748b;
  }

  .spinner {
    width: 44px;
    height: 44px;
    border: 4px solid #e2e8f0;
    border-top-color: #007A3D;
    border-radius: 50%;
    animation: spin 0.9s linear infinite;
    margin-bottom: 1rem;
  }

  @keyframes spin { to { transform: rotate(360deg); } }

  /* ── Map ─────────────────────────────────────────────────── */
  .map-wrap {
    position: relative;
    border-radius: 14px;
    overflow: hidden;
    border: 1px solid #e2e8f0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  }

  .leaflet-map {
    width: 100%;
    height: 620px;
  }

  :global(.leaflet-container) {
    height: 100%;
    width: 100%;
    border-radius: 14px;
  }

  .legend {
    position: absolute;
    top: 12px;
    right: 12px;
    z-index: 1000;
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 0.625rem 1rem;
    display: flex;
    flex-direction: column;
    gap: 6px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  }

  .legend-item {
    display: flex;
    align-items: center;
    gap: 7px;
    font-size: 0.8125rem;
    color: #334155;
    font-weight: 500;
  }

  .legend-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    border: 2px solid white;
    box-shadow: 0 1px 3px rgba(0,0,0,0.2);
    flex-shrink: 0;
  }

  .map-empty {
    position: absolute;
    bottom: 20px;
    left: 50%;
    transform: translateX(-50%);
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 0.5rem 1.25rem;
    font-size: 0.875rem;
    color: #64748b;
    z-index: 1000;
    box-shadow: 0 2px 6px rgba(0,0,0,0.1);
  }

  /* ── List grid ───────────────────────────────────────────── */
  .list-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 1.125rem;
  }

  .plot-card {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1.25rem;
    transition: box-shadow 0.2s, transform 0.2s;
    cursor: default;
  }

  .plot-card:hover {
    box-shadow: 0 6px 20px rgba(0,0,0,0.08);
    transform: translateY(-2px);
  }

  .card-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 0.875rem;
    gap: 0.5rem;
  }

  .plot-id {
    font-size: 0.75rem;
    color: #94a3b8;
    font-weight: 600;
    letter-spacing: 0.05em;
    margin-bottom: 2px;
  }

  .plot-name {
    font-size: 1rem;
    font-weight: 600;
    color: #0f172a;
    line-height: 1.3;
  }

  .status-badge {
    display: inline-block;
    padding: 0.2rem 0.65rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
    border: 1px solid;
    white-space: nowrap;
    flex-shrink: 0;
  }

  .card-meta {
    display: flex;
    flex-direction: column;
    gap: 6px;
    margin-bottom: 0.75rem;
  }

  .meta-row {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.8125rem;
    color: #475569;
  }

  .meta-row :global(.meta-icon) {
    color: #94a3b8;
    flex-shrink: 0;
  }

  .coord-note-wrapper {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 0.625rem;
    border-top: 1px solid #f1f5f9;
  }

  .coord-note {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 0.75rem;
    color: #94a3b8;
  }

  .view-map-btn {
    font-size: 0.75rem;
    color: #007A3D;
    background: none;
    border: none;
    cursor: pointer;
    font-weight: 600;
    padding: 0;
    transition: color 0.2s;
  }

  .view-map-btn:hover {
    color: #005C2E;
    text-decoration: underline;
  }

  /* ── Empty state ─────────────────────────────────────────── */
  .empty-state {
    text-align: center;
    padding: 4rem 2rem;
    background: white;
    border-radius: 12px;
    border: 2px dashed #e2e8f0;
    color: #94a3b8;
  }

  .empty-state :global(.empty-icon) { margin-bottom: 1rem; }

  .empty-state h3 {
    font-size: 1.125rem;
    color: #64748b;
    margin-bottom: 0.4rem;
  }

  .empty-state p { font-size: 0.9rem; }

  /* ── Responsive ──────────────────────────────────────────── */
  @media (max-width: 900px) {
    .filter-bar { flex-direction: column; align-items: flex-start; }
    .right-filters { width: 100%; }
    .search-input { width: 100%; flex: 1; }
  }

  @media (max-width: 600px) {
    .content { padding: 1rem; }
    .topbar { flex-direction: column; }
    .leaflet-map { height: 400px; }
    .list-grid { grid-template-columns: 1fr; }
    .right-filters { flex-direction: column; width: 100%; }
    .search-input, .district-select { width: 100%; }
  }
</style>
