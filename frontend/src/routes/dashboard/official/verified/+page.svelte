<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { browser } from '$app/environment';
  import { CheckCircle, MapPin, Calendar, User, FileText, Search, Filter } from 'lucide-svelte';
  import Navbar from '$lib/components/Navbar.svelte';

  const API = 'http://localhost:5000';

  let verifiedClaims: any[] = [];
  let isLoading = true;
  let searchQuery = '';
  let filterStatus = 'all';

  function authHeaders() {
    return { 'Authorization': `Bearer ${localStorage.getItem('token')}` };
  }

  async function fetchVerifiedClaims() {
    isLoading = true;
    try {
      const res = await fetch(`${API}/api/parcels?status=verified`, { headers: authHeaders() });
      if (res.ok) {
        const data = await res.json();
        verifiedClaims = data;
      }
    } catch (err) {
      console.error('Error fetching verified claims:', err);
    } finally {
      isLoading = false;
    }
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

    fetchVerifiedClaims();
  });

  function formatDate(dateString: string): string {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  }

  function getFilteredClaims() {
    let filtered = verifiedClaims;
    
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(claim => 
        claim.id?.toLowerCase().includes(query) ||
        claim.location?.toLowerCase().includes(query) ||
        claim.owner_name?.toLowerCase().includes(query)
      );
    }
    
    return filtered;
  }
</script>

<svelte:head>
  <title>Verified Claims - LandLock Official</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</svelte:head>

