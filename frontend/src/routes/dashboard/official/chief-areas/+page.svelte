<script lang="ts">
  import { onMount } from 'svelte';
  import { browser } from '$app/environment';
  import { goto } from '$app/navigation';
  import { Layers, MapPin, Pencil, Save, Trash2, User } from 'lucide-svelte';
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
    if (areasRes.ok) chiefAreas = await areasRes.json();
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
    renderMap();
    map?.fitBounds((districtCoordinates[districtId] as number[][]).map((c: number[]) => [c[1], c[0]]));
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
    setOverlaysInteractive(true);
    cancelDrawing();
    selectedChief = '';
    areaName = '';
    selectedVillages = [];
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

  function deleteVillageVector(area: any) {
    if (!confirm(`Delete the vector for ${area.area_name}? This removes the chief area too.`)) return;
    fetch(`http://localhost:5000/api/official/chief-areas/${area.id}`, {
      method: 'DELETE',
      headers: headers()
    }).then(async () => {
      invalidateAreaBoundaries();
      await loadData();
      renderMap();
    });
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

  async function deleteArea(area: any) {
    if (!confirm(`Delete ${area.area_name}?`)) return;
    await fetch(`http://localhost:5000/api/official/chief-areas/${area.id}`, {
      method: 'DELETE',
      headers: headers()
    });
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

<div class="page-wrapper">
  <Navbar userType="official" activeLink="/dashboard/official/chief-areas" userName={currentUser?.full_name || 'Official'} />
  <main class="main-content">
    <div class="page-header">
      <div>
        <h1><Layers class="header-icon" /> Chief Area Assignment</h1>
        <p>Select a district, draw a chief area, and assign it now or later.</p>
      </div>
    </div>

    <section class="map-section">
      <div class="controls">
        <label>
          District
          <select bind:value={selectedDistrict} on:change={() => selectDistrict(selectedDistrict)}>
            <option value="">Choose district</option>
            {#each districts as district}
              <option value={district.id}>{district.name}</option>
            {/each}
          </select>
        </label>
        <label>
          Area name
          <input bind:value={areaName} placeholder="Chief area name" />
        </label>
        <label>
          Chief (optional)
          <select bind:value={selectedChief}>
            <option value="">Leave unassigned</option>
            {#each chiefs as chief}
              <option value={chief.id}>{chief.full_name}</option>
            {/each}
          </select>
        </label>
        <button class="button primary" on:click={() => startDrawing('chief')} disabled={drawing}><Pencil size={16} /> Draw chief area</button>
        <button class="button village" on:click={() => startDrawing('village')} disabled={drawing || !selectedDistrict}><Pencil size={16} /> Trace village vector</button>
        {#if drawing}
          <button class="button success" on:click={saveDrawing}><Save size={16} /> Save {drawMode === 'village' ? 'village vector' : 'area'}</button>
          <button class="button secondary" on:click={cancelDrawing}>Cancel</button>
        {/if}
      </div>
      {#if statusMessage}<p class="status">{statusMessage}</p>{/if}
      <div id="chief-areas-map" class="map-container" class:drawing={drawing}></div>

      {#if selectedDistrict}
        <div class="villages-panel">
          <h3>Villages in selected district</h3>
          <p>Trace a village vector on the map, or tick villages to include them in the chief area.</p>
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
                  <button class="delete small" on:click={() => deleteVillageVector(vb)}><Trash2 size={13} /> Remove</button>
                </div>
              {/each}
            </div>
          {/if}
        </div>
      {/if}
    </section>

    <section>
      <h2>Chief Areas</h2>
      <div class="areas-grid">
        {#each chiefAreas as area}
          <article class="area-card">
            <div>
              <h3><MapPin size={18} /> {area.area_name}</h3>
              {#if area.boundary}<span class="badge mapped">Mapped</span>{:else}<span class="badge">No boundary</span>{/if}
            </div>
            <label>
              Assigned chief
              <select value={area.chief_id || ''} on:change={(event) => assignChief(area, event.currentTarget.value)}>
                <option value="">Unassigned</option>
                {#each chiefs as chief}
                  <option value={chief.id}>{chief.full_name}</option>
                {/each}
              </select>
            </label>
            {#if area.villages?.length}<p class="villages">{area.villages.join(', ')}</p>{/if}
            <button class="delete" on:click={() => deleteArea(area)}><Trash2 size={15} /> Delete</button>
          </article>
        {:else}
          <p>No chief areas have been created.</p>
        {/each}
      </div>
    </section>
  </main>
</div>

<style>
  .page-wrapper { min-height: 100vh; background: #f8fafc; }
  .main-content { max-width: 1400px; margin: auto; padding: 2rem; }
  .page-header h1 { display: flex; align-items: center; gap: .5rem; font-size: 2rem; color: #1e293b; }
  .page-header p { color: #64748b; }
  .header-icon { color: #007A3D; }
  .map-section, section { background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 1.25rem; margin: 1rem 0 2rem; }
  .controls { display: grid; grid-template-columns: repeat(3, minmax(160px, 1fr)) auto auto auto; gap: .75rem; align-items: end; }
  label { display: flex; flex-direction: column; gap: .35rem; color: #334155; font-size: .875rem; font-weight: 600; }
  select, input { height: 40px; border: 1px solid #cbd5e1; border-radius: 7px; padding: 0 .65rem; background: white; }
  .button, .delete { border: 0; border-radius: 7px; height: 40px; padding: 0 .85rem; cursor: pointer; display: inline-flex; align-items: center; gap: .35rem; }
  .primary { background: #2563eb; color: white; } .success { background: #007A3D; color: white; } .secondary { background: #e2e8f0; color: #334155; }
  .village { background: #7c3aed; color: white; }
  button:disabled { opacity: .55; cursor: not-allowed; }
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
  .saved-vectors { margin-top: .75rem; }
  .saved-vectors h4 { margin: .25rem 0 .5rem; }
  .saved-vector-row { display: flex; justify-content: space-between; align-items: center; padding: .4rem .6rem; border: 1px solid #e2e8f0; border-radius: 7px; margin-bottom: .4rem; }
  .delete.small { height: 28px; padding: 0 .55rem; font-size: .8rem; }
  .areas-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1rem; }
  .area-card { border: 1px solid #e2e8f0; border-radius: 10px; padding: 1rem; }
  .area-card h3 { display: flex; align-items: center; gap: .35rem; } .badge { color: #92400e; background: #fef3c7; padding: .2rem .45rem; border-radius: 999px; font-size: .75rem; }
  .mapped { color: #166534; background: #dcfce7; } .villages { font-size: .85rem; color: #64748b; }
  .delete { margin-top: .75rem; height: 32px; color: #b91c1c; background: #fee2e2; }
  @media (max-width: 900px) { .controls { grid-template-columns: 1fr 1fr; } .map-container { height: 420px; } }
</style>
