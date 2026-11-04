<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { browser } from '$app/environment';
  import Navbar from '$lib/components/Navbar.svelte';
  import { MapPin, Filter, Search, Layers, Eye, Edit, History } from 'lucide-svelte';

  const API = 'http://localhost:5000';
  let map: any = null;
  let parcels: any[] = [];
  let isLoading = true;
  let filterStatus = 'all';
  let searchQuery = '';
  let selectedParcel = null;
  let showDetailModal = false;
  let currentUser = null;

  function authHeaders() {
    return { 'Authorization': `Bearer ${localStorage.getItem('token')}` };
  }

  async function fetchParcels() {
    isLoading = true;
    try {
      const res = await fetch(`${API}/api/parcels`, { headers: authHeaders() });
      if (res.ok) {
        parcels = await res.json();
      }
    } catch (err) {
      console.error('Error fetching parcels:', err);
    } finally {
      isLoading = false;
    }
  }

  async function fetchCurrentUser() {
    try {
      const res = await fetch(`${API}/api/user/me`, { headers: authHeaders() });
      if (res.ok) {
        currentUser = await res.json();
      }
    } catch (err) {
      console.error('Error fetching user:', err);
    }
  }

  function initializeMap() {
    if (typeof window === 'undefined') return;

    import('leaflet').then((L) => {
      const malawiBounds = [
        [-17.1667, 32.6667],
        [-9.3667, 35.9167]
      ];

      map = L.map('map-container', {
        center: [-13.2543, 34.3015],
        zoom: 7,
        maxBounds: malawiBounds,
        maxBoundsViscosity: 1.0
      });

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
      }).addTo(map);

      map.fitBounds(malawiBounds);
      addParcelMarkers(L);
    });
  }

  function addParcelMarkers(L: any) {
    if (!map) return;

    map.eachLayer((layer: any) => {
      if (layer instanceof L.Marker) {
        map.removeLayer(layer);
      }
    });

    const filteredParcels = getFilteredParcels();

    filteredParcels.forEach((parcel) => {
      if (parcel.points && parcel.points.length > 0) {
        const centerPoint = getCenterPoint(parcel.points);
        if (centerPoint) {
          const markerColor = getStatusColor(parcel.status);
          
          const customIcon = L.divIcon({
            className: 'custom-marker',
            html: `<div style="background: ${markerColor}; width: 24px; height: 24px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);"></div>`,
            iconSize: [24, 24],
            iconAnchor: [12, 12]
          });

          const marker = L.marker([centerPoint.lat, centerPoint.lng], { icon: customIcon }).addTo(map);
          
          marker.on('click', () => {
            // Zoom to the parcel location
            map.setView([centerPoint.lat, centerPoint.lng], 13, {
              animate: true,
              duration: 0.5
            });
            
            // Show detail modal
            selectedParcel = parcel;
            showDetailModal = true;
          });
        }
      }
    });
  }

  function getCenterPoint(points: any[]): { lat: number, lng: number } | null {
    if (!points || points.length === 0) return null;
    
    let lat = 0, lng = 0;
    points.forEach(point => {
      lat += point.lat;
      lng += point.lng;
    });
    
    return {
      lat: lat / points.length,
      lng: lng / points.length
    };
  }

  function getStatusColor(status: string): string {
    switch (status) {
      case 'verified': return '#10b981';
      case 'pending': return '#f59e0b';
      case 'disputed': return '#ef4444';
      case 'approve': return '#10b981';
      case 'reject': return '#ef4444';
      default: return '#6b7280';
    }
  }

  function getFilteredParcels() {
    return parcels.filter(parcel => {
      const matchesStatus = filterStatus === 'all' || parcel.status === filterStatus;
      const matchesSearch = searchQuery === '' || 
        parcel.id?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        parcel.plot_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        parcel.location?.toLowerCase().includes(searchQuery.toLowerCase());
      return matchesStatus && matchesSearch;
    });
  }

  function isOwner(parcel: any): boolean {
    return currentUser && parcel.user_id === currentUser.id;
  }

  function viewPlotDetails(parcel: any) {
    selectedParcel = parcel;
    showDetailModal = true;
  }

  function editPlot(parcel: any) {
    goto(`/my-plots/${parcel.id}/edit`);
  }

  function viewHistory(parcel: any) {
    goto(`/my-plots/${parcel.id}/history`);
  }

  function getUnitLabel(unit: string): string {
    switch (unit) {
      case 'meters': return 'm';
      case 'sqmeters': return 'm²';
      case 'acres': return 'acres';
      case 'hectares': return 'ha';
      default: return '';
    }
  }

  onMount(async () => {
    if (!browser) return;

    if (!localStorage.getItem('token')) {
      goto('/login');
      return;
    }

    await fetchCurrentUser();
    await fetchParcels();
    initializeMap();
  });

  $: if (map && parcels.length > 0) {
    import('leaflet').then((L) => {
      addParcelMarkers(L);
    });
  }
