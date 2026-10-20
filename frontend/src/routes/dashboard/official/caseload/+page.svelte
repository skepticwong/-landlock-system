<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { browser } from '$app/environment';
  import { fade } from 'svelte/transition';
  import { Eye, Edit, Search, ClipboardList, WifiOff, AlertTriangle, Check, X } from 'lucide-svelte';
  import Navbar from '$lib/components/Navbar.svelte';

  interface Claim {
    id: number;
    parcelId: string;
    plot_name: string;
    claimant: string;
    status: 'pending' | 'approved' | 'rejected';
    submittedDate: string;
    approved_by: string | null;
    approved_at: string | null;
    points: any[];
  }

  let isOnline = true;
  let claims: Claim[] = [];
  let isLoading = true;

  async function loadClaims() {
    try {
      const res = await fetch(`${API}/api/official/caseload`, { headers: authHeaders() });
      if (res.ok) {
        const data = await res.json();
        claims = data;
      }
    } catch (err) {
      console.error('Error loading caseload:', err);
    } finally {
      isLoading = false;
    }
  }

  async function approvePlot(plotId: number) {
    try {
      const res = await fetch(`${API}/api/official/caseload/${plotId}/approve`, {
        method: 'POST',
        headers: {
          ...authHeaders(),
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ action: 'approve' })
      });
      if (res.ok) {
        await loadClaims();
      }
    } catch (err) {
      console.error('Error approving plot:', err);
    }
  }

  async function rejectPlot(plotId: number) {
    try {
      const res = await fetch(`${API}/api/official/caseload/${plotId}/approve`, {
        method: 'POST',
        headers: {
          ...authHeaders(),
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ action: 'reject' })
      });
      if (res.ok) {
        await loadClaims();
      }
    } catch (err) {
      console.error('Error rejecting plot:', err);
    }
  }

  let filterStatus = 'all';
  let searchQuery = '';

  function handleOnline() {
    isOnline = true;
  }

  function handleOffline() {
    isOnline = false;
  }

  function filteredClaims() {
    return claims.filter(claim => {
      const matchesStatus = filterStatus === 'all' || claim.status === filterStatus;
      const matchesSearch = searchQuery === '' ||
        claim.claimant.toLowerCase().includes(searchQuery.toLowerCase()) ||
        claim.parcelId.toLowerCase().includes(searchQuery.toLowerCase()) ||
        claim.plot_name.toLowerCase().includes(searchQuery.toLowerCase());
      return matchesStatus && matchesSearch;
    });
  }

  function getStatusColor(status: string) {
    switch (status) {
      case 'pending': return '#f59e0b';
      case 'approved': return '#10b981';
      case 'rejected': return '#ef4444';
      default: return '#6b7280';
    }
  }

  function viewClaim(claimId: number) {
    goto(`/dashboard/official/caseload/${claimId}`);
  }

  function timeAgo(isoString: string): string {
    if (!isoString) return '';
    const diff = Date.now() - new Date(isoString).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    return `${Math.floor(hrs / 24)}d ago`;
  }

  const API = 'http://localhost:5000';

  function authHeaders() {
    return { 'Authorization': `Bearer ${localStorage.getItem('token')}` };
  }

  onMount(async () => {
    if (!browser) return;

    if (!localStorage.getItem('token')) {
      goto('/login');
      return;
    }

    try {
      const res = await fetch(`${API}/api/user/me`, { headers: authHeaders() });
      if (res.ok) {
        const u = await res.json();
        if (!u.is_superuser && !u.is_staff) {
          goto('/dashboard');
          return;
        }
      } else {
        goto('/login');
        return;
      }
    } catch (err) {
      console.error('Error verifying admin status:', err);
      goto('/login');
      return;
    }

    loadClaims();
    isOnline = navigator.onLine;

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  });
</script>

