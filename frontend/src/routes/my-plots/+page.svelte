<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { browser } from '$app/environment';
  import Navbar from '$lib/components/Navbar.svelte';
  import { MapPin, Edit, History, Plus, AlertTriangle, Store } from 'lucide-svelte';

  const API = 'http://localhost:5000';
  let plots: any[] = [];
  let isLoading = true;
  let currentUser = null;

  function authHeaders() {
    return { 'Authorization': `Bearer ${localStorage.getItem('token')}` };
  }

  async function fetchCurrentUser() {
    try {
      const res = await fetch(`${API}/api/user/me`, { headers: authHeaders() });
      if (res.ok) {
        currentUser = await res.json();
      }
    } catch (err) {
      console.error('Error fetching user:', err);
    }
  }

  async function fetchPlots() {
    isLoading = true;
    try {
      const res = await fetch(`${API}/api/plots`, { headers: authHeaders() });
      if (res.ok) {
        plots = await res.json();
      }
    } catch (err) {
      console.error('Error fetching plots:', err);
    } finally {
      isLoading = false;
    }
  }

  function editPlot(plotId: string) {
    goto(`/my-plots/${plotId}/edit`);
  }

  function viewHistory(plotId: string) {
    goto(`/my-plots/${plotId}/history`);
  }

  function listPlot(plot: any) {
    const pTitle = encodeURIComponent(plot.plot_name || '');
    const pLoc = encodeURIComponent(plot.district || plot.village || '');
    let sizeDesc = '';
    if (plot.estimated_size) {
      sizeDesc = `${plot.estimated_size} ${getUnitLabel(plot.size_unit)}`;
    }
    const pSize = encodeURIComponent(sizeDesc);

    goto(`/sell-or-lease/new?plotId=${plot.id}&title=${pTitle}&location=${pLoc}&size=${pSize}`);
  }

  function getStatusColor(status: string): string {
    switch (status) {
      case 'verified': return '#10b981';
      case 'pending': return '#f59e0b';
      case 'disputed': return '#ef4444';
      case 'approve': return '#10b981';
      case 'reject': return '#ef4444';
      default: return '#6b7280';
    }
  }

  function formatDate(isoString: string): string {
    if (!isoString) return 'N/A';
    return new Date(isoString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  }

  function getUnitLabel(unit: string): string {
    switch (unit) {
      case 'meters': return 'm';
      case 'sqmeters': return 'm²';
      case 'acres': return 'acres';
      case 'hectares': return 'ha';
      default: return '';
    }
  }

  onMount(async () => {
    if (!browser) return;

    if (!localStorage.getItem('token')) {
      goto('/login');
      return;
    }

    await fetchCurrentUser();
    await fetchPlots();
  });
</script>

<svelte:head>
  <title>My Plots - LandLock</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</svelte:head>

<div class="my-plots-page">
  <Navbar userType="citizen" activeLink="/my-plots" userName={currentUser?.full_name || 'User'} />

  <main class="main-content">
    <div class="page-header">
      <div class="header-left">
        <h1>My Plots</h1>
        <p>Manage your registered land parcels</p>
      </div>
      <div class="header-right">
        <button class="btn btn-primary" on:click={() => goto('/register-land')}>
          <Plus class="w-5 h-5 inline" />
          Register New Plot
        </button>
      </div>
    </div>

    {#if isLoading}
      <div class="loading-state">
        <div class="spinner"></div>
        <p>Loading your plots...</p>
      </div>
    {:else if plots.length === 0}
      <div class="empty-state">
        <MapPin class="w-16 h-16" />
        <h3>No plots registered yet</h3>
        <p>Register your first plot to get started</p>
        <button class="btn btn-primary" on:click={() => goto('/register-land')}>
          Register Your First Plot
        </button>
      </div>
    {:else}
      <div class="plots-grid">
        {#each plots as plot (plot.id)}
          <div class="plot-card">
            <div class="plot-header">
              <div class="plot-id">MLW-{plot.id}</div>
              <div class="plot-status" style="background: {getStatusColor(plot.status)}20; color: {getStatusColor(plot.status)};">
                {plot.status || 'Unknown'}
              </div>
            </div>
            
            <div class="plot-body">
              <div class="plot-name">{plot.plot_name || 'Unnamed Plot'}</div>
              
              <div class="plot-details">
                <div class="detail-row">
                  <span class="label">Location:</span>
                  <span class="value">{plot.district || plot.village || 'N/A'}</span>
                </div>
                <div class="detail-row">
                  <span class="label">Registered:</span>
                  <span class="value">{formatDate(plot.created_at)}</span>
                </div>
                <div class="detail-row">
                  <span class="label">Last Updated:</span>
                  <span class="value">{formatDate(plot.updated_at)}</span>
                </div>
                {#if plot.estimated_size}
                  <div class="detail-row">
                    <span class="label">Size:</span>
                    <span class="value">{plot.estimated_size} {getUnitLabel(plot.size_unit)}</span>
                  </div>
                {/if}
              </div>

              {#if plot.status === 'pending'}
                <div class="pending-notice">
                  <AlertTriangle class="w-4 h-4 inline" />
                  <span>Awaiting official approval</span>
                </div>
              {/if}
            </div>

            <div class="plot-actions">
              {#if plot.status === 'verified' || plot.status === 'approve'}
                <button class="btn btn-primary" style="flex: 1.5; background: #3b82f6;" on:click={() => listPlot(plot)}>
                  <Store class="w-4 h-4 inline" />
                  Sell/Lease
                </button>
              {/if}
              <button class="btn btn-secondary" on:click={() => editPlot(plot.id)}>
                <Edit class="w-4 h-4 inline" />
                Edit
              </button>
              <button class="btn btn-secondary" on:click={() => viewHistory(plot.id)}>
                <History class="w-4 h-4 inline" />
                History
              </button>
            </div>
          </div>
        {/each}
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

  .my-plots-page {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  .main-content {
    max-width: 1200px;
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
    font-size: 1.875rem;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 0.25rem;
  }

  .header-left p {
    color: #64748b;
    font-size: 0.9375rem;
  }

  .header-right {
    display: flex;
    gap: 1rem;
  }

  .btn {
    padding: 0.625rem 1.25rem;
    border-radius: 8px;
    border: none;
    font-weight: 600;
    font-size: 0.9375rem;
    cursor: pointer;
    transition: all 0.2s;
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
  }

  .btn-primary {
    background: #007A3D;
    color: white;
  }

  .btn-primary:hover {
    background: #005C2E;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0, 122, 61, 0.25);
  }

  .btn-secondary {
    background: white;
    color: #007A3D;
    border: 1px solid #e2e8f0;
  }

  .btn-secondary:hover {
    background: #f8fafc;
    border-color: #cbd5e1;
  }

  .loading-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 4rem 2rem;
  }

  .spinner {
    width: 48px;
    height: 48px;
    border: 4px solid #e2e8f0;
    border-top-color: #007A3D;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-bottom: 1rem;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .loading-state p {
    color: #64748b;
  }

  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
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
    margin-bottom: 1.5rem;
  }

  .plots-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(420px, 1fr));
    gap: 1.5rem;
  }

  .plot-card {
    background: white;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
    overflow: hidden;
    transition: all 0.2s;
  }

  .plot-card:hover {
    border-color: #cbd5e1;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
    transform: translateY(-2px);
  }

  .plot-header {
    padding: 1rem 1.5rem;
    border-bottom: 1px solid #e2e8f0;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .plot-id {
    font-weight: 600;
    color: #0f172a;
    font-size: 0.9375rem;
  }

  .plot-status {
    padding: 0.25rem 0.75rem;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
  }

  .plot-body {
    padding: 1.5rem;
  }

  .plot-name {
    font-size: 1.125rem;
    font-weight: 600;
    color: #0f172a;
    margin-bottom: 1rem;
  }

  .plot-details {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    margin-bottom: 1rem;
  }

  .detail-row {
    display: flex;
    justify-content: space-between;
    font-size: 0.875rem;
  }

  .detail-row .label {
    color: #64748b;
  }

  .detail-row .value {
    color: #0f172a;
    font-weight: 500;
  }

  .pending-notice {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem;
    background: #fef3c7;
    border-radius: 8px;
    color: #92400e;
    font-size: 0.875rem;
    margin-top: 1rem;
  }

  .plot-actions {
    padding: 1rem 1.5rem;
    border-top: 1px solid #e2e8f0;
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem;
  }

  .plot-actions .btn {
    flex: 1;
    justify-content: center;
  }

  @media (max-width: 768px) {
    .main-content {
      padding: 1rem;
    }

    .page-header {
      flex-direction: column;
      align-items: flex-start;
    }

    .plots-grid {
      grid-template-columns: 1fr;
    }

    .plot-actions {
      flex-direction: column;
    }
  }
</style>
