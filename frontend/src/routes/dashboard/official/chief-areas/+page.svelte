<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { browser } from '$app/environment';
  import { MapPin, User, Layers } from 'lucide-svelte';
  import Navbar from '$lib/components/Navbar.svelte';
  import { initMap, addPolygon } from '$lib/map.js';

  let currentUser = null;
  let chiefAreas = [];
  let chiefs = [];
  let map = null;
  let mapPolygons = [];
  let selectedArea = null;
  let districtCoordinates = {};

  async function fetchCurrentUser() {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:5000/api/user/me', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        currentUser = await response.json();
        if (!currentUser.is_superuser && !currentUser.is_staff) {
          goto('/dashboard');
        }
      } else {
        goto('/login');
      }
    } catch (error) {
      console.error('Failed to fetch user:', error);
      goto('/login');
    }
  }

  async function fetchChiefAreas() {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:5000/api/admin/chief-areas', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        chiefAreas = await response.json();
      }
    } catch (error) {
      console.error('Failed to fetch chief areas:', error);
    }
  }

  async function fetchChiefs() {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:5000/api/admin/chiefs', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        chiefs = await response.json();
      }
    } catch (error) {
      console.error('Failed to fetch chiefs:', error);
    }
  }

  async function fetchDistrictBoundaries() {
    try {
      const response = await fetch('http://localhost:5000/api/admin/district-boundaries');
      if (response.ok) {
        districtCoordinates = await response.json();
      }
    } catch (error) {
      console.error('Failed to fetch district boundaries:', error);
    }
  }

  function getChiefColor(chiefId: string): string {
    const colors = ['#007A3D', '#CE1126', '#2635A3', '#FFD100', '#FF6B35', '#4A90E2', '#50E3C2', '#B8E986', '#F5A623', '#BD10E0'];
    const index = chiefs.findIndex(c => c.id === chiefId);
    return index >= 0 ? colors[index % colors.length] : '#94a3b8';
  }

  async function initializeMap() {
    if (!browser) return;
    try {
      const mapElement = document.getElementById('chief-areas-map');
      if (!mapElement) return;

      map = await initMap(mapElement, null);
      map.setView([-13.2543, 34.3015], 7);

      Object.entries(districtCoordinates).forEach(([districtId, coords]) => {
        const points = coords.map(([lng, lat]) => ({ lat, lng }));
        const assignedArea = chiefAreas.find(area => area.area_id === districtId && area.area_type === 'district');
        const color = assignedArea ? getChiefColor(assignedArea.chief_id) : '#94a3b8';

        const polygon = addPolygon(map, points, districtId, districtId.charAt(0).toUpperCase() + districtId.slice(1));
        if (polygon) {
          polygon.setStyle({
            color,
            fillColor: color,
            fillOpacity: assignedArea ? 0.4 : 0.1,
            weight: 2
          });
          polygon.on('click', () => { selectedArea = districtId; });
          polygon.on('mouseover', () => polygon.setStyle({ weight: 4, fillOpacity: 0.6 }));
          polygon.on('mouseout', () => polygon.setStyle({ weight: 2, fillOpacity: assignedArea ? 0.4 : 0.1 }));
          mapPolygons.push(polygon);
        }
      });
    } catch (error) {
      console.error('Failed to initialize map:', error);
    }
  }

  onMount(() => {
    if (!browser) return;
    if (!localStorage.getItem('token')) {
      goto('/login');
      return;
    }
    fetchCurrentUser();
    fetchChiefAreas();
    fetchChiefs();
    fetchDistrictBoundaries();
    setTimeout(() => initializeMap(), 1000);
  });
</script>

<svelte:head>
  <title>Chief Areas - LandLock Official</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
</svelte:head>