<div class="caseload-container">
  <Navbar userType="official" activeLink="/dashboard/official/caseload" userName="Official" showNotification={false} />

  <main class="main-content">
    <div class="page-header">
      <div class="header-content">
        <h1>My Caseload</h1>
        <p>Manage and review land claim applications</p>
      </div>
      
      {#if !isOnline}
        <div class="offline-indicator">
          <WifiOff size={16} style="display: inline-block; vertical-align: middle; margin-right: 0.25rem;" /> Offline Mode - Limited functionality
        </div>
      {/if}
    </div>

    <div class="filters-section">
      <div class="search-bar">
        <input
          type="text"
          placeholder="Search by claimant, parcel ID, or plot name..."
          bind:value={searchQuery}
          class="search-input"
        />
      </div>

      <div class="filter-controls">
        <select bind:value={filterStatus} class="filter-select">
          <option value="all">All Status</option>
          <option value="pending">Pending</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
        </select>
      </div>
    </div>

    {#if isLoading}
      <div class="loading-state">
        <p>Loading caseload...</p>
      </div>
    {:else}
      <div class="claims-grid">
        {#each filteredClaims() as claim (claim.id)}
          <div class="claim-card" transition:fade={{ duration: 200 }}>
            <div class="claim-header">
              <div class="parcel-id">{claim.parcelId}</div>
              <div class="status-badge" style="background-color: {getStatusColor(claim.status)}">
                {claim.status.charAt(0).toUpperCase() + claim.status.slice(1)}
              </div>
            </div>

            <div class="claim-content">
              <h3 class="claimant-name">{claim.claimant}</h3>
              <div class="plot-name">{claim.plot_name}</div>
              <div class="claim-details">
                <div class="detail-item">
                  <span class="detail-label">Submitted:</span>
                  <span class="detail-value">{timeAgo(claim.submittedDate)}</span>
                </div>
                {#if claim.approved_by}
                  <div class="detail-item">
                    <span class="detail-label">Approved by:</span>
                    <span class="detail-value">{claim.approved_by}</span>
                  </div>
                {/if}
              </div>

              <div class="claim-footer">
                {#if claim.status === 'pending'}
                  <div class="claim-actions">
                    <button
                      class="action-btn approve-btn"
                      on:click={() => approvePlot(claim.id)}
                      disabled={!isOnline}
                    >
                      <span class="btn-flex"><Check size={14} style="margin-right: 0.25rem;" /> Approve</span>
                    </button>
                    <button
                      class="action-btn reject-btn"
                      on:click={() => rejectPlot(claim.id)}
                      disabled={!isOnline}
                    >
                      <span class="btn-flex"><X size={14} style="margin-right: 0.25rem;" /> Reject</span>
                    </button>
                  </div>
                {:else}
                  <button
                    class="action-btn view-btn"
                    on:click={() => viewClaim(claim.id)}
                    disabled={!isOnline}
                  >
                    <span class="btn-flex"><Eye size={14} style="margin-right: 0.25rem;" /> View</span>
                  </button>
                {/if}
              </div>
            </div>
          </div>
        {/each}
      </div>

      {#if filteredClaims().length === 0}
        <div class="empty-state">
          <div class="empty-icon"><ClipboardList size={48} style="margin: 0 auto 1rem auto; color: #94a3b8;" /></div>
          <h3>No claims found</h3>
          <p>Try adjusting your search or filters</p>
        </div>
      {/if}
    {/if}
  </main>
</div>

<style>
  .caseload-container {
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

  .page-header {
    margin-bottom: 2rem;
  }

  .header-content {
    margin-bottom: 1rem;
  }

  .back-link {
    color: var(--color-primary);
    cursor: pointer;
    font-weight: 600;
    margin-bottom: 1rem;
    transition: color 0.2s;
  }

  .back-link:hover {
    color: var(--color-primary-hover);
  }

  .page-header h1 {
    font-size: 2.5rem;
    font-weight: 700;
    color: #1e293b;
    margin-bottom: 0.5rem;
  }

  .page-header p {
    font-size: 1.125rem;
    color: #64748b;
  }

  .offline-indicator {
    background: #fef3c7;
    color: #92400e;
    padding: 0.75rem 1rem;
    border-radius: 8px;
    border: 1px solid #fcd34d;
    font-weight: 500;
    display: inline-block;
  }

  .filters-section {
    display: flex;
    gap: 1rem;
    margin-bottom: 2rem;
    align-items: center;
  }

  .search-bar {
    flex: 1;
  }

  .search-input {
    width: 100%;
    padding: 0.75rem 1rem;
    border: 2px solid #e2e8f0;
    border-radius: 8px;
    font-size: 1rem;
    transition: border-color 0.2s;
  }

  .search-input:focus {
    outline: none;
    border-color: var(--color-primary);
    box-shadow: 0 0 0 3px rgba(0,122,61,0.15);
  }

  .filter-select {
    padding: 0.75rem 1rem;
    border: 2px solid #e2e8f0;
    border-radius: 8px;
    font-size: 1rem;
    background: white;
    cursor: pointer;
    transition: border-color 0.2s;
  }

  .filter-select:focus {
    outline: none;
    border-color: var(--color-primary);
  }

  .claims-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
    gap: 1.5rem;
  }

  .claim-card {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    border: 2px solid #e2e8f0;
    transition: all 0.3s ease;
  }

  .claim-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 15px rgba(0, 0, 0, 0.15);
    border-color: var(--color-primary);
  }

  .claim-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }

  .parcel-id {
    font-family: monospace;
    font-weight: 600;
    color: #1e293b;
    font-size: 1.125rem;
  }

  .priority-badge {
    color: white;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
  }

  .claimant-name {
    font-size: 1.25rem;
    font-weight: 600;
    color: #1e293b;
    margin-bottom: 0.5rem;
  }

  .plot-name {
    font-size: 0.875rem;
    color: #64748b;
    margin-bottom: 1rem;
  }

  .claim-details {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    margin-bottom: 1rem;
  }

  .detail-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .detail-label {
    color: #64748b;
    font-size: 0.875rem;
  }

  .detail-value {
    color: #1e293b;
    font-weight: 500;
  }

  .claim-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 1rem;
    padding-top: 1rem;
    border-top: 1px solid #e2e8f0;
  }

  .status-badge {
    color: white;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    font-size: 0.875rem;
    font-weight: 600;
  }

  .claim-actions {
    display: flex;
    gap: 0.5rem;
  }

  .btn-flex {
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }

  .action-btn {
    padding: 0.5rem 0.875rem;
    border-radius: 6px;
    font-size: 0.8125rem;
    cursor: pointer;
    transition: all 0.2s;
    font-weight: 600;
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    border: 1.5px solid transparent;
  }

  .action-btn:disabled {
    opacity: 0.45;
    cursor: not-allowed;
  }

  .view-btn {
    background: #1e293b;
    color: #f8fafc;
    border-color: #1e293b;
  }

  .view-btn:hover:not(:disabled) {
    background: #334155;
  }

  .approve-btn {
    background: #10b981;
    color: white;
    border-color: #10b981;
  }

  .approve-btn:hover:not(:disabled) {
    background: #059669;
  }

  .reject-btn {
    background: #ef4444;
    color: white;
    border-color: #ef4444;
  }

  .reject-btn:hover:not(:disabled) {
    background: #dc2626;
  }

  .loading-state {
    text-align: center;
    padding: 4rem;
    color: #64748b;
  }

  .edit-btn:hover:not(:disabled) {
    background: #005c2e;
    border-color: #005c2e;
  }

  .empty-state {
    text-align: center;
    padding: 4rem 2rem;
    color: #64748b;
  }

  .empty-icon {
    display: flex;
    justify-content: center;
    margin-bottom: 1rem;
  }

  .empty-state h3 {
    font-size: 1.5rem;
    margin-bottom: 0.5rem;
  }

  @media (max-width: 768px) {
    .caseload-container {
      padding: 1rem;
    }

    .filters-section {
      flex-direction: column;
      gap: 1rem;
    }

    .claims-grid {
      grid-template-columns: 1fr;
      gap: 1rem;
    }

    .claim-card {
      padding: 1rem;
    }

    .claim-footer {
      flex-direction: column;
      gap: 1rem;
      align-items: stretch;
    }

    .claim-actions {
      justify-content: center;
    }
  }
</style>
