<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { browser } from '$app/environment';

  interface Claim {
    id: string;
    parcelId: string;
    claimant: string;
    village: string;
    status: 'pending' | 'verified' | 'disputed';
    submittedDate: string;
    priority: 'high' | 'medium' | 'low';
  }

  let isOnline = true;
  let claims: Claim[] = [
    {
      id: 'c1',
      parcelId: 'MLW-LIL-8821',
      claimant: 'Grace Banda',
      village: 'Chilomoni',
      status: 'pending',
      submittedDate: '2024-11-20',
      priority: 'high'
    },
    {
      id: 'c2',
      parcelId: 'MLW-TAK-5532',
      claimant: 'James Phiri',
      village: 'Mwase',
      status: 'pending',
      submittedDate: '2024-11-22',
      priority: 'medium'
    },
    {
      id: 'c3',
      parcelId: 'MLW-BT-4412',
      claimant: 'Village Headman Jere',
      village: 'Chemusa',
      status: 'disputed',
      submittedDate: '2024-11-18',
      priority: 'high'
    },
    {
      id: 'c4',
      parcelId: 'MLW-ZO-7789',
      claimant: 'Mary Kachere',
      village: 'Ndirande',
      status: 'pending',
      submittedDate: '2024-11-23',
      priority: 'low'
    }
  ];

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
        claim.village.toLowerCase().includes(searchQuery.toLowerCase());
      return matchesStatus && matchesSearch;
    });
  }

  function getStatusColor(status: string) {
    switch (status) {
      case 'pending': return '#f59e0b';
      case 'verified': return '#10b981';
      case 'disputed': return '#ef4444';
      default: return '#6b7280';
    }
  }

  function getPriorityColor(priority: string) {
    switch (priority) {
      case 'high': return '#ef4444';
      case 'medium': return '#f59e0b';
      case 'low': return '#10b981';
      default: return '#6b7280';
    }
  }

  function viewClaim(claimId: string) {
    // TODO: Navigate to claim details
    console.log('View claim:', claimId);
  }

  function editClaim(claimId: string) {
    // TODO: Navigate to edit claim
    console.log('Edit claim:', claimId);
  }

  onMount(() => {
    if (!browser) return;
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
  <!-- Professional Navigation -->
  <nav class="professional-nav">
    <div class="nav-brand">
      <span class="brand-text">Land Registry Official Portal</span>
    </div>
    <div class="nav-menu">
      <a href="/dashboard/official" class="nav-item">Dashboard</a>
      <a href="/dashboard/official/caseload" class="nav-item active">My Caseload</a>
      <a href="/register-plot" class="nav-item">Registration</a>
      <a href="/map" class="nav-item">Map View</a>
      <a href="/profile" class="nav-item">Account</a>
    </div>
  </nav>

  <div class="page-header">
    <div class="header-content">
      <h1>My Caseload</h1>
      <p>Manage and review land claim applications</p>
    </div>
    
    {#if !isOnline}
      <div class="offline-indicator">
        📱 Offline Mode - Limited functionality
      </div>
    {/if}
  </div>

  <div class="filters-section">
    <div class="search-bar">
      <input
        type="text"
        placeholder="Search by claimant, parcel ID, or village..."
        bind:value={searchQuery}
        class="search-input"
      />
    </div>
    
    <div class="filter-controls">
      <select bind:value={filterStatus} class="filter-select">
        <option value="all">All Status</option>
        <option value="pending">Pending</option>
        <option value="verified">Verified</option>
        <option value="disputed">Disputed</option>
      </select>
    </div>
  </div>

  <div class="claims-grid">
    {#each filteredClaims() as claim (claim.id)}
      <div class="claim-card" transition:fade={{ duration: 200 }}>
        <div class="claim-header">
          <div class="parcel-id">{claim.parcelId}</div>
          <div class="priority-badge" style="background-color: {getPriorityColor(claim.priority)}">
            {claim.priority.toUpperCase()}
          </div>
        </div>
        
        <div class="claim-content">
          <h3 class="claimant-name">{claim.claimant}</h3>
          <div class="claim-details">
            <div class="detail-item">
              <span class="detail-label">Village:</span>
              <span class="detail-value">{claim.village}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">Submitted:</span>
              <span class="detail-value">{new Date(claim.submittedDate).toLocaleDateString()}</span>
            </div>
          </div>
          
          <div class="claim-footer">
            <div class="status-badge" style="background-color: {getStatusColor(claim.status)}">
              {claim.status.charAt(0).toUpperCase() + claim.status.slice(1)}
            </div>
            
            <div class="claim-actions">
              <button 
                class="action-btn view-btn"
                on:click={() => viewClaim(claim.id)}
                disabled={!isOnline}
              >
                👁️ View
              </button>
              <button 
                class="action-btn edit-btn"
                on:click={() => editClaim(claim.id)}
                disabled={!isOnline}
              >
                ✏️ Edit
              </button>
            </div>
          </div>
        </div>
      </div>
    {/each}
  </div>

  {#if filteredClaims().length === 0}
    <div class="empty-state">
      <div class="empty-icon">📋</div>
      <h3>No claims found</h3>
      <p>Try adjusting your search or filters</p>
    </div>
  {/if}
</div>

<style>
  .caseload-container {
    padding: 2rem;
    max-width: 1200px;
    margin: 0 auto;
  }

  .page-header {
    margin-bottom: 2rem;
  }

  .header-content {
    margin-bottom: 1rem;
  }

  .back-link {
    color: #0d9488;
    cursor: pointer;
    font-weight: 600;
    margin-bottom: 1rem;
    transition: color 0.2s;
  }

  .back-link:hover {
    color: #0b7a71;
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
    border-color: #0d9488;
    box-shadow: 0 0 0 3px rgba(13,148,136,0.15);
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
    border-color: #0d9488;
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
    border-color: #0d9488;
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

  .action-btn {
    padding: 0.5rem 0.75rem;
    border: none;
    border-radius: 6px;
    font-size: 0.875rem;
    cursor: pointer;
    transition: all 0.2s;
    font-weight: 500;
  }

  .action-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .view-btn {
    background: #f1f5f9;
    color: #475569;
  }

  .view-btn:hover:not(:disabled) {
    background: #e2e8f0;
  }

  .edit-btn {
    background: #f0fdf4;
    color: #166534;
  }

  .edit-btn:hover:not(:disabled) {
    background: #dcfce7;
  }

  .empty-state {
    text-align: center;
    padding: 4rem 2rem;
    color: #64748b;
  }

  /* Professional Navigation */
  .professional-nav {
    background: #ffffff;
    border-bottom: 1px solid #e5e7eb;
    padding: 0 2rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 64px;
    margin-bottom: 2rem;
  }

  .nav-brand {
    display: flex;
    align-items: center;
  }

  .brand-text {
    font-size: 1.25rem;
    font-weight: 600;
    color: #111827;
  }

  .nav-menu {
    display: flex;
    gap: 0.5rem;
  }

  .nav-item {
    padding: 0.5rem 1rem;
    border-radius: 4px;
    text-decoration: none;
    font-weight: 500;
    color: #6b7280;
    transition: all 0.2s;
  }

  .nav-item:hover {
    background: #f3f4f6;
    color: #111827;
  }

  .nav-item.active {
    background: #2563eb;
    color: white;
  }

  .empty-icon {
    font-size: 4rem;
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
