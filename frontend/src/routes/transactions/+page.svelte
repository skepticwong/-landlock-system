<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { browser } from '$app/environment';
  import { MessageSquare, DollarSign, FileText, MapPin, Ruler, Check, Handshake, Home, Clock, User, Calendar as CalendarIcon, Trash2, Eye, Phone, Mail } from 'lucide-svelte';
  import { fetchTransactions, fetchMyListings, deleteListing, listingImageUrl, fetchBuyerInterests, approveBuyerInterest, rejectBuyerInterest, fetchMyInterests } from '$lib/api.js';
  import Navbar from '$lib/components/Navbar.svelte';

  // Data from database
  let myListings: any[] = [];
  let activeTransactions: any[] = [];
  let completedTransactions: any[] = [];
  let interestedBuyers: any[] = [];
  let myInterests: any[] = [];
  let isLoading = true;
  let error: string | null = null;

  let activeTab = 'listings';
  let currentUser: any = null;
  let removingId: number | null = null;

  async function fetchCurrentUser() {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:5000/api/user/me', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) currentUser = await response.json();
    } catch (e) { /* silent */ }
  }

  async function loadData() {
    isLoading = true;
    error = null;
    try {
      const [listings, transactions, interests, myInt] = await Promise.all([
        fetchMyListings(),
        fetchTransactions(),
        fetchBuyerInterests(),
        fetchMyInterests()
      ]);

      // Only show listings the citizen explicitly posted for sale/lease
      myListings = listings;

      activeTransactions = transactions
        .filter((tx: any) => tx.status !== 'completed' && tx.status !== 'cancelled' && tx.status !== 'rejected')
        .map((tx: any) => ({
          id: `TXN-${tx.id}`,
          rawId: tx.id,
          parcelId: tx.plot_id ? `MLW-${tx.plot_id}` : 'Unknown',
          type: tx.transaction_type || 'sale',
          status: tx.status,
          buyer: tx.counterparty || tx.buyer_name || 'Unknown',
          price: tx.amount ? `MK ${Number(tx.amount).toLocaleString()}` : 'MK 0',
          startedAt: tx.created_at?.split('T')[0] || '',
          nextAction: getApprovalNextAction(tx),
          buyer_approval_status: tx.buyer_approval_status || 'pending',
          chief_approval_status: tx.chief_approval_status || 'pending',
          witness_approval_status: tx.witness_approval_status || 'pending',
          chief_name: tx.chief_name || '',
          witness_name: tx.witness_name || '',
          seller_name: tx.seller_name || '',
        }));

      completedTransactions = transactions
        .filter((tx: any) => tx.status === 'completed')
        .map((tx: any) => ({
          id: `TXN-${tx.id}`,
          parcelId: tx.plot_id ? `MLW-${tx.plot_id}` : 'Unknown',
          type: tx.transaction_type || 'sale',
          status: 'completed',
          buyer: tx.counterparty || 'Unknown',
          price: tx.amount ? `MK ${Number(tx.amount).toLocaleString()}` : 'MK 0',
          completedAt: tx.updated_at?.split('T')[0] || ''
        }));

      interestedBuyers = interests;
      myInterests = myInt;
    } catch (err: any) {
      console.error('Failed to fetch data:', err);
      error = err.message;
    } finally {
      isLoading = false;
    }
  }

  onMount(async () => {
    if (!browser) return;
    if (!localStorage.getItem('token')) { goto('/login'); return; }
    fetchCurrentUser();
    await loadData();
  });

  async function handleRemoveListing(id: number) {
    if (!confirm('Remove this listing from the marketplace?')) return;
    removingId = id;
    try {
      await deleteListing(id);
      myListings = myListings.filter((l: any) => l.id !== id);
    } catch (e: any) {
      alert(e.message);
    } finally {
      removingId = null;
    }
  }

  async function approveBuyerContact(id: number) {
    try {
      await approveBuyerInterest(id);
      interestedBuyers = interestedBuyers.map((i: any) =>
        i.id === id ? { ...i, status: 'contact_shared' } : i
      );
    } catch (e: any) {
      alert(e.message);
    }
  }

  async function handleRejectBuyerInterest(id: number) {
    if (!confirm('Reject this buyer interest?')) return;
    try {
      await rejectBuyerInterest(id);
      interestedBuyers = interestedBuyers.filter((i: any) => i.id !== id);
    } catch (e: any) {
      alert(e.message);
    }
  }

  function createNewListing() { goto('/my-plots'); }
  function viewMarketplace()  { goto('/marketplace'); }

  function getStatusColor(status: string): string {
    switch (status) {
      case 'active':          return '#16a34a';
      case 'under_transfer':  return '#f59e0b';
      case 'awaiting_officer':return '#3b82f6';
      case 'chat_active':     return '#8b5cf6';
      case 'completed':       return '#10b981';
      case 'pending_consent': return '#f97316';
      case 'contact_shared':  return '#06b6d4';
      case 'cancelled':       return '#ef4444';
      default:                return '#6b7280';
    }
  }

  function getStatusText(status: string): string {
    switch (status) {
      case 'active':           return 'Active';
      case 'under_transfer':   return 'Under Transfer';
      case 'awaiting_officer': return 'Officer Review';
      case 'chat_active':      return 'Chat Active';
      case 'completed':        return 'Completed';
      case 'pending_consent':  return 'Awaiting Consent';
      case 'contact_shared':   return 'Contact Shared';
      case 'cancelled':        return 'Removed';
      default:                 return status;
    }
  }

  function formatPrice(val: any): string {
    if (!val) return '—';
    return `MK ${Number(val).toLocaleString()}`;
  }

  function getApprovalNextAction(tx: any): string {
    if (tx.status === 'pending_buyer') return 'Awaiting buyer confirmation';
    if (tx.status === 'pending_approvals') {
      const pending: string[] = [];
      if (tx.chief_approval_status === 'pending') pending.push('Chief');
      if (tx.witness_approval_status === 'pending') pending.push('Witness');
      if (pending.length > 0) return `Awaiting: ${pending.join(' & ')}`;
      return 'Processing...';
    }
    if (tx.status === 'pending') return 'Awaiting approval';
    return 'In progress';
  }

  function approvalPill(status: string): { label: string; color: string } {
    if (status === 'approved') return { label: 'Approved', color: '#16a34a' };
    if (status === 'rejected') return { label: 'Rejected', color: '#dc2626' };
    return { label: 'Pending', color: '#d97706' };
  }

  function formatDate(ds: string): string {
    if (!ds) return '—';
    return new Date(ds).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
  }

  function coverImage(listing: any): string | null {
    if (listing.images && listing.images.length > 0) {
      return listingImageUrl(listing.images[0].image_path);
    }
    return null;
  }

  function handleLogout() {
    if (browser) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      goto('/login');
    }
  }
