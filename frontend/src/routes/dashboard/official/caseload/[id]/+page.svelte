<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';
  import { browser } from '$app/environment';
  import { ArrowLeft, MapPin, Calendar, User, Shield, Check, X, FileText } from 'lucide-svelte';

  let claim = null;
  let isLoading = true;
  let error = null;
  let isOnline = true;

  const API = 'http://localhost:5000';

  function authHeaders() {
    return { 'Authorization': `Bearer ${localStorage.getItem('token')}` };
  }

  async function fetchClaimDetails() {
    isLoading = true;
    try {
      const claimId = $page.params.id;
      const response = await fetch(`${API}/api/official/caseload`, {
        headers: authHeaders()
      });

      if (response.ok) {
        const claims = await response.json();
        claim = claims.find(c => c.id === parseInt(claimId));
        if (!claim) {
          error = 'Claim not found';
        }
      } else {
        error = 'Failed to fetch claim details';
      }
    } catch (err) {
      console.error('Error fetching claim:', err);
      error = 'Failed to fetch claim details';
    } finally {
      isLoading = false;
    }
  }

  async function approveClaim() {
    if (!confirm('Are you sure you want to approve this claim?')) return;

    try {
      const response = await fetch(`${API}/api/official/caseload/${claim.id}/approve`, {
        method: 'POST',
        headers: {
          ...authHeaders(),
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ action: 'approve' })
      });

      if (response.ok) {
        alert('Claim approved successfully');
        await fetchClaimDetails();
      } else {
        alert('Failed to approve claim');
      }
    } catch (err) {
      console.error('Error approving claim:', err);
      alert('Failed to approve claim');
    }
  }

  async function rejectClaim() {
    if (!confirm('Are you sure you want to reject this claim?')) return;

    try {
      const response = await fetch(`${API}/api/official/caseload/${claim.id}/approve`, {
        method: 'POST',
        headers: {
          ...authHeaders(),
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ action: 'reject' })
      });

      if (response.ok) {
        alert('Claim rejected successfully');
        await fetchClaimDetails();
      } else {
        alert('Failed to reject claim');
      }
    } catch (err) {
      console.error('Error rejecting claim:', err);
      alert('Failed to reject claim');
    }
  }

  function goBack() {
    goto('/dashboard/official/caseload');
  }

  function formatDate(dateString: string): string {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  }

  function getStatusColor(status: string): string {
    switch (status) {
      case 'approved': return '#16a34a';
      case 'rejected': return '#dc2626';
      case 'pending': return '#f59e0b';
      default: return '#6b7280';
    }
  }

  onMount(() => {
    if (!browser) return;
    
    isOnline = navigator.onLine;
    window.addEventListener('online', () => isOnline = true);
    window.addEventListener('offline', () => isOnline = false);

    if (!localStorage.getItem('token')) {
      goto('/login');
      return;
    }

    fetchClaimDetails();
  });
</script>

<svelte:head>
  <title>Claim Details - LandLock</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</svelte:head>

