<script lang="ts">
  import { onMount, tick } from 'svelte';
  import { browser } from '$app/environment';
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import { ArrowLeft, MapPin, User, Ruler, FileText, Image, Video, Calendar, ShieldCheck } from 'lucide-svelte';
  import Navbar from '$lib/components/Navbar.svelte';

  const API = 'http://localhost:5000';
  let claim: any = null;
  let loading = true;
  let error = '';
  let map: any;

  async function loadClaim() {
    try {
      const response = await fetch(`${API}/api/chief/claims/${$page.params.id}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Could not load claim details');
      claim = data;
      await renderMap();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not load claim details';
    } finally {
      loading = false;
    }
  }

  async function renderMap() {
    if (!browser || !claim?.points?.length) return;
    await tick();
    const mapElement = document.getElementById('claim-map');
    if (!mapElement) return;
    const L = (await import('leaflet')).default;
    if (map) map.remove();
    map = L.map(mapElement, { scrollWheelZoom: false });
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);
    const coordinates = claim.points.map((point: any) => [Number(point.lat), Number(point.lng)]);
    const polygon = L.polygon(coordinates, { color: '#007A3D', weight: 3, fillOpacity: 0.25 }).addTo(map);
    polygon.bindPopup(claim.plot_name || 'Claimed boundary');
    map.fitBounds(polygon.getBounds(), { padding: [20, 20] });
  }

  function formatDate(value: string) {
    if (!value) return 'Not recorded';
    return new Date(value).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
  }

  function mediaUrl(path: string) {
    return path?.startsWith('/uploads/') ? `${API}${path}` : `${API}/uploads/${path}`;
  }

  onMount(() => { if (browser) loadClaim(); return () => map?.remove(); });
</script>

<svelte:head>
  <title>{claim?.plot_name || 'Claim Details'} - LandLock Chief</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
</svelte:head>

<Navbar userType="chief" activeLink="/dashboard/chief/pending" showNotification={false} />

<main class="page-content">
  <button class="back" on:click={() => goto('/dashboard/chief/pending')}><ArrowLeft /> Back to Pending Claims</button>
  {#if loading}<section class="panel">Loading complete claim details...</section>
  {:else if error}<section class="panel error">{error}</section>
  {:else if claim}
    <header class="claim-header">
      <div>
        <span class="status">{claim.status || 'Pending'}</span>
        <h1>{claim.plot_name || `Claim #${claim.id}`}</h1>
        <p>Claim submitted {formatDate(claim.created_at)}</p>
      </div>
      <button class="review" on:click={() => goto('/dashboard/chief/pending')}>Return to review</button>
    </header>

    <section class="details-grid">
      <article class="panel wide">
        <h2><MapPin /> Boundary map</h2>
        {#if claim.points?.length}<div id="claim-map"></div>
        {:else}<p class="empty">No map boundary was submitted.</p>{/if}
      </article>

      <article class="panel">
        <h2><User /> Claimant</h2>
        <dl>
          <dt>Name</dt><dd>{claim.owner?.full_name || claim.owner_name || 'Not recorded'}</dd>
          <dt>Phone</dt><dd>{claim.owner?.phone || claim.owner_phone || 'Not recorded'}</dd>
          <dt>Email</dt><dd>{claim.owner?.email || 'Not recorded'}</dd>
        </dl>
      </article>

      <article class="panel">
        <h2><Ruler /> Plot size & location</h2>
        <dl>
          <dt>Estimated size</dt><dd>{claim.estimated_size || 'Not recorded'} {claim.size_unit || ''}</dd>
          <dt>District</dt><dd>{claim.district || 'Not recorded'}</dd>
          <dt>Traditional authority</dt><dd>{claim.traditional_authority || 'Not recorded'}</dd>
          <dt>Village</dt><dd>{claim.village || claim.location || 'Not recorded'}</dd>
          <dt>Land use</dt><dd>{claim.land_use || 'Not recorded'}</dd>
        </dl>
      </article>

      <article class="panel wide">
        <h2><FileText /> Registration details</h2>
        <dl class="two-column">
          <div><dt>Acquisition method</dt><dd>{claim.acquisition_method || 'Not recorded'}</dd></div>
          <div><dt>Landmark</dt><dd>{claim.landmark_description || 'Not recorded'}</dd></div>
          <div><dt>Map boundary</dt><dd>{claim.has_map_boundary ? 'Provided' : 'Not provided'}</dd></div>
          <div><dt>Submitted</dt><dd>{formatDate(claim.created_at)}</dd></div>
          <div class="span"><dt>Description</dt><dd>{claim.description || 'No description provided.'}</dd></div>
          <div class="span"><dt>Witnesses</dt><dd>{Array.isArray(claim.witnesses) ? claim.witnesses.join(', ') || 'None recorded' : claim.witnesses || 'None recorded'}</dd></div>
        </dl>
      </article>

      <article class="panel wide">
        <h2><Image /> Photos & videos</h2>
        {#if claim.media?.length}
          <div class="media-grid">
            {#each claim.media as media}
              <figure>
                {#if media.media_type === 'video'}
                  <video controls src={mediaUrl(media.file_path)}><track kind="captions"></video>
                {:else}
                  <img src={mediaUrl(media.file_path)} alt={media.file_name} />
                {/if}
                <figcaption>{media.file_name}</figcaption>
              </figure>
            {/each}
          </div>
        {:else}
          <p class="empty">No photos or videos were attached to this claim.</p>
        {/if}
      </article>
    </section>
  {/if}
</main>

<style>
  :global(body) { background:#f8fafc; }
  .page-content { margin-left:260px; padding:2rem; max-width:1400px; }
  .back { border:0; background:transparent; color:#007A3D; display:flex; gap:.5rem; align-items:center; font-weight:700; cursor:pointer; margin-bottom:1.5rem; }
  .claim-header { display:flex; justify-content:space-between; align-items:flex-end; gap:1rem; margin-bottom:1.5rem; }
  h1 { font-size:2rem; margin:.35rem 0; }
  h2 { display:flex; align-items:center; gap:.5rem; font-size:1.05rem; }
  .status { background:#dcfce7; color:#166534; padding:.3rem .65rem; border-radius:999px; text-transform:capitalize; font-weight:700; }
  .review { border:0; background:#007A3D; color:white; border-radius:8px; padding:.75rem 1rem; font-weight:700; }
  .details-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:1rem; }
  .panel { background:white; border:1px solid #e2e8f0; border-radius:12px; padding:1.25rem; box-shadow:0 1px 3px rgba(15,23,42,.05); }
  .wide { grid-column:1/-1; }
  #claim-map { height:420px; border-radius:10px; overflow:hidden; }
  dl { display:grid; grid-template-columns:minmax(120px,.5fr) 1fr; gap:.7rem 1rem; margin:1rem 0 0; }
  dt { color:#64748b; font-weight:600; }
  dd { margin:0; overflow-wrap:anywhere; }
  .two-column { grid-template-columns:repeat(2,minmax(0,1fr)); }
  .two-column div { display:grid; grid-template-columns:150px 1fr; gap:.5rem; }
  .span { grid-column:1/-1; }
  .media-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(220px,1fr)); gap:1rem; margin-top:1rem; }
  figure { margin:0; border:1px solid #e2e8f0; border-radius:10px; overflow:hidden; background:#fff; }
  img, video { width:100%; height:220px; object-fit:cover; background:#0f172a; }
  figcaption { padding:.65rem; font-size:.875rem; overflow-wrap:anywhere; }
  .empty, .error { color:#64748b; }
  .error { color:#dc2626; }
  @media (max-width:768px) {
    .page-content { margin-left:0; padding:5rem 1rem 1rem; }
    .claim-header { align-items:flex-start; flex-direction:column; }
    .details-grid, .two-column { grid-template-columns:1fr; }
    .wide, .span { grid-column:auto; }
    #claim-map { height:300px; }
  }
</style>
