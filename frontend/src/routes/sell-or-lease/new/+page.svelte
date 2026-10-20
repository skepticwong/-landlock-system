<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';
  import { browser } from '$app/environment';
  import { createListing, uploadListingImages } from '$lib/api.js';
  import Navbar from '$lib/components/Navbar.svelte';

  let currentUser: any = null;
  let isSubmitting = false;
  let submitError = '';
  let success = false;
  let createdListingId: number | null = null;
  let plotId: number | null = null;
  let plotDetails: any = null;
  let plotError = '';

  // Form fields
  let listingType: 'sale' | 'lease' = 'sale';
  let title = '';
  let location = '';
  let askingPrice = '';
  let sizeDescription = '';
  let description = '';

  // Images
  let selectedFiles: File[] = [];
  let previews: string[] = [];
  let isDragging = false;
  let fileInput: HTMLInputElement;

  onMount(() => {
    if (!browser) return;
    if (!localStorage.getItem('token')) { goto('/login'); return; }
    fetchUser();

    // Prefill from query params if passed
    const params = new URLSearchParams(window.location.search);
    const plotIdParam = params.get('plotId');
    if (!plotIdParam) {
      goto('/my-plots');
      return;
    }
    plotId = parseInt(plotIdParam);
    if (isNaN(plotId)) {
      goto('/my-plots');
      return;
    }

    if (params.get('title')) title = params.get('title') || '';
    if (params.get('location')) location = params.get('location') || '';
    if (params.get('size')) sizeDescription = params.get('size') || '';

    fetchPlotDetails(plotId);
  });

  async function fetchUser() {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch('http://localhost:5000/api/user/me', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) currentUser = await res.json();
    } catch { /* silent */ }
  }

  async function fetchPlotDetails(id: number) {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`http://localhost:5000/api/plots/${id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        plotDetails = await res.json();
        title = plotDetails.plot_name || title;
        location = plotDetails.district || plotDetails.village || location;
        if (plotDetails.estimated_size) {
          sizeDescription = `${plotDetails.estimated_size} ${getUnitLabel(plotDetails.size_unit)}`;
        }
      } else {
        const err = await res.json().catch(() => ({}));
        plotError = err.error || 'Failed to verify registered plot details.';
        submitError = plotError;
      }
    } catch {
      plotError = 'Could not verify plot ownership.';
      submitError = plotError;
    }
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

  function handleFileSelect(files: FileList | null) {
    if (!files) return;
    const allowed = Array.from(files).filter(f => f.type.startsWith('image/'));
    const remaining = 5 - selectedFiles.length;
    const toAdd = allowed.slice(0, remaining);
    toAdd.forEach(f => {
      selectedFiles = [...selectedFiles, f];
      const reader = new FileReader();
      reader.onload = e => { previews = [...previews, e.target?.result as string]; };
      reader.readAsDataURL(f);
    });
  }

  function removeFile(i: number) {
    selectedFiles = selectedFiles.filter((_, idx) => idx !== i);
    previews = previews.filter((_, idx) => idx !== i);
  }

  function onDrop(e: DragEvent) {
    e.preventDefault();
    isDragging = false;
    handleFileSelect(e.dataTransfer?.files ?? null);
  }

  async function handleSubmit() {
    if (plotError) { submitError = plotError; return; }
    if (!title.trim()) { submitError = 'Please enter a listing title.'; return; }
    submitError = '';
    isSubmitting = true;
    try {
      const listing = await createListing({
        plot_id: plotId,
        title: title.trim(),
        listing_type: listingType,
        location: location.trim(),
        asking_price: askingPrice ? parseFloat(askingPrice) : null,
        size_description: sizeDescription.trim(),
        description: description.trim()
      });

      if (selectedFiles.length > 0) {
        await uploadListingImages(listing.id, selectedFiles);
      }

      createdListingId = listing.id;
      success = true;
    } catch (e: any) {
      submitError = e.message || 'Something went wrong. Please try again.';
    } finally {
      isSubmitting = false;
    }
  }
</script>

<svelte:head>
  <title>Post Land for Sale — LandLock</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
</svelte:head>

<Navbar userType="citizen" activeLink="/transactions" userName={currentUser?.full_name || ''} />

<div class="page">
  {#if success}
    <!-- ── Success screen ── -->
    <div class="success-wrap">
      <div class="success-card">
        <div class="success-icon">
          <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
            <circle cx="24" cy="24" r="24" fill="#dcfce7"/>
            <path d="M14 24l7 7 13-13" stroke="#16a34a" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <h2>Listing Published!</h2>
        <p>Your land is now live on the marketplace. Interested buyers can see it and contact you.</p>
        <div class="success-actions">
          <button class="btn-primary" on:click={() => goto('/marketplace')}>View Marketplace</button>
          <button class="btn-secondary" on:click={() => goto('/transactions')}>My Listings</button>
        </div>
      </div>
    </div>
  {:else}
    <!-- ── Form ── -->
    <div class="form-wrap">
      <div class="form-header">
        <button class="back-btn" on:click={() => goto('/transactions')}>
          <svg width="18" height="18" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z" clip-rule="evenodd"/></svg>
          Back
        </button>
        <div>
          <h1>Post Your Land</h1>
          <p class="subtitle">Fill in the details below to list your land on the marketplace</p>
        </div>
      </div>

      <div class="form-card">
        <!-- Type toggle -->
        <div class="field-group">
          <label class="field-label">Listing Type</label>
          <div class="type-toggle">
            <button
              class="toggle-btn {listingType === 'sale' ? 'active' : ''}"
              on:click={() => listingType = 'sale'}
              type="button"
            >
              🏷️ For Sale
            </button>
            <button
              class="toggle-btn {listingType === 'lease' ? 'active lease' : ''}"
              on:click={() => listingType = 'lease'}
              type="button"
            >
              🔑 For Lease
            </button>
          </div>
        </div>

        <!-- Title -->
        <div class="field-group">
          <label class="field-label" for="title">Listing Title <span class="required">*</span></label>
          <input
            id="title"
            class="field-input"
            type="text"
            placeholder="e.g. Residential Plot in Area 25, Lilongwe"
            bind:value={title}
            disabled
          />
        </div>

        <!-- Location + Size row -->
        <div class="field-row">
          <div class="field-group">
            <label class="field-label" for="location">Location</label>
            <input
              id="location"
              class="field-input"
              type="text"
              placeholder="e.g. Area 25, Lilongwe"
              bind:value={location}
              disabled
            />
          </div>
          <div class="field-group">
            <label class="field-label" for="size">Size / Dimensions</label>
            <input
              id="size"
              class="field-input"
              type="text"
              placeholder="e.g. 30m × 40m, 1 acre"
              bind:value={sizeDescription}
              disabled
            />
          </div>
        </div>

        <!-- Price -->
        <div class="field-group">
          <label class="field-label" for="price">
            {listingType === 'sale' ? 'Asking Price (MWK)' : 'Lease Rate (MWK / month)'}
          </label>
          <div class="price-input-wrap">
            <span class="price-prefix">MK</span>
            <input
              id="price"
              class="field-input price"
              type="number"
              min="0"
              placeholder="0"
              bind:value={askingPrice}
            />
          </div>
        </div>

        <!-- Description -->
        <div class="field-group">
          <label class="field-label" for="desc">Description</label>
          <textarea
            id="desc"
            class="field-input"
            rows="4"
            placeholder="Describe the land — nearby landmarks, road access, utilities, title deed status, etc."
            bind:value={description}
          ></textarea>
        </div>

        <!-- Photo uploader -->
        <div class="field-group">
          <label class="field-label">
            Photos
            <span class="field-hint">Up to 5 photos — buyers trust listings with clear images</span>
          </label>

          <!-- Drop zone -->
          {#if selectedFiles.length < 5}
            <div
              class="drop-zone {isDragging ? 'drag-over' : ''}"
              on:dragover|preventDefault={() => isDragging = true}
              on:dragleave={() => isDragging = false}
              on:drop={onDrop}
              on:click={() => fileInput.click()}
              role="button"
              tabindex="0"
              on:keydown={e => e.key === 'Enter' && fileInput.click()}
            >
              <input
                bind:this={fileInput}
                type="file"
                accept="image/*"
                multiple
                style="display:none"
                on:change={e => handleFileSelect(e.currentTarget.files)}
              />
              <div class="drop-icon">
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <rect x="3" y="3" width="18" height="18" rx="2"/>
                  <circle cx="8.5" cy="8.5" r="1.5"/>
                  <path d="M21 15l-5-5L5 21"/>
                </svg>
              </div>
              <p class="drop-label">Click or drag photos here</p>
              <p class="drop-sub">JPG, PNG, WEBP — max 5 photos ({5 - selectedFiles.length} remaining)</p>
            </div>
          {/if}

          <!-- Previews -->
          {#if previews.length > 0}
            <div class="preview-grid">
              {#each previews as src, i}
                <div class="preview-item">
                  <img {src} alt="preview {i+1}" />
                  {#if i === 0}<span class="cover-badge">Cover</span>{/if}
                  <button class="remove-photo" on:click={() => removeFile(i)} title="Remove">
                    <svg width="14" height="14" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/></svg>
                  </button>
                </div>
              {/each}
            </div>
          {/if}
        </div>

        {#if submitError}
          <div class="error-banner">{submitError}</div>
        {/if}

        <div class="form-footer">
          <button class="btn-secondary" on:click={() => goto('/transactions')} type="button">Cancel</button>
          <button
            class="btn-primary"
            on:click={handleSubmit}
            disabled={isSubmitting}
            type="button"
          >
            {#if isSubmitting}
              <span class="spinner"></span> Publishing...
            {:else}
              Publish Listing
            {/if}
          </button>
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  :global(*) { box-sizing: border-box; margin: 0; padding: 0; }
  :global(body) {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background: #f8fafc;
    color: #0f172a;
  }

  .page { min-height: 100vh; }

  /* ── Success screen ── */
  .success-wrap {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: calc(100vh - 64px);
    padding: 2rem;
  }

  .success-card {
    background: white;
    border-radius: 20px;
    border: 1px solid #e2e8f0;
    padding: 3rem 2.5rem;
    max-width: 440px;
    width: 100%;
    text-align: center;
    box-shadow: 0 8px 40px rgba(0,0,0,0.08);
  }

  .success-icon { margin-bottom: 1.5rem; display: flex; justify-content: center; }

  .success-card h2 {
    font-size: 1.5rem;
    font-weight: 800;
    color: #0f172a;
    margin-bottom: 0.75rem;
  }

  .success-card p {
    color: #64748b;
    line-height: 1.6;
    margin-bottom: 2rem;
  }

  .success-actions { display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap; }

  /* ── Form layout ── */
  .form-wrap {
    max-width: 760px;
    margin: 0 auto;
    padding: 2rem;
  }

  .form-header {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    margin-bottom: 1.5rem;
  }

  .back-btn {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 8px 14px;
    border: 1px solid #e2e8f0;
    background: white;
    border-radius: 8px;
    color: #64748b;
    cursor: pointer;
    font-size: 0.875rem;
    font-weight: 500;
    transition: all 0.2s;
    white-space: nowrap;
    margin-top: 4px;
  }
  .back-btn:hover { background: #f1f5f9; color: #334155; }

  .form-header h1 {
    font-size: 1.75rem;
    font-weight: 800;
    color: #0f172a;
    line-height: 1.2;
  }
  .subtitle { color: #64748b; margin-top: 4px; font-size: 0.9375rem; }

  .form-card {
    background: white;
    border-radius: 20px;
    border: 1px solid #e2e8f0;
    padding: 2rem;
    box-shadow: 0 2px 12px rgba(0,0,0,0.04);
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  /* ── Type toggle ── */
  .type-toggle {
    display: flex;
    gap: 0.75rem;
  }

  .toggle-btn {
    flex: 1;
    padding: 0.875rem;
    border-radius: 12px;
    border: 2px solid #e2e8f0;
    background: white;
    font-size: 0.9375rem;
    font-weight: 600;
    color: #64748b;
    cursor: pointer;
    transition: all 0.2s;
    text-align: center;
  }
  .toggle-btn.active {
    border-color: #007A3D;
    background: #f0fdf4;
    color: #15803d;
  }
  .toggle-btn.active.lease {
    border-color: #3b82f6;
    background: #eff6ff;
    color: #1d4ed8;
  }

  /* ── Fields ── */
  .field-group { display: flex; flex-direction: column; gap: 0.375rem; }

  .field-label {
    font-size: 0.875rem;
    font-weight: 600;
    color: #374151;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  .required { color: #ef4444; }
  .field-hint { font-weight: 400; color: #94a3b8; font-size: 0.8125rem; }

  .field-input {
    padding: 0.75rem 1rem;
    border: 1.5px solid #e2e8f0;
    border-radius: 10px;
    font-size: 0.9375rem;
    color: #0f172a;
    background: #fafafa;
    transition: border-color 0.2s, box-shadow 0.2s;
    font-family: inherit;
    width: 100%;
    resize: vertical;
  }
  .field-input:focus {
    outline: none;
    border-color: #007A3D;
    background: white;
    box-shadow: 0 0 0 3px rgba(0,122,61,0.1);
  }
  .field-input:disabled {
    background: #f1f5f9;
    color: #64748b;
    border-color: #cbd5e1;
    cursor: not-allowed;
    opacity: 0.8;
  }

  .field-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.25rem;
  }

  .price-input-wrap {
    position: relative;
    display: flex;
    align-items: center;
  }
  .price-prefix {
    position: absolute;
    left: 1rem;
    color: #64748b;
    font-weight: 600;
    font-size: 0.9375rem;
    pointer-events: none;
  }
  .field-input.price { padding-left: 3rem; }

  /* ── Drop zone ── */
  .drop-zone {
    border: 2px dashed #cbd5e1;
    border-radius: 14px;
    padding: 2.5rem 1rem;
    text-align: center;
    cursor: pointer;
    transition: all 0.2s;
    background: #fafafa;
  }
  .drop-zone:hover, .drop-zone.drag-over {
    border-color: #007A3D;
    background: #f0fdf4;
  }
  .drop-icon { color: #94a3b8; display: flex; justify-content: center; margin-bottom: 0.75rem; }
  .drop-zone:hover .drop-icon, .drop-zone.drag-over .drop-icon { color: #007A3D; }
  .drop-label { font-weight: 600; color: #374151; margin-bottom: 0.25rem; }
  .drop-sub { font-size: 0.8125rem; color: #94a3b8; }

  /* ── Previews ── */
  .preview-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    gap: 0.75rem;
    margin-top: 0.75rem;
  }

  .preview-item {
    position: relative;
    border-radius: 10px;
    overflow: hidden;
    aspect-ratio: 1;
    border: 2px solid #e2e8f0;
    background: #f1f5f9;
  }
  .preview-item img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
  }
  .cover-badge {
    position: absolute;
    bottom: 4px;
    left: 4px;
    background: #007A3D;
    color: white;
    font-size: 0.65rem;
    font-weight: 700;
    padding: 2px 6px;
    border-radius: 4px;
    text-transform: uppercase;
  }
  .remove-photo {
    position: absolute;
    top: 4px;
    right: 4px;
    width: 22px;
    height: 22px;
    background: rgba(0,0,0,0.6);
    border: none;
    border-radius: 50%;
    color: white;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background 0.2s;
  }
  .remove-photo:hover { background: #ef4444; }

  /* ── Buttons ── */
  .btn-primary {
    padding: 0.875rem 2rem;
    background: #007A3D;
    color: white;
    border: none;
    border-radius: 10px;
    font-size: 0.9375rem;
    font-weight: 700;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    transition: background 0.2s, transform 0.15s;
  }
  .btn-primary:hover:not(:disabled) { background: #005c2e; transform: translateY(-1px); }
  .btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }

  .btn-secondary {
    padding: 0.875rem 2rem;
    background: white;
    color: #374151;
    border: 1.5px solid #e2e8f0;
    border-radius: 10px;
    font-size: 0.9375rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
  }
  .btn-secondary:hover { background: #f8fafc; border-color: #cbd5e1; }

  .form-footer {
    display: flex;
    justify-content: flex-end;
    gap: 1rem;
    padding-top: 0.5rem;
    border-top: 1px solid #f1f5f9;
  }

  .error-banner {
    background: #fef2f2;
    border: 1px solid #fecaca;
    color: #dc2626;
    border-radius: 10px;
    padding: 0.875rem 1rem;
    font-size: 0.9rem;
    font-weight: 500;
  }

  .spinner {
    width: 16px;
    height: 16px;
    border: 2px solid rgba(255,255,255,0.4);
    border-top-color: white;
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
    display: inline-block;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  @media (max-width: 600px) {
    .form-wrap { padding: 1rem; }
    .form-card { padding: 1.25rem; }
    .field-row { grid-template-columns: 1fr; }
    .type-toggle { flex-direction: column; }
  }
</style>