<div class="claim-details-page">
  <!-- Navigation -->
  <nav class="navbar">
    <div class="navbar-content">
      <div class="navbar-brand">
        <div class="logo">
          <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
            <rect width="32" height="32" rx="6" fill="#007A3D"/>
            <path d="M16 8L22 14H18V20H14V14H10L16 8Z" fill="white"/>
          </svg>
        </div>
        <span class="brand-name">LandLock Official Portal</span>
      </div>
      
      <div class="navbar-menu">
        <a href="/dashboard/official" class="nav-link">Dashboard</a>
        <a href="/dashboard/official/caseload" class="nav-link active">My Caseload</a>
        <a href="/register-plot" class="nav-link">Land Registration</a>
        <a href="/map" class="nav-link">Map View</a>
        <a href="/profile" class="nav-link">Account</a>
      </div>

      <div class="navbar-actions">
        <button class="icon-btn">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
            <path d="M10 2a6 6 0 00-6 6v3.586l-.707.707A1 1 0 004 14h12a1 1 0 00.707-1.707L16 11.586V8a6 6 0 00-6-6z"/>
            <path d="M10 18a3 3 0 01-3-3h6a3 3 0 01-3 3z"/>
          </svg>
        </button>
        <div class="avatar">
          <span>O</span>
        </div>
      </div>
    </div>
  </nav>

  <!-- Main Content -->
  <main class="main-content">
    <div class="back-button" on:click={goBack}>
      <ArrowLeft size={20} />
      <span>Back to Caseload</span>
    </div>

    {#if isLoading}
      <div class="loading-state">
        <p>Loading claim details...</p>
      </div>
    {:else if error}
      <div class="error-state">
        <p>{error}</p>
      </div>
    {:else if claim}
      <div class="claim-details-container">
        <!-- Claim Header -->
        <div class="claim-header">
          <div class="header-left">
            <h1>Claim Details</h1>
            <div class="parcel-id">{claim.parcelId}</div>
          </div>
          <div class="header-right">
            <div class="status-badge" style="background-color: {getStatusColor(claim.status)}">
              {claim.status.charAt(0).toUpperCase() + claim.status.slice(1)}
            </div>
          </div>
        </div>

        <!-- Claim Information -->
        <div class="claim-info-grid">
          <div class="info-card">
            <div class="info-card-header">
              <User size={20} />
              <h3>Claimant Information</h3>
            </div>
            <div class="info-card-content">
              <div class="info-row">
                <span class="label">Name:</span>
                <span class="value">{claim.claimant}</span>
              </div>
              <div class="info-row">
                <span class="label">Submitted:</span>
                <span class="value">{formatDate(claim.submittedDate)}</span>
              </div>
            </div>
          </div>

          <div class="info-card">
            <div class="info-card-header">
              <FileText size={20} />
              <h3>Plot Information</h3>
            </div>
            <div class="info-card-content">
              <div class="info-row">
                <span class="label">Plot Name:</span>
                <span class="value">{claim.plot_name}</span>
              </div>
              <div class="info-row">
                <span class="label">Status:</span>
                <span class="value">{claim.status}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Map Boundary -->
        <div class="map-section">
          <div class="section-header">
            <MapPin size={20} />
            <h3>Boundary Points</h3>
          </div>
          <div class="boundary-points">
            {#if claim.points && claim.points.length > 0}
              <div class="points-list">
                {#each claim.points as point, i}
                  <div class="point-item">
                    <span class="point-number">{i + 1}</span>
                    <span class="point-coords">Lat: {point.lat.toFixed(6)}, Lng: {point.lng.toFixed(6)}</span>
                  </div>
                {/each}
              </div>
            {:else}
              <p>No boundary points available</p>
            {/if}
          </div>
        </div>

        <!-- Approval Information -->
        {#if claim.approved_by || claim.approved_at}
          <div class="approval-section">
            <div class="section-header">
              <Shield size={20} />
              <h3>Approval Information</h3>
            </div>
            <div class="approval-info">
              <div class="info-row">
                <span class="label">Approved By:</span>
                <span class="value">{claim.approved_by || 'N/A'}</span>
              </div>
              <div class="info-row">
                <span class="label">Approved At:</span>
                <span class="value">{formatDate(claim.approved_at)}</span>
              </div>
            </div>
          </div>
        {/if}

        <!-- Actions -->
        {#if claim.status === 'pending'}
          <div class="actions-section">
            <button class="btn btn-approve" on:click={approveClaim} disabled={!isOnline}>
              <Check size={18} />
              <span>Approve Claim</span>
            </button>
            <button class="btn btn-reject" on:click={rejectClaim} disabled={!isOnline}>
              <X size={18} />
              <span>Reject Claim</span>
            </button>
          </div>
        {/if}
      </div>
    {/if}
  </main>
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

  .claim-details-page {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  /* Navbar */
  .navbar {
    background: white;
    border-bottom: 1px solid #e2e8f0;
    position: sticky;
    top: 0;
    z-index: 100;
    box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
  }

  .navbar-content {
    max-width: 1400px;
    margin: 0 auto;
    padding: 0 2rem;
    height: 64px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 2rem;
  }

  .navbar-brand {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .brand-name {
    font-size: 1.25rem;
    font-weight: 700;
    color: #0f172a;
    letter-spacing: -0.5px;
  }

  .navbar-menu {
    display: flex;
    gap: 0.5rem;
    flex: 1;
  }

  .nav-link {
    padding: 0.5rem 1rem;
    border-radius: 8px;
    text-decoration: none;
    color: #64748b;
    font-weight: 500;
    font-size: 0.9375rem;
    transition: all 0.2s;
    white-space: nowrap;
  }

  .nav-link:hover {
    background: #f1f5f9;
    color: #334155;
  }

  .nav-link.active {
    background: #007A3D;
    color: white;
  }

  .navbar-actions {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .icon-btn {
    width: 40px;
    height: 40px;
    border-radius: 8px;
    border: none;
    background: #f8fafc;
    color: #64748b;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
  }

  .icon-btn:hover {
    background: #f1f5f9;
    color: #334155;
  }

  .avatar {
    width: 40px;
    height: 40px;
    border-radius: 10px;
    background: #007A3D;
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
    font-size: 0.875rem;
    cursor: pointer;
  }

  /* Main Content */
  .main-content {
    max-width: 1400px;
    margin: 0 auto;
    padding: 2rem;
    width: 100%;
    flex: 1;
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
    margin-bottom: 2rem;
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

  /* Claim Details Container */
  .claim-details-container {
    display: flex;
    flex-direction: column;
    gap: 2rem;
  }

  .claim-header {
    background: white;
    border-radius: 12px;
    padding: 2rem;
    border: 1px solid #e2e8f0;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .header-left h1 {
    font-size: 1.875rem;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 0.5rem;
  }

  .parcel-id {
    font-size: 1rem;
    color: #64748b;
    font-weight: 500;
  }

  .status-badge {
    padding: 0.5rem 1rem;
    border-radius: 8px;
    color: white;
    font-weight: 600;
    font-size: 0.875rem;
  }

  /* Info Grid */
  .claim-info-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1.5rem;
  }

  .info-card {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    border: 1px solid #e2e8f0;
  }

  .info-card-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 1.5rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid #e2e8f0;
  }

  .info-card-header h3 {
    font-size: 1.125rem;
    font-weight: 700;
    color: #0f172a;
  }

  .info-card-content {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .info-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .info-row .label {
    color: #64748b;
    font-weight: 500;
    font-size: 0.875rem;
  }

  .info-row .value {
    color: #0f172a;
    font-weight: 600;
    font-size: 0.875rem;
  }

  /* Map Section */
  .map-section {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    border: 1px solid #e2e8f0;
  }

  .section-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 1.5rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid #e2e8f0;
  }

  .section-header h3 {
    font-size: 1.125rem;
    font-weight: 700;
    color: #0f172a;
  }

  .boundary-points {
    max-height: 300px;
    overflow-y: auto;
  }

  .points-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .point-item {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 0.75rem;
    background: #f8fafc;
    border-radius: 8px;
  }

  .point-number {
    width: 28px;
    height: 28px;
    background: #007A3D;
    color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
    font-size: 0.75rem;
  }

  .point-coords {
    color: #0f172a;
    font-weight: 500;
    font-size: 0.875rem;
  }

  /* Approval Section */
  .approval-section {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    border: 1px solid #e2e8f0;
  }

  .approval-info {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  /* Actions Section */
  .actions-section {
    display: flex;
    gap: 1rem;
    justify-content: flex-end;
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

  .btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .btn-approve {
    background: #16a34a;
    color: white;
  }

  .btn-approve:hover:not(:disabled) {
    background: #15803d;
    transform: translateY(-1px);
  }

  .btn-reject {
    background: #dc2626;
    color: white;
  }

  .btn-reject:hover:not(:disabled) {
    background: #b91c1c;
    transform: translateY(-1px);
  }

  /* Responsive */
  @media (max-width: 768px) {
    .navbar-content {
      padding: 0 1rem;
    }

    .navbar-menu {
      display: none;
    }

    .main-content {
      padding: 1rem;
    }

    .claim-header {
      flex-direction: column;
      align-items: flex-start;
      gap: 1rem;
    }

    .claim-info-grid {
      grid-template-columns: 1fr;
    }

    .actions-section {
      flex-direction: column;
    }

    .btn {
      width: 100%;
      justify-content: center;
    }
  }
</style>
