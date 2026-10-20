<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { browser } from '$app/environment';

  // Mock data - can be easily swapped for real backend data
  let userData = {
    name: 'Grace',
    role: 'Landowner',
    lastSeen: 'Today at 10:15 AM',
    isOnline: true,
    pendingSync: 0
  };

  let summaryStats = {
    totalParcels: 2,
    pendingActions: 1,
    activeDeals: 1,
    verified: 2
  };

  let parcels = [
    {
      id: 'MLW-LIL-8821',
      location: 'Chilomoni, Lilongwe',
      size: 2.4,
      status: 'verified'
    },
    {
      id: 'MLW-LIL-8822',
      location: 'Area 25, Lilongwe',
      size: 1.8,
      status: 'verified'
    }
  ];

  let transactions = [
    {
      type: 'selling',
      counterparty: 'James B.',
      parcelId: 'MLW-LIL-8821',
      status: 'awaiting_signature',
      action: 'Sign Now'
    }
  ];

  let alerts = [
    {
      type: 'boundary_confirmation',
      parcelId: 'MLW-LIL-8821',
      message: 'Confirm boundary for Plot #MLW-LIL-8821',
      action: 'Verify'
    }
  ];

  onMount(() => {
    if (!browser) return;
    
    if (!localStorage.getItem('token')) {
      goto('/login');
      return;
    }
  });

  function handleQuickAction(action: string) {
    switch(action) {
      case 'register':
        goto('/register');
        break;
      case 'sell':
        goto('/sell-or-lease/new');
        break;
      case 'certificates':
        goto('/certificates');
        break;
      case 'support':
        goto('/support');
        break;
    }
  }

  function handleParcelAction(parcelId: string, action: string) {
    console.log(`Parcel ${parcelId}: ${action}`);
  }

  function handleTransactionAction(transactionId: string, action: string) {
    console.log(`Transaction ${transactionId}: ${action}`);
  }

  function handleAlertAction(alertId: string, action: string) {
    console.log(`Alert ${alertId}: ${action}`);
  }

  function syncNow() {
    console.log('Syncing data...');
    userData.pendingSync = 0;
  }
</script>

<svelte:head>
  <title>Citizen Dashboard - LandLock</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</svelte:head>

