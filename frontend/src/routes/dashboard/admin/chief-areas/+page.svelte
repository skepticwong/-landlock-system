<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { browser } from '$app/environment';
  import { MapPin, Plus, Edit, Trash2, Save, X, User, Layers } from 'lucide-svelte';
  import Navbar from '$lib/components/Navbar.svelte';
  import { initMap, addPolygon } from '$lib/map.js';

  let currentUser = null;
  let chiefAreas = [];
  let chiefs = [];
  let showCreateModal = false;
  let showEditModal = false;
  let editingArea = null;
  let isSubmitting = false;
  let map = null;
  let mapPolygons = [];
  let selectedArea = null;

  // Geographic areas data
  let districts = [];
  let traditionalAuthorities = [];
  let villages = [];

  // Form data
  let formData = {
    chief_id: '',
    area_type: 'district',
    area_id: ''
  };

  // District coordinates for map (fetched from backend)
  let districtCoordinates = {};

  async function fetchCurrentUser() {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:5000/api/user/me', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        currentUser = await response.json();
        // Check if user is admin or official
        if (!currentUser.is_superuser && !currentUser.is_staff) {
          goto('/dashboard');
          return;
        }
      }
    } catch (error) {
      console.error('Failed to fetch user:', error);
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

  async function fetchGeographicAreas() {
    try {
      const [districtsRes] = await Promise.all([
        fetch('http://localhost:5000/api/districts')
      ]);

      if (districtsRes.ok) {
        districts = await districtsRes.json();
      }
    } catch (error) {
      console.error('Failed to fetch geographic areas:', error);
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

  function openCreateModal() {
    formData = {
      chief_id: '',
      area_type: 'district',
      area_id: selectedArea || ''
    };
    showCreateModal = true;
  }

  function handleMapClick(areaId: string) {
    selectedArea = areaId;
    formData.area_id = areaId;
    formData.area_type = 'district';
  }

  function getChiefColor(chiefId: string): string {
    // Generate consistent colors based on chief ID
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

      // Set view to Malawi
      map.setView([-13.2543, 34.3015], 7);

      // Add district polygons
      Object.entries(districtCoordinates).forEach(([districtId, coords]) => {
        // Convert [lng, lat] format to {lat, lng} format
        const points = coords.map(([lng, lat]) => ({ lat, lng }));
        
        // Check if this district has a chief assigned
        const assignedArea = chiefAreas.find(area => area.area_id === districtId && area.area_type === 'district');
        const color = assignedArea ? getChiefColor(assignedArea.chief_id) : '#94a3b8';
        
        const polygon = addPolygon(map, points, districtId, districtId.charAt(0).toUpperCase() + districtId.slice(1));
        
        if (polygon) {
          polygon.setStyle({
            color: color,
            fillColor: color,
            fillOpacity: assignedArea ? 0.4 : 0.1,
            weight: 2
          });

          polygon.on('click', () => handleMapClick(districtId));
          polygon.on('mouseover', () => {
            polygon.setStyle({ weight: 4, fillOpacity: 0.6 });
          });
          polygon.on('mouseout', () => {
            polygon.setStyle({ weight: 2, fillOpacity: assignedArea ? 0.4 : 0.1 });
          });

          mapPolygons.push(polygon);
        }
      });
    } catch (error) {
      console.error('Failed to initialize map:', error);
    }
  }

  function closeCreateModal() {
    showCreateModal = false;
  }

  function openEditModal(area) {
    editingArea = area;
    formData = {
      chief_id: area.chief_id,
      area_type: area.area_type || 'district',
      area_id: area.area_id || ''
    };
    showEditModal = true;
  }

  function closeEditModal() {
    showEditModal = false;
    editingArea = null;
  }

  async function createChiefArea() {
    if (!formData.chief_id || !formData.area_type || !formData.area_id) {
      alert('Please fill in all fields');
      return;
    }

    isSubmitting = true;
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:5000/api/admin/chief-areas', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          chief_id: formData.chief_id,
          area_type: formData.area_type,
          area_id: formData.area_id
        })
      });

      if (response.ok) {
        alert('Chief area created successfully');
        closeCreateModal();
        fetchChiefAreas();
        // Refresh map to show new assignment
        setTimeout(() => initializeMap(), 500);
      } else {
        const error = await response.json();
        alert(error.error || 'Failed to create chief area');
      }
    } catch (error) {
      console.error('Failed to create chief area:', error);
      alert('Failed to create chief area');
    } finally {
      isSubmitting = false;
    }
  }

  async function updateChiefArea() {
    if (!formData.chief_id || !formData.area_type || !formData.area_id) {
      alert('Please fill in all fields');
      return;
    }

    isSubmitting = true;
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:5000/api/admin/chief-areas/${editingArea.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          chief_id: formData.chief_id,
          area_type: formData.area_type,
          area_id: formData.area_id
        })
      });

      if (response.ok) {
        alert('Chief area updated successfully');
        closeEditModal();
        fetchChiefAreas();
        // Refresh map to show updated assignment
        setTimeout(() => initializeMap(), 500);
      } else {
        const error = await response.json();
        alert(error.error || 'Failed to update chief area');
      }
    } catch (error) {
      console.error('Failed to update chief area:', error);
      alert('Failed to update chief area');
    } finally {
      isSubmitting = false;
    }
  }

  async function deleteChiefArea(areaId) {
    if (!confirm('Are you sure you want to delete this chief area?')) {
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:5000/api/admin/chief-areas/${areaId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        alert('Chief area deleted successfully');
        fetchChiefAreas();
      } else {
        alert('Failed to delete chief area');
      }
    } catch (error) {
      console.error('Failed to delete chief area:', error);
      alert('Failed to delete chief area');
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
    fetchGeographicAreas();
    fetchDistrictBoundaries();
    
    // Initialize map after data is loaded
    setTimeout(() => initializeMap(), 1000);
  });

  function backToDashboard() {
    goto('/dashboard');
  }
