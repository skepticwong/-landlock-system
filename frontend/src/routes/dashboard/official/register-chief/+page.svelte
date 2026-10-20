<script lang="ts">
  import { onMount, afterUpdate } from 'svelte';
  import { goto } from '$app/navigation';
  import { browser } from '$app/environment';
  import { UserPlus, User, MapPin, Shield, ArrowLeft, Save, Trash2, Layers } from 'lucide-svelte';
  import Navbar from '$lib/components/Navbar.svelte';
  import { initMap, addPolygon } from '$lib/map.js';

  const API = 'http://localhost:5000';

  let currentUser = null;
  let chiefs = [];
  let geographicAreas = { districts: [], traditional_authorities: [], villages: [] };
  let chiefAreas = [];
  let districtCoordinates = {};
  
  // Map state
  let map = null;
  let mapPolygons = [];
  let selectedDistrict = null;
  let selectedChiefForAssignment = null;
  
  // Form state
  let showRegisterForm = false;
  let showAssignMode = false;
  
  let newChief = {
    national_id: '',
    full_name: '',
    phone: '',
    temporary_pin: ''
  };
  
  let isLoading = true;
  let isSubmitting = false;
  let message = '';
  let messageType = '';

  function authHeaders() {
    return { 'Authorization': `Bearer ${localStorage.getItem('token')}` };
  }

  async function fetchCurrentUser() {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API}/api/user/me`, {
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

  async function fetchChiefs() {
    try {
      const response = await fetch(`${API}/api/official/chiefs`, { headers: authHeaders() });
      if (response.ok) {
        chiefs = await response.json();
      }
    } catch (error) {
      console.error('Failed to fetch chiefs:', error);
    }
  }

  async function fetchGeographicAreas() {
    try {
      const response = await fetch(`${API}/api/official/geographic-areas`, { headers: authHeaders() });
      if (response.ok) {
        geographicAreas = await response.json();
      }
    } catch (error) {
      console.error('Failed to fetch geographic areas:', error);
    }
  }

  async function fetchChiefAreas() {
    try {
      const response = await fetch(`${API}/api/official/chief-areas`, { headers: authHeaders() });
      if (response.ok) {
        chiefAreas = await response.json();
      }
    } catch (error) {
      console.error('Failed to fetch chief areas:', error);
    }
  }

  async function fetchDistrictBoundaries() {
    try {
      const response = await fetch(`${API}/api/admin/district-boundaries`);
      if (response.ok) {
        districtCoordinates = await response.json();
      }
    } catch (error) {
      console.error('Failed to fetch district boundaries:', error);
    }
  }

  async function registerChief() {
    isSubmitting = true;
    message = '';
    
    try {
      const response = await fetch(`${API}/api/official/register-chief`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          ...authHeaders()
        },
        body: JSON.stringify(newChief)
      });
      
      if (response.ok) {
        const result = await response.json();
        message = 'Chief registered successfully!';
        messageType = 'success';
        
        // Reset form
        newChief = {
          national_id: '',
          full_name: '',
          phone: '',
          temporary_pin: '',
          district: '',
          traditional_authority: '',
          village: ''
        };
        showRegisterForm = false;
        
        // Refresh data
        await fetchChiefs();
      } else {
        const error = await response.json();
        message = error.error || 'Failed to register chief';
        messageType = 'error';
      }
    } catch (error) {
      console.error('Error registering chief:', error);
      message = 'Failed to register chief. Please try again.';
      messageType = 'error';
    } finally {
      isSubmitting = false;
    }
  }

  async function assignArea() {
    if (!selectedDistrict || !selectedChiefForAssignment) {
      message = 'Please select a district and a chief';
      messageType = 'error';
      return;
    }

    isSubmitting = true;
    message = '';
    
    try {
      const response = await fetch(`${API}/api/official/chief-areas`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          ...authHeaders()
        },
        body: JSON.stringify({
          chief_id: selectedChiefForAssignment,
          area_type: 'district',
          area_id: selectedDistrict
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        message = 'District assigned successfully!';
        messageType = 'success';
        
        // Reset selection
        selectedDistrict = null;
        selectedChiefForAssignment = null;
        
        // Refresh data
        await fetchChiefAreas();
        updateMapColors();
      } else {
        const error = await response.json();
        message = error.error || 'Failed to assign district';
        messageType = 'error';
      }
    } catch (error) {
      console.error('Error assigning district:', error);
      message = 'Failed to assign district. Please try again.';
      messageType = 'error';
    } finally {
      isSubmitting = false;
    }
  }

  async function deleteArea(areaId: number) {
    if (!confirm('Are you sure you want to remove this area assignment?')) return;
    
    try {
      const response = await fetch(`${API}/api/official/chief-areas/${areaId}`, {
        method: 'DELETE',
        headers: authHeaders()
      });
      
      if (response.ok) {
        message = 'Area assignment removed successfully!';
        messageType = 'success';
        await fetchChiefAreas();
      } else {
        const error = await response.json();
        message = error.error || 'Failed to remove area';
        messageType = 'error';
      }
    } catch (error) {
      console.error('Error deleting area:', error);
      message = 'Failed to remove area. Please try again.';
      messageType = 'error';
    }
  }

  async function resetChiefPin(chiefId: number, chiefName: string) {
    const newPin = prompt(`Enter new PIN for ${chiefName}:`);
    if (!newPin) return;
    
    if (newPin.length < 4) {
      message = 'PIN must be at least 4 characters';
      messageType = 'error';
      return;
    }
    
    try {
      const response = await fetch(`${API}/api/official/chiefs/${chiefId}/reset-pin`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          ...authHeaders()
        },
        body: JSON.stringify({ new_pin: newPin })
      });
      
      if (response.ok) {
        message = 'PIN reset successfully!';
        messageType = 'success';
      } else {
        const error = await response.json();
        message = error.error || 'Failed to reset PIN';
        messageType = 'error';
      }
    } catch (error) {
      console.error('Error resetting PIN:', error);
      message = 'Failed to reset PIN. Please try again.';
      messageType = 'error';
    }
  }

  function getChiefById(id: string) {
    return chiefs.find(c => c.id === parseInt(id));
  }

  function getChiefColor(chiefId: string): string {
    const colors = ['#007A3D', '#CE1126', '#2635A3', '#FFD100', '#FF6B35', '#4A90E2', '#50E3C2', '#B8E986', '#F5A623', '#BD10E0'];
    const index = chiefs.findIndex(c => c.id === chiefId);
    return index >= 0 ? colors[index % colors.length] : '#94a3b8';
  }

  function getChiefName(chiefId: string): string {
    const chief = chiefs.find(c => c.id === parseInt(chiefId));
    return chief ? chief.full_name : 'Unknown';
  }

  async function initializeMap() {
    if (!browser) return;
    try {
      const mapElement = document.getElementById('chief-assignment-map');
      if (!mapElement) {
        console.log('Map element not found');
        return;
      }

      // Destroy existing map if it exists
      if (map) {
        map.remove();
        map = null;
        mapPolygons = [];
      }

      map = await initMap(mapElement, null);
      map.setView([-13.2543, 34.3015], 7);

      updateMapColors();
    } catch (error) {
      console.error('Failed to initialize map:', error);
    }
  }

  function updateMapColors() {
    if (!map || !districtCoordinates) return;

    // Clear existing polygons
    mapPolygons.forEach(polygon => map.removeLayer(polygon));
    mapPolygons = [];

    Object.entries(districtCoordinates).forEach(([districtId, coords]) => {
      const points = coords.map(([lng, lat]) => ({ lat, lng }));
      const assignedArea = chiefAreas.find(area => area.area_id === districtId && area.area_type === 'district');
      const color = assignedArea ? getChiefColor(assignedArea.chief_id) : '#94a3b8';
      const isSelected = selectedDistrict === districtId;

      const polygon = addPolygon(map, points, districtId, districtId.charAt(0).toUpperCase() + districtId.slice(1));
      if (polygon) {
        polygon.setStyle({
          color: isSelected ? '#007A3D' : color,
          fillColor: isSelected ? '#007A3D' : color,
          fillOpacity: assignedArea ? 0.4 : (isSelected ? 0.3 : 0.1),
          weight: isSelected ? 4 : 2
        });
        polygon.on('click', () => { 
          selectedDistrict = districtId;
          updateMapColors();
        });
        polygon.on('mouseover', () => polygon.setStyle({ weight: 4, fillOpacity: 0.6 }));
        polygon.on('mouseout', () => {
          const assignedArea = chiefAreas.find(area => area.area_id === districtId && area.area_type === 'district');
          const color = assignedArea ? getChiefColor(assignedArea.chief_id) : '#94a3b8';
          const isSelected = selectedDistrict === districtId;
          polygon.setStyle({ 
            weight: isSelected ? 4 : 2, 
            fillOpacity: assignedArea ? 0.4 : (isSelected ? 0.3 : 0.1) 
          });
        });
        mapPolygons.push(polygon);
      }
    });
  }

  onMount(async () => {
    if (!browser) return;
    if (!localStorage.getItem('token')) {
      goto('/login');
      return;
    }
    
    await fetchCurrentUser();
    await Promise.all([fetchChiefs(), fetchGeographicAreas(), fetchChiefAreas(), fetchDistrictBoundaries()]);
    isLoading = false;
  });

  afterUpdate(() => {
    if (showAssignMode && !map && districtCoordinates && Object.keys(districtCoordinates).length > 0) {
      setTimeout(() => initializeMap(), 100);
    }
  });
</script>

<svelte:head>
  <title>Register Chief - LandLock Official</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
</svelte:head>

<div class="page-wrapper">
  <Navbar userType="official" activeLink="/dashboard/official/register-chief" userName={currentUser?.full_name || 'Official'} />

  <main class="main-content">
    <div class="page-header">
      <a href="/dashboard/official" class="back-link">
        <ArrowLeft size={20} />
        Back to Dashboard
      </a>
      <div>
        <h1><UserPlus class="header-icon" /> Chief Management</h1>
        <p>Register chiefs and assign their jurisdictions</p>
      </div>
    </div>

    {#if message}
      <div class="alert {messageType}">
        {message}
      </div>
    {/if}

    {#if isLoading}
      <div class="loading-state">
        <p>Loading chief data...</p>
      </div>
    {:else}
      <!-- Action Buttons -->
      <div class="action-buttons">
        <button class="btn btn-primary" on:click={() => { showRegisterForm = true; showAssignMode = false; }}>
          <UserPlus size={20} />
          Register New Chief
        </button>
        <button class="btn btn-secondary" on:click={() => { showAssignMode = true; showRegisterForm = false; }} disabled={chiefs.length === 0}>
          <Layers size={20} />
          Map Assignment
        </button>
      </div>

      <!-- Register Chief Form -->
      {#if showRegisterForm}
        <div class="card form-card">
          <div class="card-header">
            <h2><UserPlus size={20} /> Register New Chief</h2>
            <button class="btn-close" on:click={() => showRegisterForm = false}>×</button>
          </div>
          <div class="card-body">
            <form on:submit|preventDefault={registerChief}>
              <div class="form-grid">
                <div class="form-group">
                  <label>National ID *</label>
                  <input type="text" bind:value={newChief.national_id} required placeholder="Enter national ID" />
                </div>
                <div class="form-group">
                  <label>Full Name *</label>
                  <input type="text" bind:value={newChief.full_name} required placeholder="Enter full name" />
                </div>
                <div class="form-group">
                  <label>Phone Number *</label>
                  <input type="tel" bind:value={newChief.phone} required placeholder="0XXX XXX XXX" />
                </div>
                <div class="form-group">
                  <label>Temporary PIN *</label>
                  <input type="password" bind:value={newChief.temporary_pin} required placeholder="4-6 digit PIN" minlength="4" />
                </div>
              </div>
              <div class="form-actions">
                <button type="button" class="btn btn-secondary" on:click={() => showRegisterForm = false}>Cancel</button>
                <button type="submit" class="btn btn-primary" disabled={isSubmitting}>
                  {#if isSubmitting}
                    Registering...
                  {:else}
                    <Save size={18} />
                    Register Chief
                  {/if}
                </button>
              </div>
            </form>
          </div>
        </div>
      {/if}

      <!-- Map Assignment Mode -->
      {#if showAssignMode}
        <div class="card map-card">
          <div class="card-header">
            <h2><Layers size={20} /> Assign Districts via Map</h2>
            <button class="btn-close" on:click={() => { showAssignMode = false; selectedDistrict = null; selectedChiefForAssignment = null; }}>×</button>
          </div>
          <div class="card-body">
            <div class="map-instructions">
              <p><strong>Instructions:</strong> Click on a district on the map to select it, then choose a chief to assign.</p>
            </div>
            
            <div class="assignment-controls">
              <div class="control-group">
                <label>Selected District:</label>
                <div class="selected-district">
                  {#if selectedDistrict}
                    <span class="district-badge">{selectedDistrict.charAt(0).toUpperCase() + selectedDistrict.slice(1)}</span>
                  {:else}
                    <span class="no-selection">Click a district on the map</span>
                  {/if}
                </div>
              </div>
              
              <div class="control-group">
                <label>Assign to Chief:</label>
                <select bind:value={selectedChiefForAssignment} disabled={!selectedDistrict}>
                  <option value="">Select a Chief</option>
                  {#each chiefs as chief}
                    <option value={chief.id}>{chief.full_name} ({chief.phone})</option>
                  {/each}
                </select>
              </div>
              
              <button class="btn btn-primary" on:click={assignArea} disabled={!selectedDistrict || !selectedChiefForAssignment || isSubmitting}>
                {#if isSubmitting}
                  Assigning...
                {:else}
                  <Save size={18} />
                  Assign District
                {/if}
              </button>
            </div>
            
            <div id="chief-assignment-map" class="map-container"></div>
            
            <div class="legend">
              <h4>Legend</h4>
              <div class="legend-items">
                <div class="legend-item">
                  <div class="legend-color unassigned"></div>
                  <span>Unassigned</span>
                </div>
                {#each chiefs.slice(0, 8) as chief}
                  <div class="legend-item">
                    <div class="legend-color" style="background: {getChiefColor(chief.id.toString())}"></div>
                    <span>{chief.full_name}</span>
                  </div>
                {/each}
              </div>
            </div>
          </div>
        </div>
      {/if}

      <!-- Registered Chiefs List -->
      <div class="section-header">
        <h2>Registered Chiefs <span class="count-badge">{chiefs.length}</span></h2>
      </div>

      {#if chiefs.length === 0}
        <div class="empty-state">
          <User class="empty-icon" />
          <h3>No Chiefs Registered</h3>
          <p>Register chiefs to manage land transactions in their jurisdictions.</p>
        </div>
      {:else}
        <div class="chiefs-grid">
          {#each chiefs as chief}
            <div class="chief-card">
              <div class="chief-header">
                <div class="chief-avatar">
                  <Shield size={32} />
                </div>
                <div class="chief-info">
                  <h4>{chief.full_name}</h4>
                  <div class="chief-details">
                    <span class="detail-item">
                      <User size={14} />
                      {chief.phone}
                    </span>
                    <span class="detail-item">
                      ID: {chief.username}
                    </span>
                  </div>
                </div>
              </div>
              <div class="chief-areas">
                <h5>Assigned Areas</h5>
                {#if chiefAreas.filter(a => a.chief_id === chief.id).length === 0}
                  <p class="no-areas">No areas assigned</p>
                {:else}
                  <div class="areas-list">
                    {#each chiefAreas.filter(a => a.chief_id === chief.id) as area}
                      <div class="area-tag">
                        <span class="area-type">{area.area_type}</span>
                        <span class="area-name">{area.resolved_area_name || area.area_name}</span>
                        <button class="btn-delete" on:click={() => deleteArea(area.id)} title="Remove assignment">
                          <Trash2 size={14} />
                        </button>
                      </div>
                    {/each}
                  </div>
                {/if}
              </div>
              <div class="chief-actions">
                <button class="btn btn-sm btn-secondary" on:click={() => resetChiefPin(chief.id, chief.full_name)}>
                  Reset PIN
                </button>
              </div>
            </div>
          {/each}
        </div>
      {/if}
    {/if}
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

  .page-header {
    margin-bottom: 2rem;
  }

  .back-link {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    color: #64748b;
    text-decoration: none;
    margin-bottom: 1rem;
    font-weight: 500;
    transition: color 0.2s;
  }

  .back-link:hover {
    color: #007A3D;
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

  .loading-state {
    text-align: center;
    padding: 4rem;
    color: #64748b;
  }

  .alert {
    padding: 1rem;
    border-radius: 8px;
    margin-bottom: 1.5rem;
    font-weight: 500;
  }

  .alert.success {
    background: #f0fdf4;
    color: #007A3D;
    border: 1px solid #bbf7d0;
  }

  .alert.error {
    background: #fef2f2;
    color: #dc2626;
    border: 1px solid #fecaca;
  }

  .action-buttons {
    display: flex;
    gap: 1rem;
    margin-bottom: 2rem;
  }

  .btn {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.5rem;
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.9375rem;
    cursor: pointer;
    border: none;
    transition: all 0.2s;
  }

  .btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .btn-primary {
    background: #007A3D;
    color: white;
  }

  .btn-primary:hover:not(:disabled) {
    background: #006633;
  }

  .btn-secondary {
    background: white;
    color: #1e293b;
    border: 1px solid #e2e8f0;
  }

  .btn-secondary:hover:not(:disabled) {
    background: #f8fafc;
    border-color: #cbd5e1;
  }

  .btn-sm {
    padding: 0.5rem 1rem;
    font-size: 0.875rem;
  }

  .btn-close {
    background: none;
    border: none;
    font-size: 1.5rem;
    color: #64748b;
    cursor: pointer;
    padding: 0;
    width: 32px;
    height: 32px;
    border-radius: 6px;
    transition: background 0.2s;
  }

  .btn-close:hover {
    background: #f1f5f9;
  }

  .btn-delete {
    background: none;
    border: none;
    color: #ef4444;
    cursor: pointer;
    padding: 0.25rem;
    border-radius: 4px;
    transition: background 0.2s;
  }

  .btn-delete:hover {
    background: #fef2f2;
  }

  .card {
    background: white;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
    overflow: hidden;
    margin-bottom: 2rem;
  }

  .card-header {
    padding: 1.5rem;
    border-bottom: 1px solid #e2e8f0;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .card-header h2 {
    font-size: 1.125rem;
    font-weight: 600;
    color: #1e293b;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .card-body {
    padding: 1.5rem;
  }

  .form-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1.25rem;
    margin-bottom: 1.5rem;
  }

  .form-group {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .form-group label {
    font-size: 0.875rem;
    font-weight: 600;
    color: #374151;
  }

  .form-group input,
  .form-group select {
    padding: 0.75rem;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    font-size: 0.9375rem;
    transition: border-color 0.2s;
  }

  .form-group input:focus,
  .form-group select:focus {
    outline: none;
    border-color: #007A3D;
  }

  .form-actions {
    display: flex;
    justify-content: flex-end;
    gap: 0.75rem;
  }

  .section-header {
    margin-bottom: 1.25rem;
  }

  .section-header h2 {
    font-size: 1.25rem;
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

  .empty-state {
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

  .chiefs-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
    gap: 1.5rem;
  }

  .chief-card {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    border: 1px solid #e2e8f0;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    transition: box-shadow 0.2s;
  }

  .chief-card:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  }

  .chief-header {
    display: flex;
    gap: 1rem;
    margin-bottom: 1rem;
  }

  .chief-avatar {
    width: 56px;
    height: 56px;
    border-radius: 12px;
    background: #f0fdf4;
    color: #007A3D;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .chief-info {
    flex: 1;
  }

  .chief-info h4 {
    font-size: 1.0625rem;
    font-weight: 600;
    color: #1e293b;
    margin-bottom: 0.5rem;
  }

  .chief-details {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .detail-item {
    display: flex;
    align-items: center;
    gap: 0.375rem;
    font-size: 0.875rem;
    color: #64748b;
  }

  .chief-areas {
    margin-bottom: 1rem;
    padding-top: 1rem;
    border-top: 1px solid #f1f5f9;
  }

  .chief-areas h5 {
    font-size: 0.875rem;
    font-weight: 600;
    color: #374151;
    margin-bottom: 0.75rem;
  }

  .no-areas {
    font-size: 0.875rem;
    color: #94a3b8;
  }

  .areas-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .area-tag {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 0.75rem;
    background: #f8fafc;
    border-radius: 6px;
    font-size: 0.875rem;
  }

  .area-type {
    background: #007A3D;
    color: white;
    font-size: 0.6875rem;
    font-weight: 600;
    padding: 0.15rem 0.5rem;
    border-radius: 4px;
    text-transform: capitalize;
  }

  .area-name {
    flex: 1;
    color: #374151;
  }

  .chief-actions {
    display: flex;
    gap: 0.5rem;
  }

  /* Map Assignment Styles */
  .map-card {
    margin-bottom: 2rem;
  }

  .map-instructions {
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1.5rem;
  }

  .map-instructions p {
    margin: 0;
    color: #166534;
    font-size: 0.9375rem;
  }

  .assignment-controls {
    display: flex;
    align-items: flex-end;
    gap: 1rem;
    margin-bottom: 1.5rem;
    flex-wrap: wrap;
  }

  .control-group {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    flex: 1;
    min-width: 200px;
  }

  .control-group label {
    font-size: 0.875rem;
    font-weight: 600;
    color: #374151;
  }

  .selected-district {
    padding: 0.5rem 0.75rem;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    min-height: 42px;
    display: flex;
    align-items: center;
  }

  .district-badge {
    background: #007A3D;
    color: white;
    padding: 0.25rem 0.75rem;
    border-radius: 4px;
    font-weight: 600;
    font-size: 0.875rem;
  }

  .no-selection {
    color: #94a3b8;
    font-size: 0.875rem;
  }

  .control-group select {
    padding: 0.5rem 0.75rem;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    font-size: 0.9375rem;
    min-height: 42px;
  }

  .control-group select:focus {
    outline: none;
    border-color: #007A3D;
  }

  .map-container {
    height: 500px;
    border-radius: 8px;
    border: 1px solid #e2e8f0;
    overflow: hidden;
    margin-bottom: 1.5rem;
  }

  :global(.leaflet-container) {
    height: 100%;
    width: 100%;
  }

  .legend {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 1rem;
  }

  .legend h4 {
    font-size: 0.875rem;
    font-weight: 600;
    color: #374151;
    margin: 0 0 0.75rem 0;
  }

  .legend-items {
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
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
    border-radius: 4px;
    border: 1px solid rgba(0, 0, 0, 0.1);
  }

  .legend-color.unassigned {
    background: #94a3b8;
  }

  @media (max-width: 768px) {
    .main-content {
      padding: 1rem;
    }

    .action-buttons {
      flex-direction: column;
    }

    .form-grid {
      grid-template-columns: 1fr;
    }

    .chiefs-grid {
      grid-template-columns: 1fr;
    }

    .assignment-controls {
      flex-direction: column;
      align-items: stretch;
    }

    .map-container {
      height: 350px;
    }
  }
</style>
