<script lang="ts">
  import { onMount } from 'svelte';
  import { browser } from '$app/environment';
  import { goto } from '$app/navigation';
  import { Layers, MapPin, Pencil, Save, Trash2 } from 'lucide-svelte';
  import Navbar from '$lib/components/Navbar.svelte';
  import { initMap, addPolygon } from '$lib/map.js';
  import { loadAreaBoundaries, invalidateAreaBoundaries } from '$lib/geo.js';

  let currentUser: any = null;
  let chiefAreas: any[] = [];
  let chiefs: any[] = [];
  let districts: any[] = [];
  let traditionalAuthorities: Record<string, any[]> = {};
  let villages: Record<string, any[]> = {};
  let districtCoordinates: Record<string, number[][]> = {};
  let selectedDistrict = '';
  let selectedChief = '';
  let areaName = '';
  let selectedVillages: string[] = [];
  let areaBoundaries: any[] = [];
  let drawMode: 'chief' | 'village' = 'chief';
  let vectorVillage = ''; // village_id currently being traced
  let editingAreaId: number | null = null; // existing village chief-area being re-traced
  let drawing = false;
  let drawnPoints: number[][] = [];
  let map: any = null;
  let draftPolygon: any = null;
  let draftMarkers: any[] = [];
  let mapLayers: any[] = [];
  let statusMessage = '';
  let renamingAreaId: number | null = null;
  let renameValue = '';
  let currentStep = 1;
  let hasSavedArea = false;
  let searchQuery = '';
  let districtFilter = '';
  let assignmentFilter = '';
  let boundaryFilter = '';
  let currentPage = 1;
  const pageSize = 10;
  let areaToDelete: any = null;
  let deletingVillageVector = false;

  $: filteredChiefAreas = chiefAreas.filter((area) => {
    const chiefName = chiefs.find((chief) => String(chief.id) === String(area.chief_id))?.full_name || '';
    const query = searchQuery.trim().toLowerCase();
    return (!query || [area.area_name, districtName(area.district_id || ''), chiefName]
      .some((value) => value.toLowerCase().includes(query))) &&
      (!districtFilter || area.district_id === districtFilter) &&
      (!assignmentFilter || (assignmentFilter === 'assigned' ? Boolean(area.chief_id) : !area.chief_id)) &&
      (!boundaryFilter || (boundaryFilter === 'mapped' ? Boolean(area.boundary?.length) : !area.boundary?.length));
  });
  $: assignedCount = chiefAreas.filter((area) => area.chief_id).length;
  $: unassignedCount = chiefAreas.length - assignedCount;
  $: totalPages = Math.max(1, Math.ceil(filteredChiefAreas.length / pageSize));
  $: currentPage = Math.min(currentPage, totalPages);
  $: paginatedChiefAreas = filteredChiefAreas.slice((currentPage - 1) * pageSize, currentPage * pageSize);

  const headers = () => ({
    'Content-Type': 'application/json',
    Authorization: `Bearer ${localStorage.getItem('token')}`
  });

  async function loadData() {
    const token = localStorage.getItem('token');
    const [userRes, areasRes, chiefsRes, geographyRes, boundariesRes] = await Promise.all([
      fetch('http://localhost:5000/api/user/me', { headers: { Authorization: `Bearer ${token}` } }),
      fetch('http://localhost:5000/api/official/chief-areas', { headers: { Authorization: `Bearer ${token}` } }),
      fetch('http://localhost:5000/api/official/chiefs', { headers: { Authorization: `Bearer ${token}` } }),
      fetch('http://localhost:5000/api/official/geographic-areas', { headers: { Authorization: `Bearer ${token}` } }),
      fetch('http://localhost:5000/api/admin/district-boundaries')
    ]);
    if ([userRes, areasRes, chiefsRes, geographyRes].some((res) => res.status === 401)) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      goto('/login');
      return;
    }
    areaBoundaries = (await loadAreaBoundaries()) || [];
    if (userRes.ok) currentUser = await userRes.json();
    if (areasRes.ok) {
      chiefAreas = await areasRes.json();
      hasSavedArea = chiefAreas.length > 0;
    }
    if (chiefsRes.ok) chiefs = await chiefsRes.json();
    if (geographyRes.ok) {
      const geography = await geographyRes.json();
      districts = geography.districts || [];
      traditionalAuthorities = geography.traditional_authorities || {};
      villages = geography.villages || {};
    }
    if (boundariesRes.ok) districtCoordinates = await boundariesRes.json();
  }

  async function initializeMap() {
    if (!browser) return;
    const element = document.getElementById('chief-areas-map');
    if (!element) return;
    map = await initMap(element, null);
    map.setView([-13.2543, 34.3015], 7);
    renderMap();
  }

  function renderMap() {
    if (!map) return;
    mapLayers.forEach((layer) => map.removeLayer(layer));
    mapLayers = [];

    Object.entries(districtCoordinates).forEach(([districtId, coords]) => {
      const selected = selectedDistrict === districtId;
    const polygon = addPolygon(map, (coords as number[][]).map((c: number[]) => ({ lat: c[1], lng: c[0] })), districtId, districtId);
      if (!polygon) return;
      polygon.setStyle({
        color: selected ? '#2563eb' : '#64748b',
        fillColor: selected ? '#60a5fa' : '#94a3b8',
        fillOpacity: selected ? 0.25 : 0.08,
        weight: selected ? 3 : 1
      });
      polygon.on('click', () => {
        // While drawing a boundary the district polygons must not swallow the click
        if (!drawing) selectDistrict(districtId);
      });
      mapLayers.push(polygon);
    });

    chiefAreas.forEach((area) => {
      if (!Array.isArray(area.boundary) || area.boundary.length < 3) return;
      const polygon = addPolygon(map, (area.boundary as number[][]).map((c: number[]) => ({ lat: c[1], lng: c[0] })), area.id, area.area_name);
      if (!polygon) return;
      polygon.setStyle({
        color: area.chief_id ? '#007A3D' : '#f59e0b',
        fillColor: area.chief_id ? '#007A3D' : '#fbbf24',
        fillOpacity: 0.35,
        weight: 2
      });
      mapLayers.push(polygon);
    });

    // Village vectors are chief areas of type 'village' with a drawn boundary
    areaBoundaries.forEach((area) => {
      if (area.area_type !== 'village') return;
      if (!Array.isArray(area.boundary) || area.boundary.length < 3) return;
      if (selectedDistrict && area.district_id !== selectedDistrict) return;
      const polygon = addPolygon(map, (area.boundary as number[][]).map((c: number[]) => ({ lat: c[1], lng: c[0] })), area.id, `${area.area_name} (village)`);
      if (!polygon) return;
      polygon.setStyle({
        color: '#7c3aed',
        fillColor: '#a78bfa',
        fillOpacity: 0.3,
        weight: 2,
        dashArray: '4, 4'
      });
      polygon.on('click', () => {
        if (!drawing) {
          vectorVillage = area.area_id;
          editingAreaId = area.id;
          statusMessage = `Editing vector for ${area.area_name}. Draw a new boundary and save to replace it.`;
        }
      });
      mapLayers.push(polygon);
    });
  }

  function selectDistrict(districtId: string) {
    selectedDistrict = districtId;
    selectedVillages = [];
    areaName = '';
    currentStep = districtId ? 2 : 1;
    renderMap();
    if (districtCoordinates[districtId]) {
      map?.fitBounds((districtCoordinates[districtId] as number[][]).map((c: number[]) => [c[1], c[0]]));
    }
  }

  function goToDrawingStep() {
    if (!selectedDistrict || !areaName.trim()) {
      statusMessage = 'Select a district and enter an area name before continuing.';
      return;
    }
    currentStep = 3;
    statusMessage = '';
  }

  function districtVillages() {
    const authorities = traditionalAuthorities[selectedDistrict] || [];
    const result: { id: string, name: string, authority: string }[] = [];
    authorities.forEach((authority) => {
      (villages[`${selectedDistrict}:${authority.id}`] || []).forEach((village) => {
        result.push({ id: village.id, name: village.name, authority: authority.name });
      });
    });
    return result;
  }

  // While tracing, existing polygons (district outlines, other chief areas,
  // previously drawn village vectors) sit on top of the map and swallow clicks,
  // so the map click handler never fires. Make them click-through while drawing.
  function setOverlaysInteractive(interactive: boolean) {
    mapLayers.forEach((layer) => {
      const path = layer.getElement?.();
      if (path) path.style.pointerEvents = interactive ? 'auto' : 'none';
    });
  }

  async function startDrawing(mode: 'chief' | 'village') {
    if (!selectedDistrict) {
      statusMessage = 'Select a district first.';
      return;
    }
    if (mode === 'village' && !vectorVillage) {
      statusMessage = 'Choose a village to trace first.';
      return;
    }
    currentStep = 3;
    drawMode = mode;
    const leaflet = await import('leaflet');
    const L = leaflet.default || leaflet;
    drawing = true;
    drawnPoints = [];
    setOverlaysInteractive(false);
    statusMessage = mode === 'chief'
      ? 'Click the map to add boundary points, then save the chief area.'
      : 'Click the map to trace the village boundary, then save the village vector.';
    if (draftPolygon) map.removeLayer(draftPolygon);
    draftMarkers.forEach((marker) => map.removeLayer(marker));
    draftMarkers = [];
    map.off('click.drawBoundary');
    map.on('click.drawBoundary', (event: any) => {
      drawnPoints = [...drawnPoints, [event.latlng.lng, event.latlng.lat]];
      draftMarkers.push(L.marker(event.latlng).addTo(map));
      if (draftPolygon) map.removeLayer(draftPolygon);
      if (drawnPoints.length >= 3) {
        draftPolygon = L.polygon(drawnPoints.map(([lng, lat]) => [lat, lng]), {
          color: mode === 'chief' ? '#2563eb' : '#7c3aed',
          fillOpacity: 0.25
        }).addTo(map);
      }
    });
  }

  function cancelDrawing() {
    drawing = false;
    drawnPoints = [];
    setOverlaysInteractive(true);
    if (draftPolygon) map.removeLayer(draftPolygon);
    draftMarkers.forEach((marker) => map.removeLayer(marker));
    draftMarkers = [];
    draftPolygon = null;
    map?.off('click.drawBoundary');
  }

  async function saveVillageVector() {
    if (!vectorVillage || drawnPoints.length < 3) {
      statusMessage = 'Pick a village and trace at least three boundary points.';
      return;
    }
    const village = districtVillages().find((v) => v.id === vectorVillage);
    const villageName = village?.name || vectorVillage;
    const payload = {
      area_type: 'village',
      area_id: vectorVillage,
      area_name: villageName,
      district_id: selectedDistrict,
      boundary: drawnPoints,
      villages: [villageName],
      chief_id: null
    };
    const url = editingAreaId
      ? `http://localhost:5000/api/official/chief-areas/${editingAreaId}`
      : 'http://localhost:5000/api/official/chief-areas';
    const response = await fetch(url, {
      method: editingAreaId ? 'PUT' : 'POST',
      headers: headers(),
      body: JSON.stringify(payload)
    });
    if (!response.ok) {
      statusMessage = (await response.json()).error || 'Failed to save village vector.';
      return;
    }
    statusMessage = `Village vector saved for ${villageName}. Assign a chief from the list below.`;
    setOverlaysInteractive(true);
    cancelDrawing();
    editingAreaId = null;
    currentStep = 1;
    invalidateAreaBoundaries();
    await loadData();
    renderMap();
  }

  async function saveChiefArea() {
    if (!selectedDistrict || drawnPoints.length < 3) {
      statusMessage = 'Draw at least three boundary points.';
      return;
    }
    const district = districts.find((item) => item.id === selectedDistrict);
    const response = await fetch('http://localhost:5000/api/official/chief-areas', {
      method: 'POST',
      headers: headers(),
      body: JSON.stringify({
        chief_id: selectedChief || null,
        area_type: 'village',
        area_id: areaName || `${selectedDistrict}-chief-area`,
        area_name: areaName || `${district?.name || selectedDistrict} chief area`,
        district_id: selectedDistrict,
        boundary: drawnPoints,
        villages: selectedVillages
      })
    });
    if (!response.ok) {
      statusMessage = (await response.json()).error || 'Failed to save chief area.';
      return;
    }
    statusMessage = selectedChief ? 'Chief area and assignment saved.' : 'Unassigned chief area saved.';
    hasSavedArea = true;
    setOverlaysInteractive(true);
    cancelDrawing();
    selectedChief = '';
    areaName = '';
    selectedVillages = [];
    currentStep = 1;
    await loadData();
    renderMap();
  }

  async function saveDrawing() {
    if (drawMode === 'village') {
      await saveVillageVector();
    } else {
      await saveChiefArea();
    }
  }

  function areaTypeLabel(t: string): string {
    const map: Record<string, string> = {
      ta: 'Traditional Authority', village: 'Village', ward: 'Ward', district: 'District'
    };
    return map[t] || t;
  }

  function districtName(id: string): string {
    const d = districts.find((x: any) => x.id === id);
    return d ? d.name : id.replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
  }

  function requestDelete(area: any, isVillageVector = false) {
    areaToDelete = area;
    deletingVillageVector = isVillageVector;
  }

  async function confirmDelete() {
    if (!areaToDelete) return;
    const response = await fetch(`http://localhost:5000/api/official/chief-areas/${areaToDelete.id}`, {
      method: 'DELETE',
      headers: headers()
    });
    if (!response.ok) {
      statusMessage = (await response.json()).error || 'Failed to delete chief area.';
      areaToDelete = null;
      return;
    }
    statusMessage = deletingVillageVector
      ? `Village vector for ${areaToDelete.area_name} removed.`
      : `${areaToDelete.area_name} deleted.`;
    areaToDelete = null;
    deletingVillageVector = false;
    invalidateAreaBoundaries();
    await loadData();
    renderMap();
  }

  async function assignChief(area: any, chiefId: string) {
    await fetch(`http://localhost:5000/api/official/chief-areas/${area.id}`, {
      method: 'PUT',
      headers: headers(),
      body: JSON.stringify({ chief_id: chiefId || null, villages: area.villages || [], area_name: area.area_name, district_id: area.district_id })
    });
    await loadData();
    renderMap();
  }

  function startRename(area: any) {
    renamingAreaId = area.id;
    renameValue = area.area_name;
  }

  function cancelRename() {
    renamingAreaId = null;
    renameValue = '';
  }

  async function saveRename(area: any) {
    const newName = renameValue.trim();
    if (!newName) {
      statusMessage = 'Name cannot be empty.';
      return;
    }
    const res = await fetch(`http://localhost:5000/api/official/chief-areas/${area.id}`, {
      method: 'PUT',
      headers: headers(),
      body: JSON.stringify({
        chief_id: area.chief_id || null,
        villages: area.villages || [],
        area_name: newName,
        district_id: area.district_id
      })
    });
    if (!res.ok) {
      statusMessage = (await res.json()).error || 'Failed to rename area.';
      return;
    }
    statusMessage = `Area renamed to "${newName}".`;
    cancelRename();
    invalidateAreaBoundaries();
    await loadData();
    renderMap();
  }

  onMount(async () => {
    if (!browser) return;
    const token = localStorage.getItem('token');
    if (!token) {
      goto('/login');
      return;
    }
    await loadData();
    setTimeout(initializeMap, 300);
  });
