<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { browser } from '$app/environment';

  // Comprehensive transaction data
  let myListings = [
    {
      id: 'MLW-LIL-8821',
      location: 'Chilomoni, Lilongwe',
      size: 2.4,
      type: 'sale',
      price: '₵500,000',
      status: 'active',
      views: 24,
      interested: 3,
      listedAt: '2024-01-15',
      publicUrl: 'landlock.mw/listings/MLW-LIL-8821',
      verificationCode: 'VC-2024-MLW-8821-001'
    },
    {
      id: 'MLW-LIL-8822',
      location: 'Area 25, Lilongwe',
      size: 1.8,
      type: 'lease',
      rate: '₵10,000/month',
      duration: '2 years',
      status: 'under_transfer',
      views: 18,
      interested: 1,
      listedAt: '2024-01-10',
      publicUrl: 'landlock.mw/listings/MLW-LIL-8822',
      verificationCode: 'VC-2024-MLW-8822-001'
    }
  ];

  let activeTransactions = [
    {
      id: 'TXN-001',
      parcelId: 'MLW-LIL-8822',
      parcelLocation: 'Area 25, Lilongwe',
      type: 'lease',
      status: 'awaiting_officer',
      buyer: 'Mary K.',
      seller: 'Grace M. Banda',
      rate: '₵10,000/month',
      duration: '2 years',
      startedAt: '2024-01-20',
      nextAction: 'Officer review in progress',
      officerName: 'Officer Banda',
      estimatedCompletion: '2-3 days'
    },
    {
      id: 'TXN-002',
      parcelId: 'MLW-LIL-8821',
      parcelLocation: 'Chilomoni, Lilongwe',
      type: 'sale',
      status: 'chat_active',
      buyer: 'James B.',
      seller: 'Grace M. Banda',
      price: '₵500,000',
      startedAt: '2024-01-22',
      nextAction: 'Begin official transfer',
      unreadMessages: 2
    }
  ];

  let completedTransactions = [
    {
      id: 'TXN-003',
      parcelId: 'MLW-LIL-8820',
      parcelLocation: 'Area 12, Lilongwe',
      type: 'sale',
      status: 'completed',
      buyer: 'John M.',
      seller: 'Grace M. Banda',
      price: '₵350,000',
      completedAt: '2023-12-15',
      certificateIssued: true,
      receiptUrl: 'landlock.mw/receipts/TXN-003'
    }
  ];

  let interestedBuyers = [
    {
      id: 'INTEREST-001',
      parcelId: 'MLW-LIL-8821',
      buyerName: 'James B.',
      buyerPhone: '+265 991 234 567',
      message: 'I am interested in this plot for farming. Can we schedule a visit?',
      requestedAt: '2024-01-22',
      status: 'pending_consent'
    },
    {
      id: 'INTEREST-002',
      parcelId: 'MLW-LIL-8821',
      buyerName: 'Mary K.',
      buyerPhone: '+265 882 345 678',
      message: 'Looking for land near this area. What are the terms?',
      requestedAt: '2024-01-21',
      status: 'contact_shared'
    }
  ];

  let isOnline = navigator.onLine;
  let activeTab = 'listings'; // 'listings', 'transactions', 'completed'
  let selectedListing = null;
  let selectedTransaction = null;
  let isCreatingListing = false;

  onMount(() => {
    if (!browser) return;
    
    // Check authentication
    if (!localStorage.getItem('token')) {
      goto('/login');
      return;
    }

    // Listen for online/offline changes
    window.addEventListener('online', () => isOnline = true);
    window.addEventListener('offline', () => isOnline = false);
  });

  function createNewListing() {
    goto('/sell-or-lease/new');
  }

  function viewPublicListing(listingId: string) {
    const url = `https://landlock.mw/listings/${listingId}`;
    window.open(url, '_blank');
  }

  function openTransactionChat(transactionId: string) {
    console.log('Open chat for transaction:', transactionId);
    // Navigate to chat workspace
  }

  function beginTransfer(transactionId: string) {
    console.log('Begin transfer for transaction:', transactionId);
    // Start official transfer process
  }

  function approveBuyerContact(interestId: string) {
    console.log('Approve buyer contact:', interestId);
    // Send SMS consent and share contact
  }

  function rejectBuyerInterest(interestId: string) {
    console.log('Reject buyer interest:', interestId);
    // Reject the interest request
  }

  function getStatusColor(status: string): string {
    switch (status) {
      case 'active': return '#16a34a';
      case 'under_transfer': return '#f59e0b';
      case 'awaiting_officer': return '#3b82f6';
      case 'chat_active': return '#8b5cf6';
      case 'completed': return '#10b981';
      case 'pending_consent': return '#f97316';
      case 'contact_shared': return '#06b6d4';
      default: return '#6b7280';
    }
  }

  function getStatusText(status: string): string {
    switch (status) {
      case 'active': return 'Active';
      case 'under_transfer': return 'Under Transfer';
      case 'awaiting_officer': return 'Officer Review';
      case 'chat_active': return 'Chat Active';
      case 'completed': return 'Completed';
      case 'pending_consent': return 'Awaiting Consent';
      case 'contact_shared': return 'Contact Shared';
      default: return status;
    }
  }

  function getTypeIcon(type: string): string {
    return type === 'sale' ? '💰' : '📄';
  }

  function getTypeText(type: string): string {
    return type === 'sale' ? 'Sale' : 'Lease';
  }

  function formatDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    });
  }

  function getTotalViews(): number {
    return myListings.reduce((sum, listing) => sum + listing.views, 0);
  }

  function getTotalInterested(): number {
    return myListings.reduce((sum, listing) => sum + listing.interested, 0);
  }

  function getActiveListingsCount(): number {
    return myListings.filter(l => l.status === 'active').length;
  }

  function getActiveTransactionsCount(): number {
    return activeTransactions.filter(t => t.status !== 'completed').length;
  }
