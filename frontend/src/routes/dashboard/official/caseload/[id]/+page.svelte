<script lang="ts">
  import { onMount, tick } from "svelte";
  import { browser } from "$app/environment";
  import { page } from "$app/stores";
  import { goto } from "$app/navigation";
  import {
    ArrowLeft,
    MapPin,
    Calendar,
    User,
    Shield,
    Check,
    X,
    FileText,
    Image,
    Ruler,
  } from "lucide-svelte";
  import Navbar from "$lib/components/Navbar.svelte";

  const API = "http://localhost:5000";
  let claim: any = null;
  let loading = true;
  let error = "";
  let map: any;

  function authHeaders() {
    return { Authorization: `Bearer ${localStorage.getItem("token")}` };
  }

  async function fetchClaimDetails() {
    try {
      const response = await fetch(
        `${API}/api/official/caseload/${$page.params.id}`,
        {
          headers: authHeaders(),
        },
      );
      const data = await response.json();
      if (!response.ok)
        throw new Error(data.error || "Could not load claim details");
      claim = data;
      await renderMap();
    } catch (err) {
      error =
        err instanceof Error ? err.message : "Failed to fetch claim details";
    } finally {
      loading = false;
    }
  }

  async function renderMap() {
    if (!browser || !claim?.points?.length) return;
    await tick();
    const mapElement = document.getElementById("claim-map");
    if (!mapElement) return;
    const L = (await import("leaflet")).default;
    if (map) map.remove();
    map = L.map(mapElement, { scrollWheelZoom: false });
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "&copy; OpenStreetMap contributors",
    }).addTo(map);
    const coordinates = claim.points.map((point: any) => [
      Number(point.lat),
      Number(point.lng),
    ]);
    const polygon = L.polygon(coordinates, {
      color: "#007A3D",
      weight: 3,
      fillOpacity: 0.25,
    }).addTo(map);
    polygon.bindPopup(claim.plot_name || "Claimed boundary");
    map.fitBounds(polygon.getBounds(), { padding: [20, 20] });
  }

  async function decide(action: "approve" | "reject") {
    if (!confirm(`Are you sure you want to ${action} this claim?`)) return;

    try {
      const response = await fetch(
        `${API}/api/official/caseload/${claim.id}/approve`,
        {
          method: "POST",
          headers: { ...authHeaders(), "Content-Type": "application/json" },
          body: JSON.stringify({ action }),
        },
      );

      if (response.ok) {
        alert(
          `Claim ${action === "approve" ? "approved" : "rejected"} successfully`,
        );
        await fetchClaimDetails();
      } else {
        alert(`Failed to ${action} claim`);
      }
    } catch (err) {
      console.error(`Error ${action} claim:`, err);
      alert(`Failed to ${action} claim`);
    }
  }

  const approveClaim = () => decide("approve");
  const rejectClaim = () => decide("reject");

  function goBack() {
    goto("/dashboard/official/caseload");
  }

  function formatDate(dateString: string): string {
    if (!dateString) return "N/A";
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  }

  function getStatusColor(status: string): string {
    switch (status) {
      case "approved":
        return "#16a34a";
      case "rejected":
        return "#dc2626";
      case "pending":
        return "#f59e0b";
      default:
        return "#6b7280";
    }
  }

  function mediaUrl(path: string) {
    return path?.startsWith("/uploads/")
      ? `${API}${path}`
      : `${API}/uploads/${path}`;
  }

  onMount(() => {
    if (!browser) return undefined;
    if (!localStorage.getItem("token")) {
      goto("/login");
      return undefined;
    }
    fetchClaimDetails();
    return () => map?.remove();
  });
</script>

<svelte:head>
  <title>{claim?.plot_name || "Claim Details"} - LandLock Official</title>
  <link
    rel="stylesheet"
    href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
  />
</svelte:head>

<Navbar
  userType="official"
  activeLink="/dashboard/official/caseload"
  showNotification={false}
/>