</script>

<svelte:head>
  <title>Chief Area Assignment - LandLock Official</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
</svelte:head>

<a class="skip-link" href="#main-content">Skip to main content</a>
<div class="page-wrapper">
  <Navbar userType="official" activeLink="/dashboard/official/chief-areas" userName={currentUser?.full_name || 'Official'} />
  <main id="main-content" class="main-content">
    <div class="page-header">
      <div>
        <h1><Layers style="color: #007A3D" /> Chief Area Assignment</h1>
        <p>Create, review, and manage chief areas across your districts.</p>
      </div>
    </div>
    <p class="summary-line" aria-label="Chief area overview">
      <span>Total chief areas <strong>{chiefAreas.length}</strong></span>
      <span>Assigned <strong>{assignedCount}</strong></span>
      <span>Needs a chief <strong>{unassignedCount}</strong></span>
    </p>

    <section class="map-section">
      <div class="workflow-heading">
        <div>
          <h2>Create a chief area</h2>
          <p>Follow the steps to define an area and assign its chief.</p>
        </div>
      </div>
      <ol class="steps" aria-label="Chief area creation steps">
        <li class:active={currentStep === 1} class:complete={Boolean(selectedDistrict)}>
          <span>1</span><div><strong>Select district</strong><small>Choose the area to work in</small></div>
        </li>
        <li class:active={currentStep === 2} class:complete={currentStep > 2}>
          <span>2</span><div><strong>Name &amp; assign</strong><small>Set a name and optional chief</small></div>
        </li>
        <li class:active={currentStep === 3}>
          <span>3</span><div><strong>Draw on map</strong><small>Mark the area boundary</small></div>
        </li>
      </ol>

      <div class="workflow-form">
        {#if currentStep === 1}
          <label>
            District
            <select value={selectedDistrict} on:change={(event) => selectDistrict(event.currentTarget.value)}>
              <option value="">Choose district</option>
              {#each districts as district}
                <option value={district.id}>{district.name}</option>
              {/each}
            </select>
          </label>
        {:else if currentStep === 2}
          <label>
            Area name
            <input bind:value={areaName} placeholder="Enter a chief area name" />
          </label>
          <label>
            Assigned chief <span class="optional">(optional)</span>
            <select bind:value={selectedChief}>
              <option value="">Leave unassigned</option>
              {#each chiefs as chief}
                <option value={chief.id}>{chief.full_name}</option>
              {/each}
            </select>
          </label>
          <button class="button primary" on:click={goToDrawingStep}><MapPin size={16} /> Continue to map</button>
        {:else}
          <p class="selected-district">District: <strong>{districtName(selectedDistrict)}</strong></p>
          {#if !drawing}
            <button class="button primary" on:click={() => startDrawing('chief')}><Pencil size={16} /> Draw chief area</button>
          {:else}
            <button class="button success" on:click={saveDrawing} disabled={drawnPoints.length < 3}><Save size={16} /> Save {drawMode === 'village' ? 'village vector' : 'chief area'}</button>
            <button class="button secondary" on:click={cancelDrawing}>Cancel drawing</button>
          {/if}
          <button class="button secondary" on:click={() => { currentStep = 2; cancelDrawing(); }}>Back</button>
        {/if}
      </div>
      {#if statusMessage}<p class="status">{statusMessage}</p>{/if}
      <div id="chief-areas-map" class="map-container" class:drawing={drawing}></div>

      {#if selectedDistrict && hasSavedArea}
        <div class="villages-panel">
          <h3>Advanced village tools</h3>
          <p>These tools are available after your first chief area is saved.</p>
          <div class="vector-picker">
            <label>
              Village to trace
              <select bind:value={vectorVillage} on:change={() => { editingAreaId = null; }}>
                <option value="">Choose village</option>
                {#each districtVillages() as village}
                  <option value={village.id}>{village.name} ({village.authority})</option>
                {/each}
              </select>
            </label>
            {#if vectorVillage}
              <button class="button village" on:click={() => startDrawing('village')} disabled={drawing}><Pencil size={16} /> Trace boundary</button>
            {/if}
          </div>
          <div class="village-list">
            {#each districtVillages() as village}
              {@const hasVector = areaBoundaries.some((a) => a.area_type === 'village' && a.area_id === village.id && a.district_id === selectedDistrict)}
              <label class="village-option">
                <input type="checkbox" value={village.id} bind:group={selectedVillages} />
                <span>{village.name}</span><small>{village.authority}{hasVector ? ' • vector saved' : ''}</small>
              </label>
            {/each}
          </div>
          {#if areaBoundaries.filter((a) => a.area_type === 'village' && a.district_id === selectedDistrict).length}
            <div class="saved-vectors">
              <h4>Saved village vectors</h4>
              {#each areaBoundaries.filter((a) => a.area_type === 'village' && a.district_id === selectedDistrict) as vb}
                <div class="saved-vector-row">
                  <span>{vb.village_name}</span>
                  <button class="delete small" on:click={() => requestDelete(vb, true)}><Trash2 size={13} /> Remove</button>
                </div>
              {/each}
            </div>
          {/if}
        </div>
      {/if}
    </section>

    <section>
      <div class="areas-heading">
        <div>
          <h2>Chief areas</h2>
          <p>Search and manage area boundaries and chief assignments.</p>
        </div>
      </div>
      <div class="table-toolbar">
        <label class="search-field">
          Search
          <input bind:value={searchQuery} on:input={() => { currentPage = 1; }} placeholder="Search areas, districts, or chiefs" />
        </label>
        <label>
          District
          <select bind:value={districtFilter} on:change={() => { currentPage = 1; }}>
            <option value="">All districts</option>
            {#each districts as district}
              <option value={district.id}>{district.name}</option>
            {/each}
          </select>
        </label>
        <label>
          Assignment
          <select bind:value={assignmentFilter} on:change={() => { currentPage = 1; }}>
            <option value="">All assignments</option>
            <option value="assigned">Assigned</option>
            <option value="unassigned">Needs a chief</option>
          </select>
        </label>
        <label>
          Boundary
          <select bind:value={boundaryFilter} on:change={() => { currentPage = 1; }}>
            <option value="">All boundaries</option>
            <option value="mapped">Mapped</option>
            <option value="missing">No boundary</option>
          </select>
        </label>
      </div>

      {#if filteredChiefAreas.length}
        <div class="table-scroll">
          <table>
            <thead>
              <tr><th scope="col">Chief area</th><th scope="col">District</th><th scope="col">Boundary</th><th scope="col">Assigned chief</th><th scope="col">Actions</th></tr>
            </thead>
            <tbody>
              {#each paginatedChiefAreas as area}
                <tr>
                  <td>
                    {#if renamingAreaId === area.id}
                      <div class="rename-row">
                        <input
                          aria-label="New area name"
                          bind:value={renameValue}
                          on:keydown={(e) => {
                            if (e.key === 'Enter') saveRename(area);
                            if (e.key === 'Escape') cancelRename();
                          }}
                        />
                        <button class="button success small-btn" on:click={() => saveRename(area)} aria-label="Save area name"><Save size={14} /></button>
                        <button class="button secondary small-btn" on:click={cancelRename} aria-label="Cancel rename">✕</button>
                      </div>
                    {:else}
                      <strong>{area.area_name}</strong>
                      {#if area.area_type}<small class="cell-subtitle">{areaTypeLabel(area.area_type)}</small>{/if}
                    {/if}
                  </td>
                  <td>{area.district_id ? districtName(area.district_id) : '—'}</td>
                  <td>{#if area.boundary?.length}<span class="badge mapped">Mapped</span>{:else}<span class="badge">No boundary</span>{/if}</td>
                  <td>
                    <select aria-label={`Assigned chief for ${area.area_name}`} value={area.chief_id || ''} on:change={(event) => assignChief(area, event.currentTarget.value)}>
                      <option value="">Unassigned</option>
                      {#each chiefs as chief}
                        <option value={chief.id}>{chief.full_name}</option>
                      {/each}
                    </select>
                  </td>
                  <td>
                    <div class="row-actions">
                      {#if renamingAreaId !== area.id}
                        <button class="icon-btn" on:click={() => startRename(area)} aria-label={`Rename ${area.area_name}`}><Pencil size={15} /></button>
                      {/if}
                      <button class="icon-btn delete-action" on:click={() => requestDelete(area)} aria-label={`Delete ${area.area_name}`}><Trash2 size={15} /></button>
                    </div>
                  </td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
        <div class="pagination">
          <span>Showing {(currentPage - 1) * pageSize + 1}–{Math.min(currentPage * pageSize, filteredChiefAreas.length)} of {filteredChiefAreas.length} areas</span>
          <div>
            <button class="button secondary" on:click={() => currentPage--} disabled={currentPage <= 1} aria-label="Previous page">Previous</button>
            <span aria-live="polite">Page {currentPage} of {totalPages}</span>
            <button class="button secondary" on:click={() => currentPage++} disabled={currentPage >= totalPages} aria-label="Next page">Next</button>
          </div>
        </div>
      {:else}
        <div class="empty-state" role="status">
          <MapPin size={28} />
          {#if chiefAreas.length}
            <h3>No matching chief areas</h3>
            <p>Try changing your search or filters.</p>
          {:else}
            <h3>No chief areas yet</h3>
            <p>Select a district above to create the first area.</p>
          {/if}
        </div>
      {/if}
    </section>
  </main>
</div>

{#if areaToDelete}
  <div class="modal-backdrop">
    <div class="confirm-modal" role="dialog" aria-modal="true" aria-labelledby="delete-title" aria-describedby="delete-description">
      <h2 id="delete-title">{deletingVillageVector ? 'Remove village vector?' : 'Delete chief area?'}</h2>
      <p id="delete-description">
        {#if deletingVillageVector}
          Removing the vector for <strong>{areaToDelete.area_name}</strong> will also delete its chief area record. This cannot be undone.
        {:else}
          <strong>{areaToDelete.area_name}</strong> and its boundary will be permanently deleted. This cannot be undone.
        {/if}
      </p>
      <div class="modal-actions">
        <button class="button secondary" on:click={() => { areaToDelete = null; }}>Cancel</button>
        <button class="button danger" on:click={confirmDelete}>Delete permanently</button>
      </div>
    </div>
  </div>
{/if}

<style>
  .skip-link { position: absolute; top: -48px; left: 1rem; z-index: 10000; padding: .65rem 1rem; border-radius: 6px; background: #fff; color: #14532d; font-weight: 700; }
  .skip-link:focus { top: 1rem; }
  .page-wrapper { min-height: 100vh; background: #f8fafc; }
  .main-content { max-width: 1400px; margin: auto; padding: 2rem; }
  .page-header h1 { display: flex; align-items: center; gap: .5rem; font-size: 2rem; color: #1e293b; }
  .page-header p { color: #64748b; }
  .summary-line { display: flex; flex-wrap: wrap; gap: .5rem 1.25rem; margin: .75rem 0 1.25rem; color: #475569; }
  .summary-line strong { margin-left: .25rem; color: #1e293b; }
  .map-section, .main-content > section { background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 1.25rem; margin: 1rem 0 2rem; }
  .areas-heading p, .workflow-heading p { color: #64748b; }
  .workflow-heading, .areas-heading { display: flex; justify-content: space-between; align-items: center; }
  .workflow-heading h2, .areas-heading h2 { margin: 0; color: #1e293b; }
  .workflow-heading p, .areas-heading p { margin: .35rem 0 0; }
  .steps { display: grid; grid-template-columns: repeat(3, 1fr); list-style: none; gap: .75rem; margin: 1.25rem 0; padding: 0; }
  .steps li { display: flex; align-items: center; gap: .65rem; padding: .75rem; border-radius: 8px; background: #f8fafc; color: #64748b; }
  .steps li > span { display: grid; place-items: center; width: 2rem; height: 2rem; flex: 0 0 auto; border-radius: 50%; background: #e2e8f0; font-weight: 700; }
  .steps li.active { background: #eff6ff; color: #1d4ed8; }
  .steps li.active > span { color: white; background: #2563eb; }
  .steps li.complete > span { color: white; background: #15803d; }
  .steps li div { display: grid; gap: .15rem; }
  .steps small { color: #64748b; }
  .workflow-form { display: flex; align-items: end; gap: .75rem; flex-wrap: wrap; }
  .workflow-form label { min-width: 220px; flex: 1; }
  .workflow-form .selected-district { margin: 0 auto 0 0; color: #475569; }
  .optional { color: #64748b; font-weight: 400; }
  label { display: flex; flex-direction: column; gap: .35rem; color: #334155; font-size: .875rem; font-weight: 600; }
  select, input { height: 40px; border: 1px solid #cbd5e1; border-radius: 7px; padding: 0 .65rem; background: white; }
  .button, .delete { border: 0; border-radius: 7px; height: 40px; padding: 0 .85rem; cursor: pointer; display: inline-flex; align-items: center; gap: .35rem; }
  .primary { background: #2563eb; color: white; } .success { background: #007A3D; color: white; } .secondary { background: #e2e8f0; color: #334155; }
  .village { background: #7c3aed; color: white; }
  .danger { color: white; background: #b91c1c; }
  button:disabled { opacity: .55; cursor: not-allowed; }
  button:focus-visible, a:focus-visible, input:focus-visible, select:focus-visible { outline: 3px solid #2563eb; outline-offset: 2px; }
  .status { color: #0369a1; font-weight: 600; }
  .map-container { height: 520px; border-radius: 8px; overflow: hidden; margin-top: 1rem; border: 1px solid #cbd5e1; }
  /* Pen cursor shown while drawing a boundary */
  .map-container.drawing {
    cursor: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='28' height='28' viewBox='0 0 24 24' fill='%232563eb' stroke='white' stroke-width='1.5'><path d='M12 19l7-7 3 3-7 7-3-3z'/><path d='M18 13l-1.5-7.5L2 2l3.5 14.5L13 18l5-5z'/><circle cx='11' cy='11' r='2'/></svg>") 2 2, crosshair;
  }
  .villages-panel { margin-top: 1rem; border-top: 1px solid #e2e8f0; padding-top: 1rem; }
  .villages-panel h3 { margin-bottom: .25rem; } .villages-panel p { color: #64748b; }
  .village-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: .5rem; max-height: 220px; overflow: auto; }
  .village-option { display: grid; grid-template-columns: 18px 1fr; align-items: center; border: 1px solid #e2e8f0; border-radius: 7px; padding: .65rem; }
  .village-option input { height: auto; } .village-option small { grid-column: 2; color: #64748b; }
  .vector-picker { display: flex; gap: .75rem; align-items: end; margin: .75rem 0; flex-wrap: wrap; }
  .vector-picker label { min-width: 260px; }
  .vector-picker .button { flex: 0 0 auto; }
  .saved-vectors { margin-top: .75rem; }
  .saved-vectors h4 { margin: .25rem 0 .5rem; }
  .saved-vector-row { display: flex; justify-content: space-between; align-items: center; padding: .4rem .6rem; border: 1px solid #e2e8f0; border-radius: 7px; margin-bottom: .4rem; }
  .delete.small { height: 28px; padding: 0 .55rem; font-size: .8rem; }
  .rename-row { display: flex; gap: .35rem; align-items: center; }
  .rename-row input { flex: 1; height: 32px; }
  .small-btn { height: 28px; padding: 0 .5rem; }
  .icon-btn {
    border: 0; background: transparent; cursor: pointer; color: #64748b;
    padding: 2px; border-radius: 4px; display: inline-flex;
  }
  .icon-btn:hover { color: #2563eb; background: #eff6ff; }
  .table-toolbar { display: grid; grid-template-columns: minmax(220px, 2fr) repeat(3, minmax(145px, 1fr)); gap: .75rem; align-items: end; margin: 1.25rem 0; }
  .table-scroll { overflow-x: auto; border: 1px solid #e2e8f0; border-radius: 8px; }
  table { width: 100%; border-collapse: collapse; text-align: left; }
  th, td { padding: .85rem 1rem; border-bottom: 1px solid #e2e8f0; vertical-align: middle; }
  th { background: #f8fafc; color: #475569; font-size: .8rem; font-weight: 700; text-transform: uppercase; letter-spacing: .03em; white-space: nowrap; }
  tbody tr:last-child td { border-bottom: 0; }
  td select { min-width: 150px; max-width: 220px; }
  .cell-subtitle { display: block; margin-top: .25rem; color: #64748b; }
  .badge { display: inline-block; color: #92400e; background: #fef3c7; padding: .25rem .55rem; border-radius: 999px; font-size: .75rem; white-space: nowrap; }
  .mapped { color: #166534; background: #dcfce7; }
  .row-actions { display: flex; gap: .35rem; }
  .delete-action { color: #b91c1c; }
  .delete-action:hover { color: #991b1b; background: #fee2e2; }
  .pagination { display: flex; justify-content: space-between; align-items: center; gap: 1rem; margin-top: 1rem; color: #64748b; font-size: .9rem; }
  .pagination > div { display: flex; align-items: center; gap: .75rem; }
  .pagination .button { height: 34px; }
  .empty-state { display: grid; justify-items: center; gap: .5rem; padding: 2.5rem 1rem; text-align: center; color: #64748b; }
  .empty-state h3, .empty-state p { margin: 0; }
  .empty-state h3 { color: #1e293b; }
  .delete { margin-top: .75rem; height: 32px; color: #b91c1c; background: #fee2e2; }
  .modal-backdrop { position: fixed; inset: 0; z-index: 2000; display: grid; place-items: center; padding: 1rem; background: rgb(15 23 42 / 55%); }
  .confirm-modal { width: min(100%, 440px); padding: 1.5rem; border-radius: 12px; background: white; box-shadow: 0 20px 50px rgb(15 23 42 / 25%); }
  .confirm-modal h2 { margin: 0; color: #1e293b; font-size: 1.25rem; }
  .confirm-modal p { margin: 1rem 0 1.5rem; color: #475569; line-height: 1.5; }
  .modal-actions { display: flex; justify-content: flex-end; gap: .75rem; }
  @media (max-width: 900px) {
    .main-content { padding: 1.25rem; }
    .table-toolbar { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .map-container { height: 420px; }
  }
  @media (max-width: 600px) {
    .steps { grid-template-columns: 1fr; gap: .5rem; }
    .table-toolbar { grid-template-columns: 1fr; }
    .pagination { align-items: flex-start; flex-direction: column; }
    .pagination > div { width: 100%; justify-content: space-between; }
  }
</style>