<div class="page-wrapper">
  <Navbar userType="official" activeLink="/dashboard/official/chief-areas" userName={currentUser?.full_name || 'Official'} />

  <main class="main-content">
    <div class="page-header">
      <div>
        <h1><Layers class="header-icon" /> Chief Area Overview</h1>
        <p>View districts and their assigned chiefs across Malawi</p>
      </div>
    </div>

    <!-- Map -->
    <div class="map-section">
      <div class="map-header">
        <h3>Interactive Map</h3>
        <p>Click a district to highlight it. Coloured areas have an assigned chief.</p>
        {#if selectedArea}
          <div class="selected-badge">
            Selected: {selectedArea.charAt(0).toUpperCase() + selectedArea.slice(1)}
          </div>
        {/if}
      </div>
      <div id="chief-areas-map" class="map-container"></div>
    </div>

    <!-- Assignments list -->
    <div class="section-header">
      <h3>Current Assignments <span class="count-badge">{chiefAreas.length}</span></h3>
    </div>

    <div class="areas-grid">
      {#if chiefAreas.length === 0}
        <div class="empty-state">
          <MapPin class="empty-icon" />
          <h3>No Chief Areas Assigned</h3>
          <p>No chief–area assignments have been configured yet.</p>
        </div>
      {:else}
        {#each chiefAreas as area}
          <div class="area-card">
            <div class="area-header">
              <div class="area-info">
                <h4>{area.area_name}</h4>
                <div class="chief-info">
                  <User class="icon-xs" />
                  <span>{area.chief_name || 'Unknown Chief'}</span>
                </div>
                {#if area.chief_phone}
                  <div class="chief-phone">{area.chief_phone}</div>
                {/if}
              </div>
              <span class="type-badge">{area.area_type || 'Unknown'}</span>
            </div>
            <div class="area-details">
              <div class="detail-item">
                <span class="detail-label">Area</span>
                <span class="detail-value">{area.resolved_area_name || area.area_name || '—'}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Added</span>
                <span class="detail-value">{new Date(area.created_at).toLocaleDateString()}</span>
              </div>
            </div>
          </div>
        {/each}
      {/if}
    </div>
  </main>
</div>

<style>
  .page-wrapper {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    background: #f8fafc;
  }

  .main-content {
    max-width: 1400px;
    margin: 0 auto;
    padding: 2rem;
    width: 100%;
    flex: 1;
  }

  /* Page Header */
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
  }

  .page-header h1 {
    font-size: 2rem;
    font-weight: 700;
    color: #1e293b;
    margin-bottom: 0.4rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .header-icon {
    color: #007A3D;
  }

  .page-header p {
    color: #64748b;
    font-size: 1rem;
  }

  /* Map */
  .map-section {
    background: white;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
    padding: 1.5rem;
    margin-bottom: 2rem;
  }

  .map-header {
    margin-bottom: 1rem;
  }

  .map-header h3 {
    font-size: 1.125rem;
    font-weight: 600;
    color: #1e293b;
    margin-bottom: 0.25rem;
  }

  .map-header p {
    font-size: 0.875rem;
    color: #64748b;
    margin-bottom: 0.5rem;
  }

  .selected-badge {
    display: inline-block;
    background: #007A3D;
    color: white;
    padding: 0.375rem 0.875rem;
    border-radius: 6px;
    font-size: 0.875rem;
    font-weight: 500;
  }

  .map-container {
    height: 480px;
    border-radius: 8px;
    border: 1px solid #e2e8f0;
    overflow: hidden;
  }

  :global(.leaflet-container) {
    height: 100%;
    width: 100%;
  }

  /* Section header */
  .section-header {
    margin-bottom: 1.25rem;
  }

  .section-header h3 {
    font-size: 1.125rem;
    font-weight: 600;
    color: #1e293b;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .count-badge {
    background: #e2e8f0;
    color: #475569;
    font-size: 0.75rem;
    font-weight: 600;
    padding: 0.2rem 0.6rem;
    border-radius: 999px;
  }

  /* Grid */
  .areas-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 1.25rem;
  }

  /* Empty */
  .empty-state {
    grid-column: 1 / -1;
    text-align: center;
    padding: 3rem 2rem;
    background: white;
    border-radius: 12px;
    border: 2px dashed #e2e8f0;
    color: #94a3b8;
  }

  .empty-icon {
    width: 48px;
    height: 48px;
    margin-bottom: 1rem;
    color: #cbd5e1;
  }

  .empty-state h3 {
    font-size: 1.125rem;
    color: #64748b;
    margin-bottom: 0.5rem;
  }

  .empty-state p {
    font-size: 0.9rem;
  }

  /* Area card */
  .area-card {
    background: white;
    border-radius: 12px;
    padding: 1.25rem;
    border: 1px solid #e2e8f0;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    transition: box-shadow 0.2s, transform 0.2s;
  }

  .area-card:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    transform: translateY(-2px);
  }

  .area-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 1rem;
  }

  .area-info h4 {
    font-size: 1.0625rem;
    font-weight: 600;
    color: #1e293b;
    margin-bottom: 0.375rem;
  }

  .chief-info {
    display: flex;
    align-items: center;
    gap: 0.375rem;
    color: #475569;
    font-size: 0.875rem;
    margin-bottom: 0.2rem;
  }

  .icon-xs {
    width: 14px;
    height: 14px;
    flex-shrink: 0;
  }

  .chief-phone {
    font-size: 0.8125rem;
    color: #94a3b8;
  }

  .type-badge {
    background: #f0fdf4;
    color: #007A3D;
    font-size: 0.75rem;
    font-weight: 600;
    padding: 0.25rem 0.625rem;
    border-radius: 999px;
    white-space: nowrap;
    text-transform: capitalize;
  }

  .area-details {
    display: flex;
    gap: 2rem;
    padding-top: 0.875rem;
    border-top: 1px solid #f1f5f9;
  }

  .detail-item {
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
  }

  .detail-label {
    font-size: 0.6875rem;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    font-weight: 600;
  }

  .detail-value {
    font-size: 0.875rem;
    color: #1e293b;
    font-weight: 500;
  }

  @media (max-width: 768px) {
    .main-content {
      padding: 1rem;
    }

    .areas-grid {
      grid-template-columns: 1fr;
    }

    .map-container {
      height: 320px;
    }
  }
</style>