<main class="main-content">
  <button class="back-button" on:click={goBack}>
    <ArrowLeft size={20} />
    <span>Back to Caseload</span>
  </button>

  {#if loading}
    <div class="loading-state"><p>Loading complete claim details...</p></div>
  {:else if error}
    <div class="error-state"><p>{error}</p></div>
  {:else if claim}
    <div class="claim-details-container">
      <!-- Claim Header -->
      <div class="claim-header">
        <div class="header-left">
          <div
            class="status-badge"
            style="background-color: {getStatusColor(claim.status)}"
          >
            {(claim.status || "pending").charAt(0).toUpperCase() +
              (claim.status || "").slice(1)}
          </div>
          <h1>{claim.plot_name || "Claim Details"}</h1>
          <div class="parcel-id">
            MLW-{claim.id} &middot; Submitted {formatDate(claim.created_at)}
          </div>
        </div>

        {#if claim.status === "pending"}
          <div class="actions-section">
            <button class="btn btn-approve" on:click={approveClaim}>
              <Check size={18} /><span>Approve Claim</span>
            </button>
            <button class="btn btn-reject" on:click={rejectClaim}>
              <X size={18} /><span>Reject Claim</span>
            </button>
          </div>
        {/if}
      </div>

      <!-- Map -->
      <article class="panel wide">
        <div class="section-header">
          <MapPin size={20} />
          <h3>Boundary Map</h3>
        </div>
        {#if claim.points?.length}
          <div id="claim-map"></div>
          <div class="points-list">
            {#each claim.points as point, i}
              <div class="point-item">
                <span class="point-number">{i + 1}</span>
                <span class="point-coords"
                  >Lat: {Number(point.lat).toFixed(6)}, Lng: {Number(
                    point.lng,
                  ).toFixed(6)}</span
                >
              </div>
            {/each}
          </div>
        {:else}
          <p class="empty">No map boundary was submitted for this claim.</p>
        {/if}
      </article>

      <!-- Claimant -->
      <div class="claim-info-grid">
        <article class="panel">
          <div class="section-header">
            <User size={20} />
            <h3>Claimant Information</h3>
          </div>
          <dl>
            <dt>Name</dt>
            <dd>
              {claim.owner?.full_name || claim.claimant || "Not recorded"}
            </dd>
            <dt>Phone</dt>
            <dd>{claim.owner?.phone || claim.owner_phone || "Not recorded"}</dd>
            <dt>Email</dt>
            <dd>{claim.owner?.email || "Not recorded"}</dd>
          </dl>
        </article>

        <article class="panel">
          <div class="section-header">
            <Ruler size={20} />
            <h3>Plot Size & Location</h3>
          </div>
          <dl>
            <dt>Estimated size</dt>
            <dd>
              {claim.estimated_size || "Not recorded"}
              {claim.size_unit || ""}
            </dd>
            <dt>District</dt>
            <dd>{claim.district || "Not recorded"}</dd>
            <dt>Traditional authority</dt>
            <dd>{claim.traditional_authority || "Not recorded"}</dd>
            <dt>Village</dt>
            <dd>{claim.village || claim.location || "Not recorded"}</dd>
            <dt>Land use</dt>
            <dd>{claim.land_use || "Not recorded"}</dd>
          </dl>
        </article>
      </div>

      <!-- Registration details -->
      <article class="panel wide">
        <div class="section-header">
          <FileText size={20} />
          <h3>Registration Details</h3>
        </div>
        <dl class="two-column">
          <div>
            <dt>Acquisition method</dt>
            <dd>{claim.acquisition_method || "Not recorded"}</dd>
          </div>
          <div>
            <dt>Landmark</dt>
            <dd>{claim.landmark_description || "Not recorded"}</dd>
          </div>
          <div>
            <dt>Map boundary</dt>
            <dd>{claim.has_map_boundary ? "Provided" : "Not provided"}</dd>
          </div>
          <div>
            <dt>Submitted</dt>
            <dd>{formatDate(claim.created_at)}</dd>
          </div>
          <div class="span">
            <dt>Description</dt>
            <dd>{claim.description || "No description provided."}</dd>
          </div>
          <div class="span">
            <dt>Witnesses</dt>
            <dd>
              {Array.isArray(claim.witnesses)
                ? claim.witnesses.join(", ") || "None recorded"
                : claim.witnesses || "None recorded"}
            </dd>
          </div>
        </dl>
      </article>

      <!-- Media -->
      <article class="panel wide">
        <div class="section-header">
          <Image size={20} />
          <h3>Photos & Videos</h3>
        </div>
        {#if claim.media?.length}
          <div class="media-grid">
            {#each claim.media as media}
              <figure>
                {#if media.media_type === "video"}
                  <video controls src={mediaUrl(media.file_path)}
                    ><track kind="captions" /></video
                  >
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

      <!-- Approval Information -->
      {#if claim.approved_by_name || claim.approved_at}
        <article class="panel wide">
          <div class="section-header">
            <Shield size={20} />
            <h3>Approval Information</h3>
          </div>
          <dl>
            <dt>Approved By</dt>
            <dd>{claim.approved_by_name || "N/A"}</dd>
            <dt>Approved At</dt>
            <dd>{formatDate(claim.approved_at)}</dd>
          </dl>
        </article>
      {/if}
    </div>
  {/if}
</main>

<style>
  :global(*) {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }
  :global(body) {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Roboto",
      sans-serif;
    background: #f8fafc;
    color: #1e293b;
    line-height: 1.5;
  }

  .main-content {
    margin-left: 260px;
    max-width: 1400px;
    padding: 2rem;
    width: calc(100% - 260px);
  }

  .back-button {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    cursor: pointer;
    font-weight: 600;
    color: #64748b;
    transition: all 0.2s;
    margin-bottom: 1.5rem;
    width: fit-content;
  }
  .back-button:hover {
    background: #f8fafc;
    color: #334155;
  }

  .loading-state,
  .error-state {
    text-align: center;
    padding: 4rem;
    color: #64748b;
  }
  .error-state {
    color: #dc2626;
  }

  .claim-details-container {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .claim-header {
    background: white;
    border-radius: 12px;
    padding: 2rem;
    border: 1px solid #e2e8f0;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
  }
  .header-left h1 {
    font-size: 1.75rem;
    font-weight: 700;
    color: #0f172a;
    margin: 0.5rem 0 0.25rem;
  }
  .parcel-id {
    font-size: 0.95rem;
    color: #64748b;
    font-weight: 500;
  }
  .status-badge {
    display: inline-block;
    padding: 0.35rem 0.85rem;
    border-radius: 999px;
    color: white;
    font-weight: 700;
    font-size: 0.8rem;
    text-transform: capitalize;
  }

  .claim-info-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 1rem;
  }

  .panel {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    border: 1px solid #e2e8f0;
    box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);
  }
  .wide {
    grid-column: 1 / -1;
  }

  .section-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 1rem;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid #e2e8f0;
  }
  .section-header h3 {
    font-size: 1.05rem;
    font-weight: 700;
    color: #0f172a;
  }

  #claim-map {
    height: 420px;
    border-radius: 10px;
    overflow: hidden;
    z-index: 0;
  }

  dl {
    display: grid;
    grid-template-columns: minmax(140px, 0.5fr) 1fr;
    gap: 0.7rem 1rem;
    margin-top: 0.5rem;
  }
  dt {
    color: #64748b;
    font-weight: 600;
    font-size: 0.875rem;
  }
  dd {
    margin: 0;
    overflow-wrap: anywhere;
    font-weight: 500;
  }
  .two-column {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .two-column div {
    display: grid;
    grid-template-columns: 160px 1fr;
    gap: 0.5rem;
  }
  .span {
    grid-column: 1 / -1;
  }

  .points-list {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: 0.75rem;
    margin-top: 1rem;
  }
  .point-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.6rem 0.75rem;
    background: #f8fafc;
    border-radius: 8px;
  }
  .point-number {
    width: 26px;
    height: 26px;
    background: #007a3d;
    color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
    font-size: 0.75rem;
    flex-shrink: 0;
  }
  .point-coords {
    color: #0f172a;
    font-weight: 500;
    font-size: 0.85rem;
  }

  .media-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 1rem;
    margin-top: 0.5rem;
  }
  figure {
    margin: 0;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    overflow: hidden;
    background: #fff;
  }
  img,
  video {
    width: 100%;
    height: 220px;
    object-fit: cover;
    background: #0f172a;
    display: block;
  }
  figcaption {
    padding: 0.65rem;
    font-size: 0.8rem;
    color: #475569;
    overflow-wrap: anywhere;
  }

  .actions-section {
    display: flex;
    gap: 1rem;
  }
  .btn {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.5rem;
    border-radius: 8px;
    border: none;
    font-weight: 600;
    font-size: 0.9375rem;
    cursor: pointer;
    transition: all 0.2s;
  }
  .btn-approve {
    background: #16a34a;
    color: white;
  }
  .btn-approve:hover {
    background: #15803d;
  }
  .btn-reject {
    background: #dc2626;
    color: white;
  }
  .btn-reject:hover {
    background: #b91c1c;
  }

  .empty {
    color: #64748b;
  }

  @media (max-width: 768px) {
    .main-content {
      margin-left: 0;
      width: 100%;
      padding: 1rem;
    }
    .claim-header {
      flex-direction: column;
      align-items: flex-start;
    }
    .claim-info-grid,
    .two-column {
      grid-template-columns: 1fr;
    }
    .wide,
    .span {
      grid-column: auto;
    }
    #claim-map {
      height: 300px;
    }
    .actions-section {
      width: 100%;
      flex-direction: column;
    }
    .btn {
      width: 100%;
      justify-content: center;
    }
  }
</style>