</script>

<svelte:head>
  <title>Transactions - LandLock</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</svelte:head>

<div class="transactions-page">
  <!-- Navigation -->
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
        <a href="/dashboard" class="nav-link">
          <span>Dashboard</span>
        </a>
        <a href="/register-land" class="nav-link">
          <span>Register Land</span>
        </a>
        <a href="/sell-or-lease" class="nav-link active">
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
        <h1>Transactions & Marketplace</h1>
        <p class="subtitle">Manage your land listings, buyer interests, and secure transfers</p>
      </div>
      <div class="header-right">
        <button class="btn btn-primary" on:click={createNewListing}>
          <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
            <path d="M10 5v10m5-5H5"/>
          </svg>
          Create New Listing
        </button>
      </div>
    </div>

    <!-- Stats Overview -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="white">
            <path d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
          </svg>
        </div>
        <div class="stat-content">
          <div class="stat-value">{getActiveListingsCount()}</div>
          <div class="stat-label">Active Listings</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="white">
            <path d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>
          </svg>
        </div>
        <div class="stat-content">
          <div class="stat-value">{getActiveTransactionsCount()}</div>
          <div class="stat-label">Active Transactions</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="white">
            <path d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
            <path d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
          </svg>
        </div>
        <div class="stat-content">
          <div class="stat-value">{getTotalViews()}</div>
          <div class="stat-label">Total Views</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="white">
            <path d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/>
          </svg>
        </div>
        <div class="stat-content">
          <div class="stat-value">{getTotalInterested()}</div>
          <div class="stat-label">Interested Buyers</div>
        </div>
      </div>
    </div>

    <!-- Transaction Tabs -->
    <div class="transaction-tabs">
      <button 
        class="tab-btn" 
        class:active={activeTab === 'listings'}
        on:click={() => activeTab = 'listings'}
      >
        <span class="tab-icon">🏠</span>
        <span>My Listings</span>
        <span class="tab-count">{myListings.length}</span>
      </button>
      <button 
        class="tab-btn" 
        class:active={activeTab === 'transactions'}
        on:click={() => activeTab = 'transactions'}
      >
        <span class="tab-icon">🤝</span>
        <span>Active Deals</span>
        <span class="tab-count">{activeTransactions.length}</span>
      </button>
      <button 
        class="tab-btn" 
        class:active={activeTab === 'completed'}
        on:click={() => activeTab = 'completed'}
      >
        <span class="tab-icon">✅</span>
        <span>Completed</span>
        <span class="tab-count">{completedTransactions.length}</span>
      </button>
      <button 
        class="tab-btn" 
        class:active={activeTab === 'interests'}
        on:click={() => activeTab = 'interests'}
      >
        <span class="tab-icon">💬</span>
        <span>Buyer Interests</span>
        <span class="tab-count">{interestedBuyers.length}</span>
      </button>
    </div>

    <!-- Tab Content -->
    <div class="tab-content">
      <!-- My Listings Tab -->
      {#if activeTab === 'listings'}
        <div class="listings-container">
          {#if myListings.length > 0}
            <div class="listings-grid">
              {#each myListings as listing (listing.id)}
                <div class="listing-card">
                  <div class="listing-header">
                    <div class="listing-id">
                      {getTypeIcon(listing.type)}
                      <span>{listing.id}</span>
                    </div>
                    <div class="listing-status">
                      <div class="status-badge" style="background: {getStatusColor(listing.status)}20; color: {getStatusColor(listing.status)};">
                        {getStatusText(listing.status)}
                      </div>
                    </div>
                  </div>
                  
                  <div class="listing-details">
                    <div class="detail-row">
                      <span class="label">📍 Location:</span>
                      <span class="value">{listing.location}</span>
                    </div>
                    <div class="detail-row">
                      <span class="label">📏 Size:</span>
                      <span class="value">{listing.size} acres</span>
                    </div>
                    <div class="detail-row">
                      <span class="label">💰 Price:</span>
                      <span class="value price">{listing.price || listing.rate}</span>
                    </div>
                    {#if listing.duration}
                      <div class="detail-row">
                        <span class="label">⏰ Duration:</span>
                        <span class="value">{listing.duration}</span>
                      </div>
                    {/if}
                  </div>
                  
                  <div class="listing-stats">
                    <div class="stat-item">
                      <span class="stat-icon">👁️</span>
                      <span class="stat-value">{listing.views}</span>
                      <span class="stat-label">views</span>
                    </div>
                    <div class="stat-item">
                      <span class="stat-icon">❤️</span>
                      <span class="stat-value">{listing.interested}</span>
                      <span class="stat-label">interested</span>
                    </div>
                  </div>
                  
                  <div class="listing-actions">
                    <button class="btn btn-secondary btn-sm" on:click={() => viewPublicListing(listing.id)}>
                      <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
                        <path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/>
                        <path fill-rule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clip-rule="evenodd"/>
                      </svg>
                      View Public
                    </button>
                    <button class="btn btn-primary btn-sm" on:click={() => selectedListing = listing}>
                      Manage
                    </button>
                  </div>
                  
                  <div class="public-url">
                    <span class="url-label">Public URL:</span>
                    <code class="url-value">{listing.publicUrl}</code>
                  </div>
                </div>
              {/each}
            </div>
          {:else}
            <div class="empty-state">
              <div class="empty-icon">
                <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
                  <circle cx="32" cy="32" r="32" fill="#f0f4ff"/>
                  <path d="M32 20L42 30H36V40H28V30H22L32 20Z" fill="#667eea" opacity="0.5"/>
                </svg>
              </div>
              <h3>No Active Listings</h3>
              <p>List your verified land to start selling or leasing</p>
              <button class="btn btn-primary" on:click={createNewListing}>
                Create Your First Listing
              </button>
            </div>
          {/if}
        </div>
      {/if}

      <!-- Active Transactions Tab -->
      {#if activeTab === 'transactions'}
        <div class="transactions-container">
          {#if activeTransactions.length > 0}
            <div class="transactions-list">
              {#each activeTransactions as transaction (transaction.id)}
                <div class="transaction-card">
                  <div class="transaction-header">
                    <div class="transaction-parties">
                      <div class="party">
                        <span class="party-label">Seller:</span>
                        <span class="party-name">{transaction.seller}</span>
                      </div>
                      <div class="transfer-arrow">→</div>
                      <div class="party">
                        <span class="party-label">Buyer:</span>
                        <span class="party-name">{transaction.buyer}</span>
                      </div>
                    </div>
                    <div class="transaction-status">
                      <div class="status-badge" style="background: {getStatusColor(transaction.status)}20; color: {getStatusColor(transaction.status)};">
                        {getStatusText(transaction.status)}
                      </div>
                    </div>
                  </div>
                  
                  <div class="transaction-details">
                    <div class="detail-row">
                      <span class="label">📍 Parcel:</span>
                      <span class="value">{transaction.parcelId} - {transaction.parcelLocation}</span>
                    </div>
                    <div class="detail-row">
                      <span class="label">{getTypeIcon(transaction.type)} Type:</span>
                      <span class="value">{getTypeText(transaction.type)}</span>
                    </div>
                    <div class="detail-row">
                      <span class="label">💰 Price:</span>
                      <span class="value price">{transaction.price || transaction.rate}</span>
                    </div>
                    {#if transaction.duration}
                      <div class="detail-row">
                        <span class="label">⏰ Duration:</span>
                        <span class="value">{transaction.duration}</span>
                      </div>
                    {/if}
                    <div class="detail-row">
                      <span class="label">📅 Started:</span>
                      <span class="value">{formatDate(transaction.startedAt)}</span>
                    </div>
                  </div>
                  
                  <div class="transaction-progress">
                    <div class="progress-header">
                      <span class="next-action">{transaction.nextAction}</span>
                      {#if transaction.estimatedCompletion}
                        <span class="eta">ETA: {transaction.estimatedCompletion}</span>
                      {/if}
                    </div>
                    {#if transaction.officerName}
                      <div class="officer-info">
                        <span class="officer-name">🏛️ {transaction.officerName}</span>
                      </div>
                    {/if}
                  </div>
                  
                  <div class="transaction-actions">
                    {#if transaction.status === 'chat_active'}
                      <button class="btn btn-primary" on:click={() => openTransactionChat(transaction.id)}>
                        <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
                          <path fill-rule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clip-rule="evenodd"/>
                        </svg>
                        {transaction.unreadMessages ? `Chat (${transaction.unreadMessages})` : 'Open Chat'}
                      </button>
                      <button class="btn btn-secondary" on:click={() => beginTransfer(transaction.id)}>
                        <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
                          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-8.293l-3-3a1 1 0 00-1.414 1.414L10.586 9.5H7a1 1 0 100 2h3.586l-1.293 1.293a1 1 0 101.414 1.414l3-3a1 1 0 000-1.414z" clip-rule="evenodd"/>
                        </svg>
                        Begin Transfer
                      </button>
                    {:else if transaction.status === 'awaiting_officer'}
                      <div class="waiting-indicator">
                        <svg width="20" height="20" viewBox="0 0 20 20" fill="#f59e0b" class="animate-spin">
                          <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd"/>
                        </svg>
                        <span>Awaiting Officer Review</span>
                      </div>
                    {/if}
                  </div>
                </div>
              {/each}
            </div>
          {:else}
            <div class="empty-state">
              <div class="empty-icon">
                <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
                  <circle cx="32" cy="32" r="32" fill="#f0f4ff"/>
                  <path d="M32 20L42 30H36V40H28V30H22L32 20Z" fill="#667eea" opacity="0.5"/>
                </svg>
              </div>
              <h3>No Active Transactions</h3>
              <p>Once buyers contact you and you approve, active transactions will appear here</p>
            </div>
          {/if}
        </div>
      {/if}

      <!-- Completed Transactions Tab -->
      {#if activeTab === 'completed'}
        <div class="completed-container">
          {#if completedTransactions.length > 0}
            <div class="completed-list">
              {#each completedTransactions as transaction (transaction.id)}
                <div class="completed-card">
                  <div class="completed-header">
                    <div class="completion-badge">
                      <svg width="24" height="24" viewBox="0 0 24 24" fill="#16a34a">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
                      </svg>
                      <span>Transfer Complete</span>
                    </div>
                    <div class="completion-date">
                      {formatDate(transaction.completedAt)}
                    </div>
                  </div>
                  
                  <div class="completed-details">
                    <div class="detail-row">
                      <span class="label">📍 Parcel:</span>
                      <span class="value">{transaction.parcelId} - {transaction.parcelLocation}</span>
                    </div>
                    <div class="detail-row">
                      <span class="label">👤 Buyer:</span>
                      <span class="value">{transaction.buyer}</span>
                    </div>
                    <div class="detail-row">
                      <span class="label">👤 Seller:</span>
                      <span class="value">{transaction.seller}</span>
                    </div>
                    <div class="detail-row">
                      <span class="label">💰 Price:</span>
                      <span class="value price">{transaction.price}</span>
                    </div>
                  </div>
                  
                  <div class="completed-actions">
                    {#if transaction.certificateIssued}
                      <div class="certificate-info">
                        <span class="certificate-badge">✅ Certificate Issued</span>
                      </div>
                    {/if}
                    <button class="btn btn-secondary btn-sm" on:click={() => window.open(`https://${transaction.receiptUrl}`, '_blank')}>
                      <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M4 4a2 2 0 00-2 2v1h16V6a2 2 0 00-2-2H4z" clip-rule="evenodd"/>
                        <path fill-rule="evenodd" d="M18 9H2v5a2 2 0 002 2h12a2 2 0 002-2V9zM4 13a1 1 0 011-1h1a1 1 0 110 2H5a1 1 0 01-1-1zm5-1a1 1 0 100 2h1a1 1 0 100-2H9z" clip-rule="evenodd"/>
                      </svg>
                      View Receipt
                    </button>
                  </div>
                </div>
              {/each}
            </div>
          {:else}
            <div class="empty-state">
              <div class="empty-icon">
                <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
                  <circle cx="32" cy="32" r="32" fill="#f0f4ff"/>
                  <path d="M32 20L42 30H36V40H28V30H22L32 20Z" fill="#667eea" opacity="0.5"/>
                </svg>
              </div>
              <h3>No Completed Transactions</h3>
              <p>Completed land transfers will appear here</p>
            </div>
          {/if}
        </div>
      {/if}

      <!-- Buyer Interests Tab -->
      {#if activeTab === 'interests'}
        <div class="interests-container">
          {#if interestedBuyers.length > 0}
            <div class="interests-list">
              {#each interestedBuyers as interest (interest.id)}
                <div class="interest-card">
                  <div class="interest-header">
                    <div class="buyer-info">
                      <div class="buyer-avatar">
                        <span>{interest.buyerName.charAt(0)}</span>
                      </div>
                      <div class="buyer-details">
                        <div class="buyer-name">{interest.buyerName}</div>
                        <div class="buyer-phone">{interest.buyerPhone}</div>
                      </div>
                    </div>
                    <div class="interest-status">
                      <div class="status-badge" style="background: {getStatusColor(interest.status)}20; color: {getStatusColor(interest.status)};">
                        {getStatusText(interest.status)}
                      </div>
                    </div>
                  </div>
                  
                  <div class="interest-details">
                    <div class="detail-row">
                      <span class="label">📍 Parcel:</span>
                      <span class="value">{interest.parcelId}</span>
                    </div>
                    <div class="detail-row">
                      <span class="label">📅 Requested:</span>
                      <span class="value">{formatDate(interest.requestedAt)}</span>
                    </div>
                  </div>
                  
                  <div class="interest-message">
                    <div class="message-label">Message:</div>
                    <div class="message-content">{interest.message}</div>
                  </div>
                  
                  <div class="interest-actions">
                    {#if interest.status === 'pending_consent'}
                      <button class="btn btn-primary" on:click={() => approveBuyerContact(interest.id)}>
                        <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
                          <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/>
                        </svg>
                        Share Contact
                      </button>
                      <button class="btn btn-secondary" on:click={() => rejectBuyerInterest(interest.id)}>
                        <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
                          <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
                        </svg>
                        Reject
                      </button>
                    {:else if interest.status === 'contact_shared'}
                      <div class="contact-shared-info">
                        <span class="shared-badge">✅ Contact Shared</span>
                        <button class="btn btn-secondary btn-sm" on:click={() => openTransactionChat('TXN-002')}>
                          <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
                            <path fill-rule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clip-rule="evenodd"/>
                          </svg>
                          Open Chat
                        </button>
                      </div>
                    {/if}
                  </div>
                </div>
              {/each}
            </div>
          {:else}
            <div class="empty-state">
              <div class="empty-icon">
                <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
                  <circle cx="32" cy="32" r="32" fill="#f0f4ff"/>
                  <path d="M32 20L42 30H36V40H28V30H22L32 20Z" fill="#667eea" opacity="0.5"/>
                </svg>
              </div>
              <h3>No Buyer Interests</h3>
              <p>When buyers show interest in your listings, they'll appear here</p>
            </div>
          {/if}
        </div>
      {/if}
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

  .transactions-page {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  /* Navbar - Same as dashboard */
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
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
    width: 100%;
    flex: 1;
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

  /* Transaction Tabs */
  .transaction-tabs {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 2rem;
    background: white;
    padding: 0.5rem;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
  }

  .tab-btn {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.25rem;
    border-radius: 8px;
    border: none;
    background: transparent;
    color: #64748b;
    font-weight: 500;
    font-size: 0.9375rem;
    cursor: pointer;
    transition: all 0.2s;
    white-space: nowrap;
  }

  .tab-btn:hover {
    background: #f8fafc;
    color: #334155;
  }

  .tab-btn.active {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
  }

  .tab-icon {
    font-size: 1rem;
  }

  .tab-count {
    background: rgba(255, 255, 255, 0.2);
    padding: 0.125rem 0.5rem;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 600;
  }

  .tab-btn:not(.active) .tab-count {
    background: #e2e8f0;
    color: #64748b;
  }

  /* Tab Content */
  .tab-content {
    min-height: 400px;
  }

  /* Listings Grid */
  .listings-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
    gap: 1.5rem;
  }

  .listing-card {
    background: white;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
    overflow: hidden;
    transition: all 0.3s;
  }

  .listing-card:hover {
    border-color: #cbd5e1;
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
    transform: translateY(-2px);
  }

  .listing-header {
    padding: 1.5rem;
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    border-bottom: 1px solid #e2e8f0;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .listing-id {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 1.125rem;
    font-weight: 700;
    color: #0f172a;
  }

  .status-badge {
    padding: 0.25rem 0.75rem;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
  }

  .listing-details {
    padding: 1.5rem;
  }

  .detail-row {
    display: flex;
    justify-content: space-between;
    margin-bottom: 0.75rem;
  }

  .detail-row:last-child {
    margin-bottom: 0;
  }

  .label {
    color: #64748b;
    font-size: 0.875rem;
  }

  .value {
    font-weight: 500;
    color: #0f172a;
  }

  .value.price {
    font-weight: 700;
    color: #16a34a;
  }

  .listing-stats {
    padding: 1rem 1.5rem;
    background: #f8fafc;
    border-top: 1px solid #e2e8f0;
    display: flex;
    gap: 2rem;
  }

  .stat-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .stat-icon {
    font-size: 1rem;
  }

  .stat-value {
    font-weight: 600;
    color: #0f172a;
  }

  .stat-label {
    font-size: 0.75rem;
    color: #64748b;
  }

  .listing-actions {
    padding: 1rem 1.5rem;
    display: flex;
    gap: 1rem;
    border-top: 1px solid #e2e8f0;
  }

  .public-url {
    padding: 1rem 1.5rem;
    background: #f0f4ff;
    border-top: 1px solid #e2e8f0;
  }

  .url-label {
    font-size: 0.75rem;
    color: #64748b;
    margin-bottom: 0.25rem;
  }

  .url-value {
    font-family: 'Courier New', monospace;
    font-size: 0.875rem;
    color: #667eea;
  }

  /* Transaction Cards */
  .transactions-list,
  .completed-list,
  .interests-list {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .transaction-card,
  .completed-card,
  .interest-card {
    background: white;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
    overflow: hidden;
  }

  .transaction-header,
  .completed-header,
  .interest-header {
    padding: 1.5rem;
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    border-bottom: 1px solid #e2e8f0;
  }

  .transaction-parties {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .party {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .party-label {
    font-size: 0.75rem;
    color: #64748b;
    font-weight: 500;
  }

  .party-name {
    font-weight: 600;
    color: #0f172a;
  }

  .transfer-arrow {
    font-size: 1.25rem;
    color: #667eea;
    font-weight: 700;
  }

  .completion-badge {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: #16a34a;
    font-weight: 600;
  }

  .completion-date {
    font-size: 0.875rem;
    color: #64748b;
  }

  .buyer-info {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .buyer-avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
  }

  .buyer-details {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .buyer-name {
    font-weight: 600;
    color: #0f172a;
  }

  .buyer-phone {
    font-size: 0.875rem;
    color: #64748b;
  }

  .transaction-details,
  .completed-details,
  .interest-details {
    padding: 1.5rem;
  }

  .transaction-progress {
    padding: 1rem 1.5rem;
    background: #f8fafc;
    border-top: 1px solid #e2e8f0;
  }

  .progress-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
  }

  .next-action {
    font-weight: 600;
    color: #f59e0b;
  }

  .eta {
    font-size: 0.875rem;
    color: #64748b;
  }

  .officer-info {
    margin-top: 0.5rem;
  }

  .officer-name {
    font-size: 0.875rem;
    color: #3b82f6;
  }

  .transaction-actions,
  .completed-actions,
  .interest-actions {
    padding: 1rem 1.5rem;
    display: flex;
    gap: 1rem;
    border-top: 1px solid #e2e8f0;
  }

  .waiting-indicator {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: #f59e0b;
    font-weight: 500;
  }

  .certificate-info {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .certificate-badge {
    color: #16a34a;
    font-weight: 600;
  }

  .interest-message {
    padding: 1rem 1.5rem;
    background: #f8fafc;
    border-top: 1px solid #e2e8f0;
  }

  .message-label {
    font-size: 0.75rem;
    color: #64748b;
    font-weight: 500;
    margin-bottom: 0.5rem;
  }

  .message-content {
    color: #0f172a;
    line-height: 1.5;
  }

  .contact-shared-info {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .shared-badge {
    color: #16a34a;
    font-weight: 600;
  }

  /* Empty State */
  .empty-state {
    text-align: center;
    padding: 4rem 2rem;
    background: white;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
  }

  .empty-icon {
    margin-bottom: 2rem;
  }

  .empty-state h3 {
    font-size: 1.25rem;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 1rem;
  }

  .empty-state p {
    color: #64748b;
    margin-bottom: 2rem;
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

  .btn-primary:hover:not(:disabled) {
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

  .btn-sm {
    padding: 0.5rem 1rem;
    font-size: 0.875rem;
  }

  /* Animations */
  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }

  .animate-spin {
    animation: spin 1s linear infinite;
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

    .stats-grid {
      grid-template-columns: repeat(2, 1fr);
      gap: 1rem;
    }

    .page-header {
      flex-direction: column;
      align-items: flex-start;
    }

    .transaction-tabs {
      flex-wrap: wrap;
    }

    .tab-btn {
      flex: 1;
      min-width: 0;
      justify-content: center;
    }

    .listings-grid {
      grid-template-columns: 1fr;
    }

    .transaction-parties {
      flex-direction: column;
      align-items: flex-start;
      gap: 0.5rem;
    }

    .transfer-arrow {
      transform: rotate(90deg);
    }

    .transaction-actions,
    .completed-actions,
    .interest-actions {
      flex-direction: column;
    }

    .listing-actions {
      flex-direction: column;
    }
  }

  @media (max-width: 480px) {
    .stats-grid {
      grid-template-columns: 1fr;
    }
  }
</style>
                        <span>👤 {transaction.counterparty}</span>
                      </div>
                      <div class="transaction-details">
                        <span class="price">{transaction.price || transaction.rate}</span>
                        <span class="next-action">{transaction.nextAction}</span>
                      </div>
                    </div>
                    <div class="list-item-actions">
                      <button class="btn btn-primary btn-sm">
                        {transaction.nextAction.includes('signature') ? 'Sign Now' : 'View Details'}
                      </button>
                    </div>
                  </div>
                {/each}
              </div>
            {:else}
              <div class="empty-state">
                <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
                  <circle cx="32" cy="32" r="32" fill="#f0f4ff"/>
                  <path d="M32 20L42 30H36V40H28V30H22L32 20Z" fill="#667eea" opacity="0.5"/>
                </svg>
                <h3>No Active Transactions</h3>
                <p>Complete transactions will appear here</p>
              </div>
            {/if}
          </div>
        </div>
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
              <a href="/sell-or-lease/new" class="action-item">
                <div class="action-icon" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                  <svg width="20" height="20" viewBox="0 0 20 20" fill="white">
                    <path d="M10 5v10m5-5H5"/>
                  </svg>
                </div>
                <div class="action-content">
                  <div class="action-title">Create Listing</div>
                  <div class="action-desc">Sell or lease land</div>
                </div>
                <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor" opacity="0.3">
                  <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd"/>
                </svg>
              </a>

              <a href="/register-land" class="action-item">
                <div class="action-icon" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
                  <svg width="20" height="20" viewBox="0 0 20 20" fill="white">
                    <path d="M4 4a2 2 0 00-2 2v1h16V6a2 2 0 00-2-2H4z"/>
                    <path fill-rule="evenodd" d="M18 9H2v5a2 2 0 002 2h12a2 2 0 002-2V9zM4 13a1 1 0 011-1h1a1 1 0 110 2H5a1 1 0 01-1-1zm5-1a1 1 0 100 2h1a1 1 0 100-2H9z" clip-rule="evenodd"/>
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
                  <div class="timeline-title">Listing created</div>
                  <div class="timeline-time">2 hours ago</div>
                </div>
              </div>
              <div class="timeline-item">
                <div class="timeline-dot" style="background: #f56565;"></div>
                <div class="timeline-content">
                  <div class="timeline-title">Buyer interested</div>
                  <div class="timeline-time">1 day ago</div>
                </div>
              </div>
              <div class="timeline-item">
                <div class="timeline-dot" style="background: #48bb78;"></div>
                <div class="timeline-content">
                  <div class="timeline-title">Transaction completed</div>
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

  .transactions-page {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  /* Navbar - Same as dashboard */
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
    flex: 1;
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
    cursor: pointer;
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

  .listing-icon,
  .transaction-icon {
    width: 40px;
    height: 40px;
    border-radius: 8px;
    background: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.25rem;
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
    margin-bottom: 0.5rem;
  }

  .listing-stats {
    display: flex;
    gap: 1rem;
    font-size: 0.8125rem;
    color: #64748b;
  }

  .transaction-details {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    margin-top: 0.5rem;
  }

  .price {
    font-weight: 700;
    color: #0f172a;
    font-size: 1rem;
  }

  .next-action {
    font-size: 0.8125rem;
    color: #f59e0b;
    font-weight: 500;
  }

  .list-item-actions {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 0.5rem;
  }

  .status-badge {
    padding: 0.25rem 0.75rem;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    white-space: nowrap;
  }

  /* Empty State */
  .empty-state {
    text-align: center;
    padding: 3rem 2rem;
  }

  .empty-state h3 {
    font-size: 1.125rem;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 1rem;
  }

  .empty-state p {
    color: #64748b;
    margin-bottom: 1.5rem;
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

  .btn-primary:hover:not(:disabled) {
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

  .btn-sm {
    padding: 0.5rem 1rem;
    font-size: 0.875rem;
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