<div class="verified-page">
  <Navbar userType="official" activeLink="/dashboard/official/verified" userName="Official" showNotification={false} />

  <div class="page-content">
    <div class="page-header">
      <div class="header-left">
        <h1><CheckCircle class="w-6 h-6 inline" /> Verified Claims</h1>
        <p>View all verified land claims and registrations</p>
      </div>
      <div class="header-right">
        <div class="search-box">
          <Search class="w-5 h-5" />
          <input 
            type="text" 
            placeholder="Search claims..." 
            bind:value={searchQuery}
            class="search-input"
          />
        </div>
      </div>
    </div>

    <div class="stats-overview">
      <div class="stat-card">
        <div class="stat-icon" style="background: #007A3D;">
          <CheckCircle class="w-6 h-6" />
        </div>
        <div class="stat-content">
          <div class="stat-value">{verifiedClaims.length}</div>
          <div class="stat-label">Total Verified</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background: #003366;">
          <FileText class="w-6 h-6" />
        </div>
        <div class="stat-content">
          <div class="stat-value">{verifiedClaims.length}</div>
          <div class="stat-label">Certificates Issued</div>
        </div>
      </div>
    </div>

    {#if isLoading}
      <div class="loading-state">
        <div class="spinner"></div>
        <p>Loading verified claims...</p>
      </div>
    {:else}
      <div class="claims-list">
        {#if getFilteredClaims().length > 0}
          {#each getFilteredClaims() as claim (claim.id)}
            <div class="claim-card">
              <div class="claim-header">
                <div class="claim-id">
                  <FileText class="w-5 h-5" />
                  <span>Claim #{claim.id || 'N/A'}</span>
                </div>
                <span class="badge badge-success">Verified</span>
              </div>
              
              <div class="claim-details">
                <div class="detail-row">
                  <span class="detail-label">Owner:</span>
                  <span class="detail-value">
                    <User class="w-4 h-4 inline" />
                    {claim.owner_name || 'N/A'}
                  </span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">Location:</span>
                  <span class="detail-value">
                    <MapPin class="w-4 h-4 inline" />
                    {claim.location || 'N/A'}
                  </span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">Size:</span>
                  <span class="detail-value">{claim.size || 'N/A'}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">Verified Date:</span>
                  <span class="detail-value">
                    <Calendar class="w-4 h-4 inline" />
                    {formatDate(claim.verified_at || claim.created_at)}
                  </span>
                </div>
              </div>

              <div class="claim-actions">
                <button class="btn btn-secondary btn-sm">View Certificate</button>
                <button class="btn btn-secondary btn-sm">View Details</button>
              </div>
            </div>
          {/each}
        {:else}
          <div class="empty-state">
            <CheckCircle class="w-16 h-16" />
            <h3>No Verified Claims Found</h3>
            <p>{searchQuery ? 'No claims match your search criteria' : 'No claims have been verified yet'}</p>
          </div>
        {/if}
      </div>
    {/if}
  </div>
</div>

<style>
  /* Global resets handled in app.css */

  .verified-page {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  /* Page Content */
  .page-content {
    max-width: 1400px;
    margin: 0 auto;
    padding: 2rem;
    width: 100%;
    flex: 1;
  }

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
    flex-wrap: wrap;
    gap: 1rem;
  }

  .header-left h1 {
    font-size: 2rem;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .header-left p {
    color: #64748b;
    font-size: 1rem;
  }

  .header-right {
    display: flex;
    gap: 1rem;
  }

  .search-box {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 0.5rem 1rem;
    width: 300px;
  }

  .search-box svg {
    color: #64748b;
  }

  .search-input {
    border: none;
    outline: none;
    flex: 1;
    font-size: 0.9375rem;
    font-family: inherit;
  }

  /* Stats Overview */
  .stats-overview {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
  }

  .stat-card {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    border: 1px solid #e2e8f0;
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .stat-icon {
    width: 48px;
    height: 48px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
  }

  .stat-content {
    flex: 1;
  }

  .stat-value {
    font-size: 1.875rem;
    font-weight: 700;
    color: #0f172a;
    line-height: 1;
    margin-bottom: 0.25rem;
  }

  .stat-label {
    font-size: 0.875rem;
    color: #64748b;
    font-weight: 500;
  }

  /* Claims List */
  .claims-list {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
    gap: 1.5rem;
  }

  .claim-card {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    border: 1px solid #e2e8f0;
    transition: all 0.2s;
  }

  .claim-card:hover {
    border-color: #007A3D;
    box-shadow: 0 4px 12px rgba(0, 122, 61, 0.1);
  }

  .claim-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid #e2e8f0;
  }

  .claim-id {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: 600;
    color: #0f172a;
  }

  .claim-id svg {
    color: #007A3D;
  }

  .claim-details {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    margin-bottom: 1rem;
  }

  .detail-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .detail-label {
    font-size: 0.875rem;
    color: #64748b;
    font-weight: 500;
  }

  .detail-value {
    font-size: 0.9375rem;
    color: #0f172a;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 0.25rem;
  }

  .claim-actions {
    display: flex;
    gap: 0.5rem;
  }

  /* Badge */
  .badge {
    padding: 0.25rem 0.75rem;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    white-space: nowrap;
  }

  .badge-success {
    background: #dcfce7;
    color: #166534;
  }

  /* Buttons */
  .btn {
    padding: 0.5rem 1rem;
    border-radius: 8px;
    border: none;
    font-weight: 600;
    font-size: 0.875rem;
    cursor: pointer;
    transition: all 0.2s;
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    white-space: nowrap;
  }

  .btn-primary {
    background: #007A3D;
    color: white;
  }

  .btn-primary:hover {
    background: #005C2E;
  }

  .btn-secondary {
    background: white;
    color: #007A3D;
    border: 1px solid #e2e8f0;
  }

  .btn-secondary:hover {
    background: #f8fafc;
  }

  .btn-sm {
    padding: 0.375rem 0.75rem;
    font-size: 0.8125rem;
  }

  /* Loading State */
  .loading-state {
    text-align: center;
    padding: 4rem 2rem;
  }

  .spinner {
    width: 48px;
    height: 48px;
    border: 4px solid #e2e8f0;
    border-top-color: #007A3D;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto 1rem;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .loading-state p {
    color: #64748b;
  }

  /* Empty State */
  .empty-state {
    text-align: center;
    padding: 4rem 2rem;
    background: white;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
  }

  .empty-state svg {
    color: #cbd5e1;
    margin-bottom: 1rem;
  }

  .empty-state h3 {
    font-size: 1.25rem;
    font-weight: 600;
    color: #0f172a;
    margin-bottom: 0.5rem;
  }

  .empty-state p {
    color: #64748b;
  }

  /* Responsive */
  @media (max-width: 768px) {
    .page-content {
      padding: 1rem;
    }

    .page-header {
      flex-direction: column;
      align-items: flex-start;
    }

    .search-box {
      width: 100%;
    }

    .claims-list {
      grid-template-columns: 1fr;
    }

    .stats-overview {
      grid-template-columns: 1fr;
    }
  }
</style>
