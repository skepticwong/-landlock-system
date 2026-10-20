<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { browser } from '$app/environment';
  import Navbar from '$lib/components/Navbar.svelte';
  import { ArrowLeft, History, Clock, Edit, Check, AlertTriangle } from 'lucide-svelte';
  import { page } from '$app/stores';

  const API = 'http://localhost:5000';
  let plot = null;
  let editHistory = [];
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

  async function fetchPlotAndHistory() {
    isLoading = true;
    try {
      const plotId = $page.params.id;
      
      // Fetch plot details
      const plotRes = await fetch(`${API}/api/plots/${plotId}`, { headers: authHeaders() });
      if (plotRes.ok) {
        plot = await plotRes.json();
        
        // Check if user owns this plot
        if (plot.user_id !== currentUser.id) {
          goto('/my-plots');
          return;
        }
      } else {
        goto('/my-plots');
        return;
      }

      // Fetch edit history
      const historyRes = await fetch(`${API}/api/plots/${plotId}/history`, { headers: authHeaders() });
      if (historyRes.ok) {
        editHistory = await historyRes.json();
      }
    } catch (err) {
      console.error('Error fetching plot history:', err);
    } finally {
      isLoading = false;
    }
  }

  function goBack() {
    goto('/my-plots');
  }

  function formatDate(isoString: string): string {
    if (!isoString) return 'N/A';
    return new Date(isoString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  function getChangeIcon(changeType: string): any {
    switch (changeType) {
      case 'created': return Check;
      case 'edited': return Edit;
      case 'status_change': return AlertTriangle;
      default: return Clock;
    }
  }

  function getChangeColor(changeType: string): string {
    switch (changeType) {
      case 'created': return '#10b981';
      case 'edited': return '#3b82f6';
      case 'status_change': return '#f59e0b';
      default: return '#6b7280';
    }
  }

  function formatChanges(changes: any): string {
    if (!changes) return 'No details available';
    
    const changeDescriptions = [];
    
    if (changes.plot_name) {
      changeDescriptions.push(`Name changed to "${changes.plot_name}"`);
    }
    if (changes.district) {
      changeDescriptions.push(`District changed to "${changes.district}"`);
    }
    if (changes.village) {
      changeDescriptions.push(`Village changed to "${changes.village}"`);
    }
    if (changes.status) {
      changeDescriptions.push(`Status changed to "${changes.status}"`);
    }
    if (changes.land_use) {
      changeDescriptions.push(`Land use changed to "${changes.land_use}"`);
    }
    if (changes.estimated_size) {
      changeDescriptions.push(`Size changed to "${changes.estimated_size}"`);
    }
    
    return changeDescriptions.length > 0 ? changeDescriptions.join(', ') : 'No details available';
  }

  onMount(async () => {
    if (!browser) return;

    if (!localStorage.getItem('token')) {
      goto('/login');
      return;
    }

    await fetchCurrentUser();
    await fetchPlotAndHistory();
  });
</script>

<svelte:head>
  <title>Plot History - LandLock</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</svelte:head>

<div class="history-page">
  <Navbar userType="citizen" activeLink="/my-plots" userName={currentUser?.full_name || 'User'} />

  <main class="main-content">
    <div class="page-header">
      <button class="back-btn" on:click={goBack}>
        <ArrowLeft class="w-5 h-5 inline" />
        Back to My Plots
      </button>
    </div>

    {#if isLoading}
      <div class="loading-state">
        <div class="spinner"></div>
        <p>Loading plot history...</p>
      </div>
    {:else}
      <div class="history-container">
        <div class="history-header">
          <div class="header-title">
            <h1><History class="w-6 h-6 inline" /> Plot History</h1>
            <p>MLW-{$page.params.id}</p>
          </div>
          {#if plot}
            <div class="plot-summary">
              <div class="summary-item">
                <span class="label">Current Name:</span>
                <span class="value">{plot.plot_name || 'Unnamed'}</span>
              </div>
              <div class="summary-item">
                <span class="label">Current Status:</span>
                <span class="value status-badge" style="background: {getStatusColor(plot.status)}20; color: {getStatusColor(plot.status)};">
                  {plot.status || 'Unknown'}
                </span>
              </div>
            </div>
          {/if}
        </div>

        <div class="history-timeline">
          {#if editHistory.length === 0}
            <div class="empty-state">
              <History class="w-16 h-16" />
              <h3>No History Available</h3>
              <p>This plot has no recorded changes yet.</p>
            </div>
          {:else}
            {#each editHistory as entry (entry.id)}
              <div class="timeline-item">
                <div class="timeline-dot" style="background: {getChangeColor(entry.change_type)};"></div>
                <div class="timeline-content">
                  <div class="timeline-header">
                    <div class="timeline-title">
                      <svelte:component this={getChangeIcon(entry.change_type)} class="w-4 h-4 inline" />
                      {getChangeTitle(entry.change_type)}
                    </div>
                    <div class="timeline-date">{formatDate(entry.created_at)}</div>
                  </div>
                  <div class="timeline-details">
                    {formatChanges(entry.changes)}
                  </div>
                  {#if entry.previous_status && entry.new_status}
                    <div class="status-change">
                      <span class="previous-status">{entry.previous_status}</span>
                      <span class="arrow">→</span>
                      <span class="new-status">{entry.new_status}</span>
                    </div>
                  {/if}
                </div>
              </div>
            {/each}
          {/if}
        </div>
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

  .history-page {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  .main-content {
    max-width: 900px;
    margin: 0 auto;
    padding: 2rem;
    width: 100%;
    flex: 1;
  }

  .page-header {
    margin-bottom: 2rem;
  }

  .back-btn {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    color: #64748b;
    font-weight: 500;
    font-size: 0.9375rem;
    cursor: pointer;
    transition: all 0.2s;
  }

  .back-btn:hover {
    background: #f8fafc;
    color: #0f172a;
  }

  .history-container {
    background: white;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
    overflow: hidden;
  }

  .history-header {
    padding: 2rem;
    border-bottom: 1px solid #e2e8f0;
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    flex-wrap: wrap;
    gap: 1rem;
  }

  .header-title h1 {
    font-size: 1.5rem;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 0.25rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .header-title p {
    color: #64748b;
    font-size: 0.9375rem;
  }

  .plot-summary {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .summary-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.875rem;
  }

  .summary-item .label {
    color: #64748b;
    font-weight: 500;
  }

  .summary-item .value {
    color: #0f172a;
    font-weight: 600;
  }

  .status-badge {
    padding: 0.25rem 0.75rem;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
  }

  .history-timeline {
    padding: 2rem;
  }

  .timeline-item {
    display: flex;
    gap: 1rem;
    padding-bottom: 2rem;
    position: relative;
  }

  .timeline-item:not(:last-child)::after {
    content: '';
    position: absolute;
    left: 6px;
    top: 24px;
    bottom: 0;
    width: 2px;
    background: #e2e8f0;
  }

  .timeline-dot {
    width: 14px;
    height: 14px;
    border-radius: 50%;
    flex-shrink: 0;
    margin-top: 4px;
    border: 2px solid white;
    box-shadow: 0 0 0 2px currentColor;
  }

  .timeline-content {
    flex: 1;
  }

  .timeline-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 0.5rem;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .timeline-title {
    font-weight: 600;
    color: #0f172a;
    font-size: 1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .timeline-date {
    font-size: 0.8125rem;
    color: #64748b;
  }

  .timeline-details {
    font-size: 0.875rem;
    color: #475569;
    line-height: 1.6;
    margin-bottom: 0.5rem;
  }

  .status-change {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.8125rem;
    padding: 0.25rem 0.75rem;
    background: #f8fafc;
    border-radius: 6px;
  }

  .previous-status {
    color: #64748b;
    font-weight: 500;
  }

  .arrow {
    color: #94a3b8;
  }

  .new-status {
    color: #0f172a;
    font-weight: 600;
  }

  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 4rem 2rem;
    text-align: center;
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

  @media (max-width: 768px) {
    .main-content {
      padding: 1rem;
    }

    .history-header {
      flex-direction: column;
    }

    .timeline-header {
      flex-direction: column;
    }
  }
</style>

<script context="module">
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

  function getChangeTitle(changeType: string): string {
    switch (changeType) {
      case 'created': return 'Plot Created';
      case 'edited': return 'Plot Edited';
      case 'status_change': return 'Status Changed';
      default: return 'Change Recorded';
    }
  }
</script>