<div class="dashboard">
  <!-- Top Navigation -->
  <nav class="navbar">
    <div class="navbar-content">
      <div class="navbar-brand">
        <div class="logo">
          <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
            <rect width="32" height="32" rx="8" fill="url(#gradient)"/>
            <path d="M16 8L22 14H18V20H14V14H10L16 8Z" fill="white"/>
            <defs>
              <linearGradient id="gradient" x1="0" y1="0" x2="32" y2="32">
                <stop stop-color="#667eea"/>
                <stop offset="1" stop-color="#764ba2"/>
              </linearGradient>
            </defs>
          </svg>
        </div>
        <span class="brand-name">LandLock</span>
      </div>
      
      <div class="navbar-menu">
        <a href="/dashboard" class="nav-link active">
          <span>Dashboard</span>
        </a>
        <a href="/register-land" class="nav-link">
          <span>Register Land</span>
        </a>
        <a href="/sell-or-lease" class="nav-link">
          <span>Sell or Lease</span>
        </a>
        <a href="/certificates" class="nav-link">
          <span>Certificates</span>
        </a>
      </div>

      <div class="navbar-actions">
        <button class="icon-btn">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
            <path d="M10 2a6 6 0 00-6 6v3.586l-.707.707A1 1 0 004 14h12a1 1 0 00.707-1.707L16 11.586V8a6 6 0 00-6-6z"/>
            <path d="M10 18a3 3 0 01-3-3h6a3 3 0 01-3 3z"/>
          </svg>
        </button>
        <div class="user-menu">
          <div class="avatar">
            <span>G</span>
          </div>
        </div>
      </div>
    </div>
  </nav>

  <!-- Main Content -->
  <main class="main-content">
    <!-- Page Header -->
    <div class="page-header">
      <div class="header-left">
        <h1>Welcome back, {userData.name}! 👋</h1>
        <p class="subtitle">{userData.role} • Last seen: {userData.lastSeen}</p>
      </div>
      <div class="header-right">
        {#if userData.isOnline}
          <div class="status-badge success">
            <div class="status-dot"></div>
            <span>All synced</span>
          </div>
        {:else}
          <div class="status-badge warning">
            <div class="status-dot"></div>
            <span>{userData.pendingSync} pending</span>
          </div>
          <button class="btn btn-primary" on:click={syncNow}>Sync Now</button>
        {/if}
      </div>
    </div>

    <!-- Stats Grid -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="white">
            <path d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
          </svg>
        </div>
        <div class="stat-content">
          <div class="stat-value">{summaryStats.totalParcels}</div>
          <div class="stat-label">Total Parcels</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="white">
            <path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
        </div>
        <div class="stat-content">
          <div class="stat-value">{summaryStats.pendingActions}</div>
          <div class="stat-label">Pending Actions</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="white">
            <path d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>
          </svg>
        </div>
        <div class="stat-content">
          <div class="stat-value">{summaryStats.activeDeals}</div>
          <div class="stat-label">Active Deals</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="white">
            <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
        </div>
        <div class="stat-content">
          <div class="stat-value">{summaryStats.verified}</div>
          <div class="stat-label">Verified</div>
        </div>
      </div>
    </div>

    <!-- Content Grid -->
    <div class="content-grid">
      <!-- Main Column -->
      <div class="main-column">
        <!-- Your Parcels -->
        <div class="card">
          <div class="card-header">
            <h2>Your Parcels</h2>
            <button class="btn btn-secondary btn-sm" on:click={() => goto('/register-land')}>
              + Add New
            </button>
          </div>
          <div class="card-body">
            {#if parcels.length > 0}
              <div class="list">
                {#each parcels as parcel (parcel.id)}
                  <div class="list-item">
                    <div class="list-item-icon">
                      <svg width="40" height="40" viewBox="0 0 40 40">
                        <rect width="40" height="40" rx="8" fill="#f0f4ff"/>
                        <path d="M20 12L26 18H22V24H18V18H14L20 12Z" fill="#667eea"/>
                      </svg>
                    </div>
                    <div class="list-item-content">
                      <div class="list-item-title">{parcel.id}</div>
                      <div class="list-item-meta">
                        <span>📍 {parcel.location}</span>
                        <span>•</span>
                        <span>📏 {parcel.size} acres</span>
                      </div>
                    </div>
                    <span class="badge badge-success">Verified</span>
                  </div>
                {/each}
              </div>
            {:else}
              <div class="empty-state">
                <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
                  <circle cx="32" cy="32" r="32" fill="#f0f4ff"/>
                  <path d="M32 20L42 30H36V40H28V30H22L32 20Z" fill="#667eea" opacity="0.5"/>
                </svg>
                <p>No parcels registered yet</p>
                <button class="btn btn-primary" on:click={() => goto('/register-land')}>
                  Register Your First Parcel
                </button>
              </div>
            {/if}
          </div>
        </div>

        <!-- Active Transactions -->
        {#if transactions.length > 0}
          <div class="card">
            <div class="card-header">
              <h2>Active Transactions</h2>
            </div>
            <div class="card-body">
              <div class="list">
                {#each transactions as transaction (transaction.parcelId)}
                  <div class="list-item highlight">
                    <div class="list-item-icon">
                      <svg width="40" height="40" viewBox="0 0 40 40">
                        <rect width="40" height="40" rx="8" fill="#fff5f5"/>
                        <path d="M20 14V26M14 20H26" stroke="#f56565" stroke-width="2" stroke-linecap="round"/>
                      </svg>
                    </div>
                    <div class="list-item-content">
                      <div class="list-item-title">
                        {#if transaction.type === 'selling'}
                          Selling to {transaction.counterparty}
                        {:else}
                          Bought Plot #{transaction.parcelId}
                        {/if}
                      </div>
                      <div class="list-item-meta">
                        {#if transaction.status === 'awaiting_signature'}
                          ⏳ Awaiting your signature
                        {:else}
                          ✅ Certificate ready
                        {/if}
                      </div>
                    </div>
                    <button class="btn btn-primary btn-sm" on:click={() => handleTransactionAction(transaction.parcelId, transaction.action)}>
                      {transaction.action}
                    </button>
                  </div>
                {/each}
              </div>
            </div>
          </div>
        {/if}

        <!-- Alerts -->
        {#if alerts.length > 0}
          <div class="card card-warning">
            <div class="card-header">
              <h2>⚠️ Action Required</h2>
            </div>
            <div class="card-body">
              <div class="list">
                {#each alerts as alert (alert.parcelId)}
                  <div class="list-item">
                    <div class="list-item-content">
                      <div class="list-item-title">{alert.message}</div>
                    </div>
                    <button class="btn btn-warning btn-sm" on:click={() => handleAlertAction(alert.parcelId, alert.action)}>
                      {alert.action}
                    </button>
                  </div>
                {/each}
              </div>
            </div>
          </div>
        {/if}
      </div>

      <!-- Sidebar -->
      <aside class="sidebar">
        <!-- Quick Actions -->
        <div class="card">
          <div class="card-header">
            <h3>Quick Actions</h3>
          </div>
          <div class="card-body">
            <div class="action-list">
              <a href="/register-land" class="action-item">
                <div class="action-icon" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                  <svg width="20" height="20" viewBox="0 0 20 20" fill="white">
                    <path d="M10 5v10m5-5H5"/>
                  </svg>
                </div>
                <div class="action-content">
                  <div class="action-title">Register Land</div>
                  <div class="action-desc">Add new parcel</div>
                </div>
                <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor" opacity="0.3">
                  <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd"/>
                </svg>
              </a>

              <a href="/sell-or-lease" class="action-item">
                <div class="action-icon" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
                  <svg width="20" height="20" viewBox="0 0 20 20" fill="white">
                    <path d="M4 4a2 2 0 00-2 2v1h16V6a2 2 0 00-2-2H4z"/>
                    <path fill-rule="evenodd" d="M18 9H2v5a2 2 0 002 2h12a2 2 0 002-2V9zM4 13a1 1 0 011-1h1a1 1 0 110 2H5a1 1 0 01-1-1zm5-1a1 1 0 100 2h1a1 1 0 100-2H9z" clip-rule="evenodd"/>
                  </svg>
                </div>
                <div class="action-content">
                  <div class="action-title">Sell or Lease</div>
                  <div class="action-desc">View transactions</div>
                </div>
                <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor" opacity="0.3">
                  <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd"/>
                </svg>
              </a>

              <a href="/certificates" class="action-item">
                <div class="action-icon" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
                  <svg width="20" height="20" viewBox="0 0 20 20" fill="white">
                    <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clip-rule="evenodd"/>
                  </svg>
                </div>
                <div class="action-content">
                  <div class="action-title">My Certificates</div>
                  <div class="action-desc">View documents</div>
                </div>
                <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor" opacity="0.3">
                  <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd"/>
                </svg>
              </a>

              <a href="/support" class="action-item">
                <div class="action-icon" style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);">
                  <svg width="20" height="20" viewBox="0 0 20 20" fill="white">
                    <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd"/>
                  </svg>
                </div>
                <div class="action-content">
                  <div class="action-title">Get Support</div>
                  <div class="action-desc">Help & assistance</div>
                </div>
                <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor" opacity="0.3">
                  <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd"/>
                </svg>
              </a>
            </div>
          </div>
        </div>

        <!-- Recent Activity -->
        <div class="card">
          <div class="card-header">
            <h3>Recent Activity</h3>
          </div>
          <div class="card-body">
            <div class="timeline">
              <div class="timeline-item">
                <div class="timeline-dot" style="background: #667eea;"></div>
                <div class="timeline-content">
                  <div class="timeline-title">Parcel verified</div>
                  <div class="timeline-time">2 hours ago</div>
                </div>
              </div>
              <div class="timeline-item">
                <div class="timeline-dot" style="background: #f56565;"></div>
                <div class="timeline-content">
                  <div class="timeline-title">Transaction initiated</div>
                  <div class="timeline-time">1 day ago</div>
                </div>
              </div>
              <div class="timeline-item">
                <div class="timeline-dot" style="background: #48bb78;"></div>
                <div class="timeline-content">
                  <div class="timeline-title">Certificate issued</div>
                  <div class="timeline-time">3 days ago</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </aside>
    </div>
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

  .dashboard {
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

  .logo {
    display: flex;
    align-items: center;
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
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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

  .user-menu {
    display: flex;
    align-items: center;
  }

  .avatar {
    width: 40px;
    height: 40px;
    border-radius: 10px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
  }

  /* Page Header */
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

  .subtitle {
    color: #64748b;
    font-size: 0.9375rem;
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .status-badge {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    border-radius: 8px;
    font-size: 0.875rem;
    font-weight: 600;
  }

  .status-badge.success {
    background: #dcfce7;
    color: #166534;
  }

  .status-badge.warning {
    background: #fef3c7;
    color: #92400e;
  }

  .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: currentColor;
    animation: pulse 2s infinite;
  }

  @keyframes pulse {
    0%, 100% {
      opacity: 1;
    }
    50% {
      opacity: 0.5;
    }
  }

  /* Buttons */
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
    white-space: nowrap;
  }

  .btn-primary {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
  }

  .btn-primary:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  }

  .btn-secondary {
    background: white;
    color: #667eea;
    border: 1px solid #e2e8f0;
  }

  .btn-secondary:hover {
    background: #f8fafc;
  }

  .btn-warning {
    background: #fbbf24;
    color: #78350f;
  }

  .btn-warning:hover {
    background: #f59e0b;
  }

  .btn-sm {
    padding: 0.5rem 1rem;
    font-size: 0.875rem;
  }

  /* Stats Grid */
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
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
    transition: all 0.2s;
  }

  .stat-card:hover {
    border-color: #cbd5e1;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
    transform: translateY(-2px);
  }

  .stat-icon {
    width: 48px;
    height: 48px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .stat-content {
    flex: 1;
  }

  .stat-value {
    font-size: 2rem;
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

  /* Content Grid */
  .content-grid {
    display: grid;
    grid-template-columns: 1fr 380px;
    gap: 2rem;
  }

  .main-column {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  /* Card */
  .card {
    background: white;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
    overflow: hidden;
  }

  .card-warning {
    border-color: #fbbf24;
    background: linear-gradient(to bottom, #fffbeb 0%, white 100%);
  }

  .card-header {
    padding: 1.5rem;
    border-bottom: 1px solid #e2e8f0;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .card-header h2,
  .card-header h3 {
    font-size: 1.125rem;
    font-weight: 700;
    color: #0f172a;
  }

  .card-body {
    padding: 1.5rem;
  }

  /* List */
  .list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .list-item {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem;
    border-radius: 8px;
    background: #f8fafc;
    transition: all 0.2s;
  }

  .list-item:hover {
    background: #f1f5f9;
  }

  .list-item.highlight {
    background: #fef3f2;
    border: 1px solid #fecaca;
  }

  .list-item-icon {
    flex-shrink: 0;
  }

  .list-item-content {
    flex: 1;
    min-width: 0;
  }

  .list-item-title {
    font-weight: 600;
    color: #0f172a;
    margin-bottom: 0.25rem;
  }

  .list-item-meta {
    font-size: 0.875rem;
    color: #64748b;
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

  /* Empty State */
  .empty-state {
    text-align: center;
    padding: 3rem 2rem;
  }

  .empty-state svg {
    margin-bottom: 1rem;
  }

  .empty-state p {
    color: #64748b;
    margin-bottom: 1.5rem;
    font-size: 1rem;
  }

  /* Sidebar */
  .sidebar {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  /* Action List */
  .action-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .action-item {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem;
    border-radius: 8px;
    background: #f8fafc;
    text-decoration: none;
    transition: all 0.2s;
  }

  .action-item:hover {
    background: #f1f5f9;
    transform: translateX(4px);
  }

  .action-icon {
    width: 40px;
    height: 40px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .action-content {
    flex: 1;
  }

  .action-title {
    font-weight: 600;
    color: #0f172a;
    font-size: 0.9375rem;
  }

  .action-desc {
    font-size: 0.8125rem;
    color: #64748b;
  }

  /* Timeline */
  .timeline {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .timeline-item {
    display: flex;
    gap: 1rem;
  }

  .timeline-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    margin-top: 4px;
    flex-shrink: 0;
  }

  .timeline-content {
    flex: 1;
  }

  .timeline-title {
    font-weight: 600;
    color: #0f172a;
    font-size: 0.9375rem;
    margin-bottom: 0.125rem;
  }

  .timeline-time {
    font-size: 0.8125rem;
    color: #94a3b8;
  }

  /* Responsive */
  @media (max-width: 1024px) {
    .content-grid {
      grid-template-columns: 1fr;
    }

    .sidebar {
      order: -1;
    }
  }

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

    .stats-grid {
      grid-template-columns: repeat(2, 1fr);
      gap: 1rem;
    }

    .page-header {
      flex-direction: column;
      align-items: flex-start;
    }
  }

  @media (max-width: 480px) {
    .stats-grid {
      grid-template-columns: 1fr;
    }
  }
</style>