</script>

<svelte:head>
  <title>Public Map - LandLock</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
</svelte:head>

<div class="map-page">
  <Navbar userType="citizen" activeLink="/public-map" userName={currentUser?.full_name || 'User'} />

  <div class="map-container">
    <div class="map-header">
      <div class="header-left">
        <h1><MapPin class="w-6 h-6 inline" /> All Registered Plots</h1>
        <p>View all registered land parcels on an interactive map</p>
      </div>
      <div class="header-right">
        <div class="filter-controls">
          <div class="search-box">
            <Search class="w-5 h-5" />
            <input
              type="text"
              placeholder="Search by plot ID or location..."
              bind:value={searchQuery}
              class="search-input"
            />
          </div>
          <select bind:value={filterStatus} class="filter-select">
            <option value="all">All Status</option>
            <option value="verified">Verified</option>
            <option value="pending">Pending</option>
            <option value="disputed">Disputed</option>
          </select>
        </div>
      </div>
    </div>

    <div class="legend">
      <div class="legend-title">Legend</div>
      <div class="legend-items">
        <div class="legend-item">
          <div class="legend-color" style="background: #10b981;"></div>
          <span>Verified</span>
        </div>
        <div class="legend-item">
          <div class="legend-color" style="background: #f59e0b;"></div>
          <span>Pending</span>
        </div>
        <div class="legend-item">
          <div class="legend-color" style="background: #ef4444;"></div>
          <span>Disputed</span>
        </div>
      </div>
    </div>

    {#if isLoading}
      <div class="loading-state">
        <div class="spinner"></div>
        <p>Loading map...</p>
      </div>
    {:else}
      <div id="map-container" class="map"></div>
      
      <div class="parcels-list">
        <h3>Parcels List</h3>
        {#if getFilteredParcels().length === 0}
          <div class="empty-state">
            <MapPin class="w-16 h-16" />
            <h3>No parcels found</h3>
            <p>{searchQuery || filterStatus !== 'all' ? 'Try adjusting your search or filters' : 'No parcels have been registered yet'}</p>
          </div>
        {:else}
          <div class="parcels-grid">
            {#each getFilteredParcels() as parcel (parcel.id)}
              <div class="parcel-card" on:click={() => viewPlotDetails(parcel)}>
                <div class="parcel-header">
                  <div class="parcel-id">{parcel.id}</div>
                  <div class="parcel-status" style="background: {getStatusColor(parcel.status)}20; color: {getStatusColor(parcel.status)};">
                    {parcel.status || 'Unknown'}
                  </div>
                </div>
                <div class="parcel-details">
                  <div class="detail-item">
                    <MapPin class="w-4 h-4 inline" />
                    <span>{parcel.plot_name || parcel.location || 'Unknown location'}</span>
                  </div>
                  {#if isOwner(parcel)}
                    <div class="owner-badge">Your Plot</div>
                  {/if}
                </div>
              </div>
            {/each}
          </div>
        {/if}
      </div>
    {/if}
  </div>

  <!-- Plot Detail Modal -->
  {#if showDetailModal && selectedParcel}
    <div class="modal-overlay" on:click={() => showDetailModal = false}>
      <div class="modal-content" on:click|stopPropagation>
        <div class="modal-header">
          <h2>Plot Details</h2>
          <button class="close-btn" on:click={() => showDetailModal = false}>&times;</button>
        </div>
        <div class="modal-body">
          <div class="detail-section">
            <h3>Public Information</h3>
            <div class="detail-row">
              <span class="label">Plot ID:</span>
              <span class="value">{selectedParcel.id}</span>
            </div>
            <div class="detail-row">
              <span class="label">Location:</span>
              <span class="value">{selectedParcel.plot_name || selectedParcel.location || 'N/A'}</span>
            </div>
            <div class="detail-row">
              <span class="label">Status:</span>
              <span class="value" style="color: {getStatusColor(selectedParcel.status)}; font-weight: 600;">
                {selectedParcel.status || 'Unknown'}
              </span>
            </div>
            <div class="detail-row">
              <span class="label">Registered:</span>
              <span class="value">{selectedParcel.created_at?.split('T')[0] || 'N/A'}</span>
            </div>
            {#if selectedParcel.estimated_size}
              <div class="detail-row">
                <span class="label">Size:</span>
                <span class="value">{selectedParcel.estimated_size} {getUnitLabel(selectedParcel.size_unit)}</span>
              </div>
            {/if}
          </div>

          {#if isOwner(selectedParcel)}
            <div class="owner-actions">
              <h3>Owner Actions</h3>
              <div class="action-buttons">
                <button class="btn btn-primary" on:click={() => editPlot(selectedParcel)}>
                  <Edit class="w-4 h-4 inline" />
                  Edit Plot
                </button>
                <button class="btn btn-secondary" on:click={() => viewHistory(selectedParcel)}>
                  <History class="w-4 h-4 inline" />
                  View History
                </button>
              </div>
              <p class="edit-warning">
                <strong>Note:</strong> Editing your plot will require re-approval from officials.
              </p>
            </div>
          {/if}
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  :global(*) {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }

  :global(body) {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', sans-serif;
    background: #f8fafc;
    color: #1e293b;
    line-height: 1.5;
  }

  .map-page {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  .map-container {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    max-width: 1400px;
    margin: 0 auto;
    width: 100%;
  }

  .map-header {
    padding: 2rem;
    width: 100%;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 1rem;
    flex-shrink: 0;
  }

  .header-left h1 {
    font-size: 2rem;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .header-left p {
    color: #64748b;
    font-size: 1rem;
  }

  .header-right {
    display: flex;
    gap: 1rem;
  }

  .filter-controls {
    display: flex;
    gap: 0.75rem;
  }

  .search-box {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 0.5rem 1rem;
    width: 300px;
  }

  .search-box svg {
    color: #64748b;
  }

  .search-input {
    border: none;
    outline: none;
    flex: 1;
    font-size: 0.9375rem;
    font-family: inherit;
  }

  .filter-select {
    padding: 0.5rem 1rem;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    font-size: 0.9375rem;
    font-family: inherit;
    background: white;
    cursor: pointer;
  }

  .legend {
    padding: 0 2rem 1rem 2rem;
    width: 100%;
    display: flex;
    align-items: center;
    gap: 1rem;
    flex-shrink: 0;
  }

  .legend-title {
    font-weight: 600;
    color: #374151;
    font-size: 0.875rem;
  }

  .legend-items {
    display: flex;
    gap: 1.5rem;
  }

  .legend-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.875rem;
    color: #64748b;
  }

  .legend-color {
    width: 16px;
    height: 16px;
    border-radius: 50%;
    border: 2px solid white;
    box-shadow: 0 1px 3px rgba(0,0,0,0.2);
  }

  .map {
    flex: 1;
    min-height: 500px;
    border-radius: 12px;
    margin: 0 2rem 2rem 2rem;
    width: calc(100% - 4rem);
    overflow: hidden;
  }

  :global(.leaflet-container) {
    border-radius: 12px;
    border: 1px solid #e2e8f0;
    height: 100%;
    width: 100%;
  }

  .parcels-list {
    padding: 0 2rem 2rem 2rem;
  }

  .parcels-list h3 {
    font-size: 1.25rem;
    font-weight: 600;
    color: #0f172a;
    margin-bottom: 1rem;
  }

  .parcels-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 1rem;
  }

  .parcel-card {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 1rem;
    cursor: pointer;
    transition: all 0.2s;
  }

  .parcel-card:hover {
    border-color: #cbd5e1;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
    transform: translateY(-2px);
  }

  .parcel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.75rem;
  }

  .parcel-id {
    font-weight: 600;
    color: #0f172a;
    font-size: 0.9375rem;
  }

  .parcel-status {
    padding: 0.25rem 0.75rem;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
  }

  .parcel-details {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .detail-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.875rem;
    color: #64748b;
  }

  .owner-badge {
    display: inline-block;
    background: #007A3D;
    color: white;
    padding: 0.25rem 0.75rem;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    align-self: flex-start;
  }

  .loading-state {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 4rem 2rem;
  }

  .spinner {
    width: 48px;
    height: 48px;
    border: 4px solid #e2e8f0;
    border-top-color: #007A3D;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-bottom: 1rem;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .loading-state p {
    color: #64748b;
  }

  .empty-state {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 4rem 2rem;
    background: white;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
  }

  .empty-state svg {
    color: #cbd5e1;
    margin-bottom: 1rem;
  }

  .empty-state h3 {
    font-size: 1.25rem;
    font-weight: 600;
    color: #0f172a;
    margin-bottom: 0.5rem;
  }

  .empty-state p {
    color: #64748b;
  }

  /* Modal Styles */
  .modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    padding: 2rem;
  }

  .modal-content {
    background: white;
    border-radius: 12px;
    max-width: 600px;
    width: 100%;
    max-height: 90vh;
    overflow-y: auto;
  }

  .modal-header {
    padding: 1.5rem;
    border-bottom: 1px solid #e2e8f0;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .modal-header h2 {
    font-size: 1.25rem;
    font-weight: 700;
    color: #0f172a;
  }

  .close-btn {
    background: none;
    border: none;
    font-size: 1.5rem;
    color: #64748b;
    cursor: pointer;
    padding: 0.5rem;
    line-height: 1;
  }

  .close-btn:hover {
    color: #0f172a;
  }

  .modal-body {
    padding: 1.5rem;
  }

  .detail-section {
    margin-bottom: 1.5rem;
  }

  .detail-section h3 {
    font-size: 1rem;
    font-weight: 600;
    color: #0f172a;
    margin-bottom: 1rem;
  }

  .detail-row {
    display: flex;
    justify-content: space-between;
    padding: 0.75rem 0;
    border-bottom: 1px solid #f1f5f9;
  }

  .detail-row:last-child {
    border-bottom: none;
  }

  .detail-row .label {
    color: #64748b;
    font-weight: 500;
  }

  .detail-row .value {
    color: #0f172a;
    font-weight: 600;
  }

  .owner-actions {
    background: #f8fafc;
    border-radius: 8px;
    padding: 1.5rem;
    border: 1px solid #e2e8f0;
  }

  .owner-actions h3 {
    font-size: 1rem;
    font-weight: 600;
    color: #0f172a;
    margin-bottom: 1rem;
  }

  .action-buttons {
    display: flex;
    gap: 0.75rem;
    margin-bottom: 1rem;
  }

  .btn {
    padding: 0.625rem 1.25rem;
    border-radius: 8px;
    border: none;
    font-weight: 600;
    font-size: 0.9375rem;
    cursor: pointer;
    transition: all 0.2s;
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
  }

  .btn-primary {
    background: #007A3D;
    color: white;
  }

  .btn-primary:hover {
    background: #005C2E;
  }

  .btn-secondary {
    background: white;
    color: #007A3D;
    border: 1px solid #e2e8f0;
  }

  .btn-secondary:hover {
    background: #f8fafc;
  }

  .edit-warning {
    font-size: 0.875rem;
    color: #f59e0b;
    margin: 0;
  }

  @media (max-width: 768px) {
    .map-header {
      padding: 1rem;
      flex-direction: column;
      align-items: flex-start;
    }

    .filter-controls {
      flex-direction: column;
      width: 100%;
    }

    .search-box {
      width: 100%;
    }

    .legend {
      padding: 0 1rem 1rem 1rem;
      flex-direction: column;
      align-items: flex-start;
    }

    .map {
      margin: 0 1rem 1rem 1rem;
      width: calc(100% - 2rem);
      min-height: 400px;
    }

    .parcels-list {
      padding: 0 1rem 1rem 1rem;
    }

    .parcels-grid {
      grid-template-columns: 1fr;
    }

    .modal-overlay {
      padding: 1rem;
    }

    .action-buttons {
      flex-direction: column;
    }
  }
</style>