</script>

<svelte:head>
  <title>Transactions - LandLock</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</svelte:head>

<div class="transactions-page">
  <Navbar userType="citizen" activeLink="/transactions" userName={currentUser?.full_name || 'User'} />

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
          Sell/Lease a Plot
        </button>
      </div>
    </div>      <!-- Stats Overview -->
    {#if isLoading}
      <div class="loading-state">
        <div class="loading-spinner"></div>
        <p>Loading your listings...</p>
      </div>
    {:else if error}
      <div class="error-state">
        <p class="error-message">Failed to load data: {error}</p>
        <button class="btn btn-secondary" on:click={loadData}>Retry</button>
      </div>
    {:else}
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon" style="background: #007A3D;">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="white">
              <path d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
            </svg>
          </div>
          <div class="stat-content">
            <div class="stat-value">{myListings.filter((l:any) => l.status === 'active').length}</div>
            <div class="stat-label">Active Listings</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon" style="background: #3b82f6;">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="white">
              <path d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"/>
            </svg>
          </div>
          <div class="stat-content">
            <div class="stat-value">{activeTransactions.length}</div>
            <div class="stat-label">Active Deals</div>
          </div>
        </div>
      </div>
    {/if}

    <!-- Transaction Tabs -->
    {#if !isLoading && !error}
      <div class="transaction-tabs">
        <button class="tab-btn" class:active={activeTab === 'listings'} on:click={() => activeTab = 'listings'}>
          <span class="tab-icon"><Home size={16} /></span>
          <span>My Listings</span>
          <span class="tab-count">{myListings.length}</span>
        </button>
        <button class="tab-btn" class:active={activeTab === 'transactions'} on:click={() => activeTab = 'transactions'}>
          <span class="tab-icon"><Handshake size={16} /></span>
          <span>Active Deals</span>
          <span class="tab-count">{activeTransactions.length}</span>
        </button>
        <button class="tab-btn" class:active={activeTab === 'completed'} on:click={() => activeTab = 'completed'}>
          <span class="tab-icon"><Check size={16} /></span>
          <span>Completed</span>
          <span class="tab-count">{completedTransactions.length}</span>
        </button>
        <button class="tab-btn" class:active={activeTab === 'interests'} on:click={() => activeTab = 'interests'}>
          <span class="tab-icon"><MessageSquare size={16} /></span>
          <span>Buyer Interests</span>
          <span class="tab-count">{interestedBuyers.length}</span>
        </button>
        <button class="tab-btn" class:active={activeTab === 'my-interests'} on:click={() => activeTab = 'my-interests'}>
          <span class="tab-icon"><Eye size={16} /></span>
          <span>My Interests</span>
          <span class="tab-count">{myInterests.length}</span>
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
                  <!-- Cover photo -->
                  {#if coverImage(listing)}
                    <div class="listing-cover">
                      <img src={coverImage(listing)} alt={listing.title} />
                      <div class="photo-count">
                        <svg width="12" height="12" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clip-rule="evenodd"/></svg>
                        {listing.images.length}
                      </div>
                    </div>
                  {:else}
                    <div class="listing-cover no-photo">
                      <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="M21 15l-5-5L5 21"/></svg>
                      <span>No photos</span>
                    </div>
                  {/if}

                  <div class="listing-body">
                    <div class="listing-top">
                      <span class="listing-type-badge {listing.listing_type}">{listing.listing_type === 'sale' ? '🏷️ For Sale' : '🔑 For Lease'}</span>
                      <div class="status-badge" style="background:{getStatusColor(listing.status)}20;color:{getStatusColor(listing.status)}">
                        {getStatusText(listing.status)}
                      </div>
                    </div>

                    <h3 class="listing-title">{listing.title}</h3>

                    {#if listing.location}
                      <div class="listing-meta">
                        <MapPin size={13} />
                        <span>{listing.location}</span>
                      </div>
                    {/if}
                    {#if listing.size_description}
                      <div class="listing-meta">
                        <Ruler size={13} />
                        <span>{listing.size_description}</span>
                      </div>
                    {/if}

                    <div class="listing-price">
                      {listing.asking_price ? formatPrice(listing.asking_price) : 'Price on request'}
                    </div>

                    <div class="listing-footer">
                      <span class="listing-date">Listed {formatDate(listing.created_at)}</span>
                      <div class="listing-actions">
                        <button class="btn-icon-action view" title="View in marketplace" on:click={viewMarketplace}>
                          <Eye size={15} />
                        </button>
                        <button
                          class="btn-icon-action remove"
                          title="Remove listing"
                          disabled={removingId === listing.id}
                          on:click={() => handleRemoveListing(listing.id)}
                        >
                          <Trash2 size={15} />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              {/each}
            </div>
          {:else}
            <div class="empty-state">
              <div class="empty-icon">
                <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
                  <circle cx="32" cy="32" r="32" fill="rgba(0,122,61,0.08)"/>
                  <path d="M32 20L42 30H36V40H28V30H22L32 20Z" fill="#007A3D" opacity="0.4"/>
                </svg>
              </div>
              <h3>No Listings Yet</h3>
              <p>Go to your registered plots to list them on the marketplace</p>
              <button class="btn btn-primary" on:click={createNewListing}>
                Go to My Plots
              </button>
            </div>
          {/if}
        </div>
      {/if}
/if}

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
                      <span class="label"><MapPin class="w-4 h-4 inline" /> Parcel:</span>
                      <span class="value">{transaction.parcelId}</span>
                    </div>
                    <div class="detail-row">
                      <span class="label"><svelte:component this={getTypeIcon(transaction.type)} class="w-4 h-4 inline" /> Type:</span>
                      <span class="value">{getTypeText(transaction.type)}</span>
                    </div>
                    <div class="detail-row">
                      <span class="label"><DollarSign class="w-4 h-4 inline" /> Price:</span>
                      <span class="value price">{transaction.price || transaction.rate}</span>
                    </div>
                    {#if transaction.duration}
                      <div class="detail-row">
                        <span class="label"><Clock class="w-4 h-4 inline" /> Duration:</span>
                        <span class="value">{transaction.duration}</span>
                      </div>
                    {/if}
                    <div class="detail-row">
                      <span class="label"><CalendarIcon class="w-4 h-4 inline" /> Started:</span>
                      <span class="value">{formatDate(transaction.startedAt)}</span>
                    </div>
                  </div>
                  
                  <div class="transaction-progress">
                    <div class="progress-header">
                      <span class="next-action">{transaction.nextAction}</span>
                    </div>
                    <!-- Multi-party approval status -->
                    {#if transaction.buyer_approval_status || transaction.chief_approval_status || transaction.witness_approval_status}
                      <div class="approval-pills">
                        <span class="approval-pill" style="background: {approvalPill(transaction.buyer_approval_status).color}15; color: {approvalPill(transaction.buyer_approval_status).color}; border-color: {approvalPill(transaction.buyer_approval_status).color}30;">
                          Buyer: {approvalPill(transaction.buyer_approval_status).label}
                        </span>
                        <span class="approval-pill" style="background: {approvalPill(transaction.chief_approval_status).color}15; color: {approvalPill(transaction.chief_approval_status).color}; border-color: {approvalPill(transaction.chief_approval_status).color}30;">
                          Chief: {approvalPill(transaction.chief_approval_status).label}
                        </span>
                        <span class="approval-pill" style="background: {approvalPill(transaction.witness_approval_status).color}15; color: {approvalPill(transaction.witness_approval_status).color}; border-color: {approvalPill(transaction.witness_approval_status).color}30;">
                          Witness: {approvalPill(transaction.witness_approval_status).label}
                        </span>
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
                  <circle cx="32" cy="32" r="32" fill="rgba(0, 122, 61, 0.1)"/>
                  <path d="M32 20L42 30H36V40H28V30H22L32 20Z" fill="var(--color-primary)" opacity="0.5"/>
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
                      <span class="label"><MapPin class="w-4 h-4 inline" /> Parcel:</span>
                      <span class="value">{transaction.parcelId}</span>
                    </div>
                    <div class="detail-row">
                      <span class="label"><User class="w-4 h-4 inline" /> Buyer:</span>
                      <span class="value">{transaction.buyer}</span>
                    </div>
                    <div class="detail-row">
                      <span class="label"><DollarSign class="w-4 h-4 inline" /> Price:</span>
                      <span class="value price">{transaction.price}</span>
                    </div>
                  </div>
                  
                  <div class="completed-actions">
                  </div>
                </div>
              {/each}
            </div>
          {:else}
            <div class="empty-state">
              <div class="empty-icon">
                <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
                  <circle cx="32" cy="32" r="32" fill="rgba(0, 122, 61, 0.1)"/>
                  <path d="M32 20L42 30H36V40H28V30H22L32 20Z" fill="var(--color-primary)" opacity="0.5"/>
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
                      <span class="label"><MapPin class="w-4 h-4 inline" /> Parcel:</span>
                      <span class="value">{interest.parcelId}</span>
                    </div>
                    <div class="detail-row">
                      <span class="label"><CalendarIcon class="w-4 h-4 inline" /> Requested:</span>
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
                      <button class="btn btn-secondary" on:click={() => handleRejectBuyerInterest(interest.id)}>
                        <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
                          <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
                        </svg>
                        Reject
                      </button>
                    {:else if interest.status === 'contact_shared'}
                      <div class="contact-shared-info">
                        <span class="shared-badge"><Check class="w-4 h-4 inline" /> Contact Shared</span>
                        <button class="btn btn-secondary btn-sm" on:click={() => {
                          const token = localStorage.getItem('token');
                          if (!token) {
                            alert('Please log in to access the chat');
                            goto('/login');
                          } else {
                            goto(`/chat/${interest.id}`);
                          }
                        }}>
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
                  <circle cx="32" cy="32" r="32" fill="rgba(0, 122, 61, 0.1)"/>
                  <path d="M32 20L42 30H36V40H28V30H22L32 20Z" fill="var(--color-primary)" opacity="0.5"/>
                </svg>
              </div>
              <h3>No Buyer Interests</h3>
              <p>When buyers show interest in your listings, they'll appear here</p>
            </div>
          {/if}
        </div>
      {/if}

      <!-- My Interests Tab -->
      {#if activeTab === 'my-interests'}
        <div class="interests-container">
          {#if myInterests.length > 0}
            <div class="interests-list">
              {#each myInterests as interest (interest.id)}
                <div class="interest-card">
                  <div class="interest-header">
                    <div class="seller-info">
                      <div class="seller-avatar">
                        <span>{interest.sellerName.charAt(0)}</span>
                      </div>
                      <div class="seller-details">
                        <div class="seller-name">{interest.sellerName}</div>
                        <div class="seller-badge">Verified Seller</div>
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
                      <span class="label"><MapPin class="w-4 h-4 inline" /> Listing:</span>
                      <span class="value">{interest.listing_title}</span>
                    </div>
                    <div class="detail-row">
                      <span class="label"><DollarSign class="w-4 h-4 inline" /> Price:</span>
                      <span class="value">{interest.listing_price ? `MK ${Number(interest.listing_price).toLocaleString()}` : 'Price on request'}</span>
                    </div>
                    {#if interest.listing_location}
                      <div class="detail-row">
                        <span class="label"><MapPin class="w-4 h-4 inline" /> Location:</span>
                        <span class="value">{interest.listing_location}</span>
                      </div>
                    {/if}
                    <div class="detail-row">
                      <span class="label"><CalendarIcon class="w-4 h-4 inline" /> Requested:</span>
                      <span class="value">{formatDate(interest.requestedAt)}</span>
                    </div>
                  </div>

                  {#if interest.status === 'contact_shared'}
                    <div class="contact-info">
                      <div class="contact-item">
                        <Phone size={16} />
                        <span>{interest.sellerPhone}</span>
                      </div>
                      {#if interest.sellerEmail}
                        <div class="contact-item">
                          <Mail size={16} />
                          <span>{interest.sellerEmail}</span>
                        </div>
                      {/if}
                    </div>
                  {/if}

                  <div class="interest-actions">
                    {#if interest.status === 'contact_shared'}
                      <button class="btn btn-primary" on:click={() => {
                        const token = localStorage.getItem('token');
                        if (!token) {
                          alert('Please log in to access the chat');
                          goto('/login');
                        } else {
                          goto(`/chat/${interest.id}`);
                        }
                      }}>
                        <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
                          <path fill-rule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clip-rule="evenodd"/>
                        </svg>
                        Open Chat
                      </button>
                    {:else if interest.status === 'pending_consent'}
                      <div class="pending-info">
                        <span class="pending-text">Waiting for seller to approve your request</span>
                      </div>
                    {:else if interest.status === 'rejected'}
                      <div class="rejected-info">
                        <span class="rejected-text">This interest was rejected by the seller</span>
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
                  <circle cx="32" cy="32" r="32" fill="rgba(0, 122, 61, 0.1)"/>
                  <path d="M32 20L42 30H36V40H28V30H22L32 20Z" fill="var(--color-primary)" opacity="0.5"/>
                </svg>
              </div>
              <h3>No Interests Yet</h3>
              <p>Browse the marketplace and express interest in listings you like</p>
              <button class="btn btn-primary" on:click={viewMarketplace}>
                Browse Marketplace
              </button>
            </div>
          {/if}
        </div>
      {/if}
    </div>
    {/if}
  </main>
</div>

<style>
  :root {
    --color-primary: #007A3D;
    --color-primary-hover: #005c2e;
    --bg-primary: #f8fafc;
    --text-primary: #0f172a;
    --color-border: #e2e8f0;
  }

  :global(*) {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }

  :global(body) {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', sans-serif;
    background: var(--bg-primary);
    color: var(--text-primary);
    line-height: 1.5;
  }

  .transactions-page {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  /* Loading and Error States */
  .loading-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 4rem 2rem;
    gap: 1rem;
  }

  .loading-spinner {
    width: 40px;
    height: 40px;
    border: 3px solid #e2e8f0;
    border-top-color: var(--color-primary);
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  .error-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 4rem 2rem;
    gap: 1rem;
  }

  .error-message {
    color: #ef4444;
    font-size: 1rem;
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
    background: var(--color-primary);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
    font-size: 0.875rem;
    cursor: pointer;
  }

  .dropdown-menu {
    position: absolute;
    top: 100%;
    right: 0;
    margin-top: 0.5rem;
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    min-width: 150px;
    z-index: 1000;
  }

  .dropdown-item {
    display: block;
    width: 100%;
    text-align: left;
    padding: 0.75rem 1rem;
    border: none;
    background: none;
    cursor: pointer;
    color: #ef4444;
    font-weight: 600;
  }

  .dropdown-item:hover {
    background: #fef2f2;
    border-radius: 8px;
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
    background: #f8fafc;
    color: #0f172a;
    box-shadow: 0 0 0 2px var(--color-primary);
  }

  .tab-icon {
    font-size: 1rem;
  }

  .tab-count {
    background: #e2e8f0;
    color: #64748b;
    padding: 0.125rem 0.5rem;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 600;
  }

  .tab-btn.active .tab-count {
    background: var(--color-primary);
    color: white;
  }

  /* Tab Content */
  .tab-content {
    min-height: 400px;
  }

  /* Listings Grid */
  .listings-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 1.5rem;
  }

  .listing-card {
    background: white;
    border-radius: 16px;
    border: 1px solid #e2e8f0;
    overflow: hidden;
    transition: all 0.25s;
    display: flex;
    flex-direction: column;
  }

  .listing-card:hover {
    border-color: #007A3D40;
    box-shadow: 0 8px 30px rgba(0,122,61,0.12);
    transform: translateY(-3px);
  }

  /* Cover photo area */
  .listing-cover {
    position: relative;
    height: 180px;
    overflow: hidden;
    background: #f1f5f9;
  }
  .listing-cover img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: transform 0.3s;
  }
  .listing-card:hover .listing-cover img { transform: scale(1.04); }

  .listing-cover.no-photo {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    color: #94a3b8;
    font-size: 0.8125rem;
  }

  .photo-count {
    position: absolute;
    bottom: 8px;
    right: 8px;
    background: rgba(0,0,0,0.55);
    color: white;
    border-radius: 20px;
    padding: 2px 8px;
    font-size: 0.75rem;
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .listing-body {
    padding: 1rem 1.25rem 1.25rem;
    display: flex;
    flex-direction: column;
    flex: 1;
  }

  .listing-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.5rem;
  }

  .listing-type-badge {
    font-size: 0.75rem;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 20px;
    background: #f0fdf4;
    color: #15803d;
  }
  .listing-type-badge.lease {
    background: #eff6ff;
    color: #1d4ed8;
  }

  .listing-title {
    font-size: 1rem;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 0.5rem;
    line-height: 1.3;
  }

  .listing-meta {
    display: flex;
    align-items: center;
    gap: 5px;
    color: #64748b;
    font-size: 0.8125rem;
    margin-bottom: 3px;
  }

  .listing-price {
    font-size: 1.125rem;
    font-weight: 700;
    color: #007A3D;
    margin-top: 0.75rem;
  }

  .listing-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: auto;
    padding-top: 0.75rem;
    border-top: 1px solid #f1f5f9;
  }

  .listing-date {
    font-size: 0.75rem;
    color: #94a3b8;
  }

  .listing-actions {
    display: flex;
    gap: 6px;
  }

  .btn-icon-action {
    width: 32px;
    height: 32px;
    border-radius: 8px;
    border: 1px solid #e2e8f0;
    background: white;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.2s;
    color: #64748b;
  }
  .btn-icon-action.view:hover { background: #eff6ff; border-color: #3b82f6; color: #3b82f6; }
  .btn-icon-action.remove:hover { background: #fef2f2; border-color: #ef4444; color: #ef4444; }
  .btn-icon-action:disabled { opacity: 0.5; cursor: not-allowed; }

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
    color: var(--color-primary);
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
    background: #f8fafc;
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
    color: var(--color-primary);
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
    background: var(--color-primary);
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

  .approval-pills {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
    margin-top: 0.5rem;
  }

  .approval-pill {
    display: inline-flex;
    align-items: center;
    padding: 0.25rem 0.625rem;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
    border: 1px solid;
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

  .contact-info {
    display: flex;
    gap: 1rem;
    margin-top: 1rem;
    padding: 0.75rem 1rem;
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    border-radius: 8px;
  }

  .contact-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.875rem;
    color: #166534;
    font-weight: 500;
  }

  .pending-info {
    margin-top: 1rem;
    padding: 0.75rem 1rem;
    background: #fef3c7;
    border: 1px solid #fcd34d;
    border-radius: 8px;
  }

  .pending-text {
    font-size: 0.875rem;
    color: #92400e;
    font-weight: 500;
  }

  .rejected-info {
    margin-top: 1rem;
    padding: 0.75rem 1rem;
    background: #fee2e2;
    border: 1px solid #fca5a5;
    border-radius: 8px;
  }

  .rejected-text {
    font-size: 0.875rem;
    color: #991b1b;
    font-weight: 500;
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
    background: var(--color-primary);
    color: white;
  }

  .btn-primary:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  }

  .btn-secondary {
    background: white;
    color: var(--color-primary);
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
    background: #f8fafc;
    color: #0f172a;
    box-shadow: 0 0 0 2px var(--color-primary);
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
    background: var(--color-primary);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
    font-size: 0.875rem;
    cursor: pointer;
  }

  .dropdown-menu {
    position: absolute;
    top: 100%;
    right: 0;
    margin-top: 0.5rem;
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    min-width: 150px;
    z-index: 1000;
  }

  .dropdown-item {
    display: block;
    width: 100%;
    text-align: left;
    padding: 0.75rem 1rem;
    border: none;
    background: none;
    cursor: pointer;
    color: #ef4444;
    font-weight: 600;
  }

  .dropdown-item:hover {
    background: #fef2f2;
    border-radius: 8px;
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
    background: var(--color-primary);
    color: white;
  }

  .btn-primary:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  }

  .btn-secondary {
    background: white;
    color: var(--color-primary);
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
