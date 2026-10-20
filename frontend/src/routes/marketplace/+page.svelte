<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { MapPin, Ruler, Calendar, Search, Filter, X } from 'lucide-svelte';
  import { fetchListings, listingImageUrl, registerListingInterest } from '$lib/api.js';
  import Navbar from '$lib/components/Navbar.svelte';

  let listings: any[] = [];
  let filteredListings: any[] = [];
  let isLoading = true;
  let error: string | null = null;
  let currentUser: any = null;

  // Filters
  let activeFilter: 'all' | 'sale' | 'lease' = 'all';
  let searchQuery = '';

  // Modal
  let selectedListing: any = null;

  onMount(async () => {
    // Check if user is logged in for the Navbar
    try {
      const token = localStorage.getItem('token');
      if (token) {
        const res = await fetch('http://localhost:5000/api/user/me', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) currentUser = await res.json();
      }
    } catch { /* silent */ }

    await loadData();
  });

  async function loadData() {
    isLoading = true;
    error = null;
    try {
      listings = await fetchListings();
      applyFilters();
    } catch (err: any) {
      error = err.message;
    } finally {
      isLoading = false;
    }
  }

  function applyFilters() {
    filteredListings = listings.filter(l => {
      // Type filter
      if (activeFilter !== 'all' && l.listing_type !== activeFilter) return false;
      // Search filter
      if (searchQuery) {
        const q = searchQuery.toLowerCase();
        const matchesTitle = l.title?.toLowerCase().includes(q);
        const matchesLocation = l.location?.toLowerCase().includes(q);
        if (!matchesTitle && !matchesLocation) return false;
      }
      return true;
    });
  }

  function setFilter(filter: 'all' | 'sale' | 'lease') {
    activeFilter = filter;
    applyFilters();
  }

  $: {
    // Re-apply filters when search changes
    if (searchQuery !== undefined) {
      applyFilters();
    }
  }

  function formatPrice(val: any): string {
    if (!val) return 'Price on request';
    return `MK ${Number(val).toLocaleString()}`;
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

  function openModal(listing: any) {
    selectedListing = listing;
    document.body.style.overflow = 'hidden'; // Prevent background scrolling
  }

  function closeModal() {
    selectedListing = null;
    document.body.style.overflow = 'auto';
  }

  async function contactSeller() {
    if (!currentUser) {
      alert('Please log in to contact the seller.');
      goto('/login');
      return;
    }

    try {
      await registerListingInterest(selectedListing.id, 'I am interested in this listing.');
      alert(`Interest registered! The seller (${selectedListing.seller_name}) will be notified.`);
      closeModal();
    } catch (err: any) {
      alert(err.message || 'Failed to register interest');
    }
  }
</script>

<svelte:head>
  <title>Marketplace — LandLock</title>
</svelte:head>

<Navbar userType={currentUser ? "citizen" : "citizen"} activeLink="/marketplace" userName={currentUser?.full_name || ''} showNotification={!!currentUser} />

<div class="marketplace-page">
  <div class="header-section">
    <div class="container">
      <h1>Land Marketplace</h1>
      <p class="subtitle">Browse verified plots of land available for sale or lease across Malawi.</p>

      <div class="filters-wrap">
        <div class="search-box">
          <Search size={18} class="search-icon" />
          <input
            type="text"
            placeholder="Search by title or location..."
            bind:value={searchQuery}
          />
        </div>
        <div class="type-filters">
          <button class="filter-btn {activeFilter === 'all' ? 'active' : ''}" on:click={() => setFilter('all')}>All</button>
          <button class="filter-btn {activeFilter === 'sale' ? 'active' : ''}" on:click={() => setFilter('sale')}>For Sale</button>
          <button class="filter-btn {activeFilter === 'lease' ? 'active' : ''}" on:click={() => setFilter('lease')}>For Lease</button>
        </div>
      </div>
    </div>
  </div>

  <main class="container content">
    {#if isLoading}
      <div class="loading-state">
        <div class="spinner"></div>
        <p>Loading listings...</p>
      </div>
    {:else if error}
      <div class="error-state">
        <p>{error}</p>
        <button class="btn-primary" on:click={loadData}>Retry</button>
      </div>
    {:else if filteredListings.length === 0}
      <div class="empty-state">
        <div class="empty-icon">
          <Filter size={32} />
        </div>
        <h3>No Listings Found</h3>
        <p>We couldn't find any listings matching your criteria.</p>
        {#if activeFilter !== 'all' || searchQuery}
          <button class="btn-secondary" on:click={() => { searchQuery = ''; setFilter('all'); }}>Clear Filters</button>
        {/if}
      </div>
    {:else}
      <div class="listings-grid">
        {#each filteredListings as listing (listing.id)}
          <button class="listing-card" on:click={() => openModal(listing)}>
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
                <span class="listing-type-badge {listing.listing_type}">
                  {listing.listing_type === 'sale' ? '🏷️ For Sale' : '🔑 For Lease'}
                </span>
              </div>

              <h3 class="listing-title">{listing.title}</h3>

              {#if listing.location}
                <div class="listing-meta">
                  <MapPin size={14} />
                  <span>{listing.location}</span>
                </div>
              {/if}

              <div class="listing-price">
                {formatPrice(listing.asking_price)}
                {#if listing.listing_type === 'lease'}
                  <span class="lease-duration">/ month</span>
                {/if}
              </div>

              <div class="listing-footer">
                <span class="listing-date">Listed {formatDate(listing.created_at)}</span>
              </div>
            </div>
          </button>
        {/each}
      </div>
    {/if}
  </main>
</div>

<!-- ── Listing Detail Modal ── -->
{#if selectedListing}
  <div class="modal-backdrop" on:click={closeModal}>
    <div class="modal-content" on:click|stopPropagation>
      <button class="modal-close" on:click={closeModal}><X size={24} /></button>
      
      <div class="modal-layout">
        <div class="modal-gallery">
          {#if selectedListing.images && selectedListing.images.length > 0}
            <div class="main-image">
              <img src={listingImageUrl(selectedListing.images[0].image_path)} alt="Cover" />
            </div>
            {#if selectedListing.images.length > 1}
              <div class="thumbnail-grid">
                {#each selectedListing.images.slice(1) as img}
                  <div class="thumbnail">
                    <img src={listingImageUrl(img.image_path)} alt="Thumbnail" />
                  </div>
                {/each}
              </div>
            {/if}
          {:else}
            <div class="main-image no-photo">
              <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="M21 15l-5-5L5 21"/></svg>
              <span>No photos available</span>
            </div>
          {/if}
        </div>

        <div class="modal-info">
          <div class="modal-header">
            <span class="listing-type-badge {selectedListing.listing_type} modal-badge">
              {selectedListing.listing_type === 'sale' ? '🏷️ For Sale' : '🔑 For Lease'}
            </span>
            <span class="modal-date">Listed {formatDate(selectedListing.created_at)}</span>
          </div>

          <h2 class="modal-title">{selectedListing.title}</h2>
          
          <div class="modal-price">
            {formatPrice(selectedListing.asking_price)}
            {#if selectedListing.listing_type === 'lease'}
              <span class="lease-duration">/ month</span>
            {/if}
          </div>

          <div class="modal-meta-grid">
            {#if selectedListing.location}
              <div class="meta-item">
                <MapPin size={18} class="meta-icon" />
                <div>
                  <span class="meta-label">Location</span>
                  <span class="meta-value">{selectedListing.location}</span>
                </div>
              </div>
            {/if}
            {#if selectedListing.size_description}
              <div class="meta-item">
                <Ruler size={18} class="meta-icon" />
                <div>
                  <span class="meta-label">Size</span>
                  <span class="meta-value">{selectedListing.size_description}</span>
                </div>
              </div>
            {/if}
          </div>

          <div class="modal-section">
            <h3>Description</h3>
            <div class="description-text">
              {#if selectedListing.description}
                {selectedListing.description}
              {:else}
                <span class="no-desc">No description provided.</span>
              {/if}
            </div>
          </div>

          <div class="modal-section seller-section">
            <h3>Seller</h3>
            <div class="seller-info">
              <div class="seller-avatar">
                {selectedListing.seller_name ? selectedListing.seller_name.charAt(0).toUpperCase() : '?'}
              </div>
              <div class="seller-details">
                <div class="seller-name">{selectedListing.seller_name || 'Verified Citizen'}</div>
                <div class="seller-badge">✓ Verified Owner</div>
              </div>
            </div>
          </div>

          <div class="modal-actions">
            <button class="btn-primary w-full" on:click={contactSeller}>
              Express Interest
            </button>
            <p class="action-hint">This will notify the seller that you are interested.</p>
          </div>
        </div>
      </div>
    </div>
  </div>
{/if}

<style>
  :global(*) { box-sizing: border-box; margin: 0; padding: 0; }
  :global(body) {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background: #f8fafc;
    color: #0f172a;
  }

  .marketplace-page {
    min-height: 100vh;
    padding-bottom: 4rem;
  }

  .container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 2rem;
  }

  /* ── Header Section ── */
  .header-section {
    background: white;
    padding: 3rem 0;
    border-bottom: 1px solid #e2e8f0;
    margin-bottom: 2rem;
  }

  .header-section h1 {
    font-size: 2.5rem;
    font-weight: 800;
    color: #0f172a;
    margin-bottom: 0.5rem;
    letter-spacing: -0.5px;
  }

  .header-section .subtitle {
    color: #64748b;
    font-size: 1.125rem;
    margin-bottom: 2rem;
    max-width: 600px;
  }

  .filters-wrap {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
    align-items: center;
  }

  .search-box {
    position: relative;
    flex: 1;
    min-width: 300px;
  }

  .search-box input {
    width: 100%;
    padding: 0.875rem 1rem 0.875rem 2.5rem;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    font-size: 0.9375rem;
    outline: none;
    transition: all 0.2s;
    background: #f8fafc;
  }
  .search-box input:focus {
    background: white;
    border-color: #007A3D;
    box-shadow: 0 0 0 3px rgba(0,122,61,0.1);
  }

  :global(.search-icon) {
    position: absolute;
    left: 1rem;
    top: 50%;
    transform: translateY(-50%);
    color: #94a3b8;
  }

  .type-filters {
    display: flex;
    background: #f1f5f9;
    padding: 0.375rem;
    border-radius: 12px;
  }

  .filter-btn {
    padding: 0.625rem 1.25rem;
    border: none;
    background: transparent;
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.875rem;
    color: #64748b;
    cursor: pointer;
    transition: all 0.2s;
  }
  .filter-btn.active {
    background: white;
    color: #0f172a;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  }

  /* ── Listings Grid ── */
  .listings-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 2rem;
  }

  .listing-card {
    background: white;
    border-radius: 16px;
    border: 1px solid #e2e8f0;
    overflow: hidden;
    transition: all 0.25s;
    display: flex;
    flex-direction: column;
    text-align: left;
    cursor: pointer;
    padding: 0;
  }

  .listing-card:hover {
    border-color: #007A3D40;
    box-shadow: 0 12px 40px rgba(0,122,61,0.08);
    transform: translateY(-4px);
  }

  .listing-cover {
    position: relative;
    height: 200px;
    background: #f1f5f9;
    overflow: hidden;
  }
  .listing-cover img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: transform 0.3s;
  }
  .listing-card:hover .listing-cover img { transform: scale(1.05); }

  .listing-cover.no-photo {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    color: #94a3b8;
    font-size: 0.875rem;
  }

  .photo-count {
    position: absolute;
    bottom: 12px;
    right: 12px;
    background: rgba(0,0,0,0.6);
    color: white;
    border-radius: 20px;
    padding: 4px 10px;
    font-size: 0.8125rem;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 6px;
    backdrop-filter: blur(4px);
  }

  .listing-body {
    padding: 1.5rem;
    display: flex;
    flex-direction: column;
    flex: 1;
  }

  .listing-top {
    margin-bottom: 0.75rem;
  }

  .listing-type-badge {
    display: inline-block;
    font-size: 0.75rem;
    font-weight: 700;
    padding: 4px 10px;
    border-radius: 20px;
    background: #f0fdf4;
    color: #15803d;
  }
  .listing-type-badge.lease {
    background: #eff6ff;
    color: #1d4ed8;
  }

  .listing-title {
    font-size: 1.125rem;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 0.75rem;
    line-height: 1.4;
  }

  .listing-meta {
    display: flex;
    align-items: center;
    gap: 6px;
    color: #64748b;
    font-size: 0.875rem;
    margin-bottom: 4px;
  }

  .listing-price {
    font-size: 1.5rem;
    font-weight: 800;
    color: #007A3D;
    margin-top: 1rem;
    display: flex;
    align-items: baseline;
    gap: 4px;
  }
  .lease-duration {
    font-size: 0.875rem;
    color: #64748b;
    font-weight: 500;
  }

  .listing-footer {
    margin-top: auto;
    padding-top: 1rem;
    border-top: 1px solid #f1f5f9;
    margin-top: 1.25rem;
  }

  .listing-date {
    font-size: 0.8125rem;
    color: #94a3b8;
  }

  /* ── Modal ── */
  .modal-backdrop {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(15, 23, 42, 0.6);
    backdrop-filter: blur(4px);
    z-index: 1000;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 2rem;
    overflow-y: auto;
  }

  .modal-content {
    background: white;
    border-radius: 24px;
    width: 100%;
    max-width: 1000px;
    max-height: 90vh;
    overflow-y: auto;
    position: relative;
    box-shadow: 0 25px 50px -12px rgba(0,0,0,0.25);
  }

  .modal-close {
    position: absolute;
    top: 1rem;
    right: 1rem;
    background: rgba(255,255,255,0.9);
    border: none;
    width: 40px; height: 40px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    z-index: 10;
    color: #0f172a;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    transition: transform 0.2s;
  }
  .modal-close:hover { transform: scale(1.1); }

  .modal-layout {
    display: grid;
    grid-template-columns: 1fr 400px;
  }

  .modal-gallery {
    background: #f8fafc;
    border-right: 1px solid #e2e8f0;
    padding: 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .main-image {
    width: 100%;
    aspect-ratio: 4/3;
    border-radius: 16px;
    overflow: hidden;
    background: #e2e8f0;
  }
  .main-image img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
  .main-image.no-photo {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    color: #94a3b8;
  }

  .thumbnail-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0.75rem;
  }
  .thumbnail {
    aspect-ratio: 1;
    border-radius: 8px;
    overflow: hidden;
    background: #e2e8f0;
  }
  .thumbnail img { width: 100%; height: 100%; object-fit: cover; }

  .modal-info {
    padding: 2.5rem;
    display: flex;
    flex-direction: column;
  }

  .modal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1rem;
  }

  .modal-badge { font-size: 0.8125rem; }
  .modal-date { font-size: 0.875rem; color: #64748b; }

  .modal-title {
    font-size: 1.75rem;
    font-weight: 800;
    color: #0f172a;
    line-height: 1.3;
    margin-bottom: 1rem;
  }

  .modal-price {
    font-size: 2rem;
    font-weight: 800;
    color: #007A3D;
    margin-bottom: 2rem;
    display: flex;
    align-items: baseline;
    gap: 6px;
  }

  .modal-meta-grid {
    display: grid;
    gap: 1.25rem;
    margin-bottom: 2rem;
    padding-bottom: 2rem;
    border-bottom: 1px solid #e2e8f0;
  }

  .meta-item {
    display: flex;
    align-items: center;
    gap: 1rem;
  }
  :global(.meta-icon) { color: #007A3D; }
  .meta-label { display: block; font-size: 0.8125rem; color: #64748b; margin-bottom: 2px; }
  .meta-value { display: block; font-size: 0.9375rem; font-weight: 600; color: #0f172a; }

  .modal-section { margin-bottom: 2rem; }
  .modal-section h3 {
    font-size: 1.125rem;
    font-weight: 700;
    margin-bottom: 0.75rem;
    color: #0f172a;
  }
  .description-text {
    color: #475569;
    line-height: 1.6;
    white-space: pre-wrap;
  }
  .no-desc { color: #94a3b8; font-style: italic; }

  .seller-info {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem;
    background: #f8fafc;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
  }
  .seller-avatar {
    width: 48px; height: 48px;
    border-radius: 50%;
    background: #007A3D;
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.25rem;
    font-weight: 700;
  }
  .seller-name { font-weight: 700; color: #0f172a; margin-bottom: 2px; }
  .seller-badge { font-size: 0.75rem; color: #16a34a; font-weight: 600; }

  .modal-actions { margin-top: auto; }
  .btn-primary.w-full {
    width: 100%;
    padding: 1rem;
    font-size: 1rem;
    justify-content: center;
    background: #007A3D;
    color: white;
    border: none;
    border-radius: 12px;
    font-weight: 700;
    cursor: pointer;
    transition: background 0.2s;
  }
  .btn-primary.w-full:hover { background: #005c2e; }
  .action-hint {
    text-align: center;
    font-size: 0.8125rem;
    color: #64748b;
    margin-top: 0.75rem;
  }

  /* ── Utilities ── */
  .spinner {
    width: 24px; height: 24px;
    border: 3px solid #e2e8f0; border-top-color: #007A3D;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  .loading-state, .error-state, .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 6rem 2rem;
    text-align: center;
    color: #64748b;
  }

  .btn-primary {
    background: #007A3D; color: white;
    border: none; border-radius: 8px;
    padding: 0.5rem 1rem; font-weight: 600; cursor: pointer;
  }
  .btn-secondary {
    background: white; color: #0f172a;
    border: 1px solid #e2e8f0; border-radius: 8px;
    padding: 0.5rem 1rem; font-weight: 600; cursor: pointer;
  }

  @media (max-width: 900px) {
    .modal-layout { grid-template-columns: 1fr; }
    .modal-gallery { border-right: none; border-bottom: 1px solid #e2e8f0; }
  }

  @media (max-width: 600px) {
    .container { padding: 0 1rem; }
    .header-section h1 { font-size: 2rem; }
    .filters-wrap { flex-direction: column; align-items: stretch; }
    .type-filters { display: flex; }
    .filter-btn { flex: 1; text-align: center; }
  }
</style>