</script>

<svelte:head>
  <title>Chief Area Management - LandLock</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
</svelte:head>

<div class="admin-chief-areas">
  <Navbar userType={currentUser?.is_superuser ? 'admin' : 'official'} activeLink="/dashboard/admin/chief-areas" userName={currentUser?.full_name || 'Admin'} />

  <main class="main-content">
    <div class="page-header">
      <div>
        <h1><Layers class="w-6 h-6 inline" /> Chief Area Management</h1>
        <p>Assign chiefs to geographic areas using the interactive map</p>
      </div>
      <button class="btn btn-primary" on:click={openCreateModal}>
        <Plus class="w-5 h-5 inline" />
        Assign New Area
      </button>
    </div>

    <div class="map-section">
      <div class="map-header">
        <h3>Interactive Map</h3>
        <p>Click on a district to select it for chief assignment</p>
        {#if selectedArea}
          <div class="selected-area">
            <strong>Selected:</strong> {selectedArea.charAt(0).toUpperCase() + selectedArea.slice(1)}
          </div>
        {/if}
      </div>
      <div id="chief-areas-map" class="map-container"></div>
    </div>

    <div class="areas-header">
      <h3>Current Assignments</h3>
    </div>

    <div class="areas-grid">
      {#if chiefAreas.length === 0}
        <div class="empty-state">
          <MapPin class="w-16 h-16" />
          <h3>No Chief Areas Assigned</h3>
          <p>Click "Assign New Area" to create the first chief area assignment.</p>
        </div>
      {:else}
        {#each chiefAreas as area}
          <div class="area-card">
            <div class="area-header">
              <div class="area-info">
                <h3>{area.area_name}</h3>
                <div class="chief-info">
                  <User class="w-4 h-4 inline" />
                  <span>{area.chief_name || 'Unknown Chief'}</span>
                </div>
                {#if area.chief_phone}
                  <div class="chief-phone">{area.chief_phone}</div>
                {/if}
              </div>
              <div class="area-actions">
                <button class="btn btn-icon btn-secondary" on:click={() => openEditModal(area)} title="Edit">
                  <Edit class="w-4 h-4" />
                </button>
                <button class="btn btn-icon btn-danger" on:click={() => deleteChiefArea(area.id)} title="Delete">
                  <Trash2 class="w-4 h-4" />
                </button>
              </div>
            </div>
            <div class="area-details">
              <div class="detail-item">
                <span class="detail-label">Area Type:</span>
                <span class="detail-value">{area.area_type || 'Unknown'}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Area:</span>
                <span class="detail-value">{area.resolved_area_name || area.area_name || 'Unknown'}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Created:</span>
                <span class="detail-value">{new Date(area.created_at).toLocaleDateString()}</span>
              </div>
            </div>
          </div>
        {/each}
      {/if}
    </div>
  </main>

  <!-- Create Modal -->
  {#if showCreateModal}
    <div class="modal-overlay">
      <div class="modal-content">
        <div class="modal-header">
          <h2>Assign Chief to Area</h2>
          <button class="btn btn-icon" on:click={closeCreateModal}>
            <X class="w-5 h-5" />
          </button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">Select Chief</label>
            <select class="form-select" bind:value={formData.chief_id}>
              <option value="">Select a chief</option>
              {#each chiefs as chief}
                <option value={chief.id}>{chief.full_name} ({chief.phone})</option>
              {/each}
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Area Type</label>
            <select class="form-select" bind:value={formData.area_type}>
              <option value="district">District</option>
              <option value="traditional_authority">Traditional Authority</option>
              <option value="village">Village</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Select Area</label>
            <select class="form-select" bind:value={formData.area_id}>
              <option value="">Select an area</option>
              {#if formData.area_type === 'district'}
                {#each districts as district}
                  <option value={district.toLowerCase()}>{district}</option>
                {/each}
              {:else if formData.area_type === 'traditional_authority'}
                {#each ['Chief Mwase', 'Chief Bvumbwe', 'Chief Kuntaja', 'Chief Nkhoma', 'Chief Chapola', 'Chief Mbelwa', 'Chief Chikuse'] as ta}
                  <option value={ta.toLowerCase().replace('chief ', '')}>{ta}</option>
                {/each}
              {:else if formData.area_type === 'village'}
                {#each ['Chilomoni', 'Area 25', 'Kawale', 'Mchenga', 'Njewa', 'Area 18', 'Area 43', 'Biwi', 'Lilongwe City Centre'] as village}
                  <option value={village.toLowerCase()}>{village}</option>
                {/each}
              {/if}
            </select>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" on:click={closeCreateModal}>Cancel</button>
          <button class="btn btn-primary" on:click={createChiefArea} disabled={isSubmitting}>
            {#if isSubmitting}
              Saving...
            {:else}
              <Save class="w-4 h-4 inline" />
              Save Assignment
            {/if}
          </button>
        </div>
      </div>
    </div>
  {/if}

  <!-- Edit Modal -->
  {#if showEditModal}
    <div class="modal-overlay">
      <div class="modal-content">
        <div class="modal-header">
          <h2>Edit Chief Area Assignment</h2>
          <button class="btn btn-icon" on:click={closeEditModal}>
            <X class="w-5 h-5" />
          </button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">Select Chief</label>
            <select class="form-select" bind:value={formData.chief_id}>
              <option value="">Select a chief</option>
              {#each chiefs as chief}
                <option value={chief.id}>{chief.full_name} ({chief.phone})</option>
              {/each}
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Area Type</label>
            <select class="form-select" bind:value={formData.area_type}>
              <option value="district">District</option>
              <option value="traditional_authority">Traditional Authority</option>
              <option value="village">Village</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Select Area</label>
            <select class="form-select" bind:value={formData.area_id}>
              <option value="">Select an area</option>
              {#if formData.area_type === 'district'}
                {#each districts as district}
                  <option value={district.toLowerCase()}>{district}</option>
                {/each}
              {:else if formData.area_type === 'traditional_authority'}
                {#each ['Chief Mwase', 'Chief Bvumbwe', 'Chief Kuntaja', 'Chief Nkhoma', 'Chief Chapola', 'Chief Mbelwa', 'Chief Chikuse'] as ta}
                  <option value={ta.toLowerCase().replace('chief ', '')}>{ta}</option>
                {/each}
              {:else if formData.area_type === 'village'}
                {#each ['Chilomoni', 'Area 25', 'Kawale', 'Mchenga', 'Njewa', 'Area 18', 'Area 43', 'Biwi', 'Lilongwe City Centre'] as village}
                  <option value={village.toLowerCase()}>{village}</option>
                {/each}
              {/if}
            </select>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" on:click={closeEditModal}>Cancel</button>
          <button class="btn btn-primary" on:click={updateChiefArea} disabled={isSubmitting}>
            {#if isSubmitting}
              Saving...
            {:else}
              <Save class="w-4 h-4 inline" />
              Update Assignment
            {/if}
          </button>
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .admin-chief-areas {
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

  .map-section {
    margin-bottom: 2rem;
  }

  .map-header {
    margin-bottom: 1rem;
  }

  .map-header h3 {
    font-size: 1.25rem;
    font-weight: 600;
    color: #1e293b;
    margin-bottom: 0.5rem;
  }

  .map-header p {
    color: #64748b;
    font-size: 0.875rem;
    margin-bottom: 0.5rem;
  }

  .selected-area {
    display: inline-block;
    background: #007A3D;
    color: white;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    font-size: 0.875rem;
    font-weight: 500;
  }

  .map-container {
    height: 500px;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
    overflow: hidden;
  }

  :global(.leaflet-container) {
    height: 100%;
    width: 100%;
  }

  .areas-header {
    margin-bottom: 1.5rem;
  }

  .areas-header h3 {
    font-size: 1.25rem;
    font-weight: 600;
    color: #1e293b;
  }

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
    margin-bottom: 0.5rem;
  }

  .page-header p {
    color: #64748b;
    font-size: 1rem;
  }

  .areas-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
    gap: 1.5rem;
  }

  .empty-state {
    grid-column: 1 / -1;
    text-align: center;
    padding: 4rem 2rem;
    background: white;
    border-radius: 12px;
    border: 2px dashed #e2e8f0;
  }

  .empty-state svg {
    color: #94a3b8;
    margin-bottom: 1rem;
  }

  .empty-state h3 {
    font-size: 1.25rem;
    color: #64748b;
    margin-bottom: 0.5rem;
  }

  .empty-state p {
    color: #94a3b8;
  }

  .area-card {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    border: 1px solid #e2e8f0;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }

  .area-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 1rem;
  }

  .area-info h3 {
    font-size: 1.25rem;
    font-weight: 600;
    color: #1e293b;
    margin-bottom: 0.5rem;
  }

  .chief-info {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: #64748b;
    font-size: 0.875rem;
    margin-bottom: 0.25rem;
  }

  .chief-phone {
    color: #94a3b8;
    font-size: 0.875rem;
  }

  .area-actions {
    display: flex;
    gap: 0.5rem;
  }

  .area-details {
    display: flex;
    gap: 1.5rem;
    padding-top: 1rem;
    border-top: 1px solid #e2e8f0;
  }

  .detail-item {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .detail-label {
    font-size: 0.75rem;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .detail-value {
    font-size: 0.875rem;
    color: #1e293b;
    font-weight: 500;
  }

  .btn {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    border-radius: 8px;
    font-weight: 500;
    font-size: 0.875rem;
    cursor: pointer;
    border: none;
    transition: all 0.2s;
  }

  .btn-primary {
    background: #3b82f6;
    color: white;
  }

  .btn-primary:hover {
    background: #2563eb;
  }

  .btn-secondary {
    background: #f1f5f9;
    color: #64748b;
  }

  .btn-secondary:hover {
    background: #e2e8f0;
  }

  .btn-icon {
    padding: 0.5rem;
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }

  .btn-danger {
    background: #fef2f2;
    color: #ef4444;
  }

  .btn-danger:hover {
    background: #fee2e2;
  }

  .btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .btn-sm {
    padding: 0.25rem 0.5rem;
    font-size: 0.75rem;
  }

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
    padding: 1rem;
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
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.5rem;
    border-bottom: 1px solid #e2e8f0;
  }

  .modal-header h2 {
    font-size: 1.25rem;
    font-weight: 600;
    color: #1e293b;
  }

  .modal-body {
    padding: 1.5rem;
  }

  .modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 0.75rem;
    padding: 1.5rem;
    border-top: 1px solid #e2e8f0;
  }

  .form-group {
    margin-bottom: 1.5rem;
  }

  .form-label {
    display: block;
    font-weight: 500;
    color: #374151;
    margin-bottom: 0.5rem;
    font-size: 0.875rem;
  }

  .form-input,
  .form-select {
    width: 100%;
    padding: 0.625rem;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    font-size: 0.875rem;
    transition: border-color 0.2s;
  }

  .form-input:focus,
  .form-select:focus {
    outline: none;
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  }

  .form-hint {
    font-size: 0.75rem;
    color: #64748b;
    margin-bottom: 0.5rem;
  }
</style>
