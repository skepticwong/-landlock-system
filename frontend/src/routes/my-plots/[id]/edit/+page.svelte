<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { browser } from '$app/environment';
  import Navbar from '$lib/components/Navbar.svelte';
  import { Save, ArrowLeft, AlertTriangle } from 'lucide-svelte';
  import { page } from '$app/stores';

  const API = 'http://localhost:5000';
  let plot = null;
  let isLoading = true;
  let isSaving = false;
  let saveError = null;
  let currentUser = null;

  // Form fields
  let plotName = '';
  let district = '';
  let traditionalAuthority = '';
  let village = '';
  let landmarkDescription = '';
  let landUse = '';
  let acquisitionMethod = '';
  let estimatedSize = '';
  let sizeUnit = 'meters'; // meters, sqmeters, acres, hectares

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

  async function fetchPlot() {
    isLoading = true;
    try {
      const plotId = $page.params.id;
      const res = await fetch(`${API}/api/plots/${plotId}`, { headers: authHeaders() });
      if (res.ok) {
        plot = await res.json();
        
        // Check if user owns this plot
        if (plot.user_id !== currentUser.id) {
          goto('/my-plots');
          return;
        }

        // Populate form fields
        plotName = plot.plot_name || '';
        district = plot.district || '';
        traditionalAuthority = plot.traditional_authority || '';
        village = plot.village || '';
        landmarkDescription = plot.landmark_description || '';
        landUse = plot.land_use || '';
        acquisitionMethod = plot.acquisition_method || '';
        estimatedSize = plot.estimated_size || '';
        sizeUnit = plot.size_unit || 'meters';
      } else {
        goto('/my-plots');
      }
    } catch (err) {
      console.error('Error fetching plot:', err);
      saveError = 'Failed to load plot details';
    } finally {
      isLoading = false;
    }
  }

  async function savePlot() {
    isSaving = true;
    saveError = null;
    
    try {
      const plotId = $page.params.id;
      const updateData = {
        plot_name: plotName,
        district: district,
        traditional_authority: traditionalAuthority,
        village: village,
        landmark_description: landmarkDescription,
        land_use: landUse,
        acquisition_method: acquisitionMethod,
        estimated_size: estimatedSize,
        size_unit: sizeUnit,
        status: 'pending' // Reset to pending for re-approval
      };

      const res = await fetch(`${API}/api/plots/${plotId}`, {
        method: 'PUT',
        headers: {
          ...authHeaders(),
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(updateData)
      });

      if (res.ok) {
        goto('/my-plots');
      } else {
        const error = await res.json();
        saveError = error.error || 'Failed to update plot';
      }
    } catch (err) {
      console.error('Error saving plot:', err);
      saveError = 'Failed to update plot. Please try again.';
    } finally {
      isSaving = false;
    }
  }

  function goBack() {
    goto('/my-plots');
  }

  onMount(async () => {
    if (!browser) return;

    if (!localStorage.getItem('token')) {
      goto('/login');
      return;
    }

    await fetchCurrentUser();
    await fetchPlot();
  });
</script>

<svelte:head>
  <title>Edit Plot - LandLock</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</svelte:head>

<div class="edit-plot-page">
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
        <p>Loading plot details...</p>
      </div>
    {:else}
      <div class="edit-container">
        <div class="edit-header">
          <h1>Edit Plot</h1>
          <p>MLW-{$page.params.id}</p>
        </div>

        <div class="approval-warning">
          <AlertTriangle class="w-5 h-5 inline" />
          <div>
            <strong>Important:</strong> Editing this plot will reset its status to "Pending" and require re-approval from officials.
          </div>
        </div>

        <form class="edit-form" on:submit|preventDefault={savePlot}>
          <div class="form-section">
            <h2>Basic Information</h2>
            
            <div class="form-group">
              <label for="plotName">Plot Name *</label>
              <input
                id="plotName"
                type="text"
                bind:value={plotName}
                required
                placeholder="e.g., Chilomoni Village Plot"
              />
            </div>

            <div class="form-row">
              <div class="form-group">
                <label for="district">District *</label>
                <select id="district" bind:value={district} required>
                  <option value="">Select District</option>
                  <option value="Lilongwe">Lilongwe</option>
                  <option value="Blantyre">Blantyre</option>
                  <option value="Mzuzu">Mzuzu</option>
                  <option value="Zomba">Zomba</option>
                  <option value="Kasungu">Kasungu</option>
                  <option value="Mangochi">Mangochi</option>
                  <option value="Salima">Salima</option>
                  <option value="Dedza">Dedza</option>
                  <option value="Ntcheu">Ntcheu</option>
                  <option value="Mwanza">Mwanza</option>
                </select>
              </div>

              <div class="form-group">
                <label for="traditionalAuthority">Traditional Authority *</label>
                <select id="traditionalAuthority" bind:value={traditionalAuthority} required>
                  <option value="">Select Authority</option>
                  <option value="Chief Mwase">Chief Mwase</option>
                  <option value="Chief Bvumbwe">Chief Bvumbwe</option>
                  <option value="Chief Kuntaja">Chief Kuntaja</option>
                  <option value="Chief Nkhoma">Chief Nkhoma</option>
                  <option value="Chief Chapola">Chief Chapola</option>
                  <option value="Chief Mbelwa">Chief Mbelwa</option>
                  <option value="Chief Chikuse">Chief Chikuse</option>
                </select>
              </div>
            </div>

            <div class="form-group">
              <label for="village">Village *</label>
              <input
                id="village"
                type="text"
                bind:value={village}
                required
                placeholder="e.g., Chilomoni"
              />
            </div>
          </div>

          <div class="form-section">
            <h2>Land Details</h2>

            <div class="form-group">
              <label for="estimatedSize">Estimated Size</label>
              <div class="size-input-group">
                <input
                  id="estimatedSize"
                  type="text"
                  bind:value={estimatedSize}
                  placeholder="e.g., 20 x 20"
                />
                <select id="sizeUnit" bind:value={sizeUnit}>
                  <option value="meters">meters</option>
                  <option value="sqmeters">m²</option>
                  <option value="acres">acres</option>
                  <option value="hectares">hectares</option>
                </select>
              </div>
            </div>

            <div class="form-group">
              <label for="landUse">Land Use</label>
              <select id="landUse" bind:value={landUse}>
                <option value="">Select Land Use</option>
                <option value="residential">Residential</option>
                <option value="agricultural">Agricultural</option>
                <option value="commercial">Commercial</option>
                <option value="industrial">Industrial</option>
                <option value="mixed">Mixed Use</option>
              </select>
            </div>

            <div class="form-group">
              <label for="acquisitionMethod">Acquisition Method</label>
              <select id="acquisitionMethod" bind:value={acquisitionMethod}>
                <option value="">Select Method</option>
                <option value="inheritance">Inheritance</option>
                <option value="purchase">Purchase</option>
                <option value="allocation">Customary Allocation</option>
                <option value="gift">Gift</option>
                <option value="other">Other</option>
              </select>
            </div>

            <div class="form-group">
              <label for="landmarkDescription">Landmark Description</label>
              <textarea
                id="landmarkDescription"
                bind:value={landmarkDescription}
                placeholder="Describe nearby landmarks, boundaries, or notable features"
                rows="3"
              ></textarea>
            </div>
          </div>

          {#if saveError}
            <div class="error-message">
              {saveError}
            </div>
          {/if}

          <div class="form-actions">
            <button type="button" class="btn btn-secondary" on:click={goBack}>
              Cancel
            </button>
            <button type="submit" class="btn btn-primary" disabled={isSaving}>
              {#if isSaving}
                <span class="spinner-small"></span>
                Saving...
              {:else}
                <Save class="w-4 h-4 inline" />
                Save Changes
              {/if}
            </button>
          </div>
        </form>
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

  .edit-plot-page {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  .main-content {
    max-width: 800px;
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

  .edit-container {
    background: white;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
    overflow: hidden;
  }

  .edit-header {
    padding: 2rem;
    border-bottom: 1px solid #e2e8f0;
  }

  .edit-header h1 {
    font-size: 1.5rem;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 0.25rem;
  }

  .edit-header p {
    color: #64748b;
    font-size: 0.9375rem;
  }

  .approval-warning {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    padding: 1rem 2rem;
    background: #fef3c7;
    border-bottom: 1px solid #fde68a;
    color: #92400e;
    font-size: 0.875rem;
  }

  .edit-form {
    padding: 2rem;
  }

  .form-section {
    margin-bottom: 2rem;
  }

  .form-section:last-of-type {
    margin-bottom: 0;
  }

  .form-section h2 {
    font-size: 1.125rem;
    font-weight: 600;
    color: #0f172a;
    margin-bottom: 1rem;
  }

  .form-group {
    margin-bottom: 1.25rem;
  }

  .size-input-group {
    display: flex;
    gap: 0.5rem;
  }

  .size-input-group input {
    flex: 1;
  }

  .size-input-group select {
    width: 140px;
  }

  .form-group label {
    display: block;
    font-weight: 500;
    color: #374151;
    font-size: 0.9375rem;
    margin-bottom: 0.5rem;
  }

  .form-group input,
  .form-group select,
  .form-group textarea {
    width: 100%;
    padding: 0.75rem 1rem;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    font-size: 0.9375rem;
    font-family: inherit;
    transition: all 0.2s;
  }

  .form-group input:focus,
  .form-group select:focus,
  .form-group textarea:focus {
    outline: none;
    border-color: #007A3D;
    box-shadow: 0 0 0 3px rgba(0, 122, 61, 0.1);
  }

  .form-group textarea {
    resize: vertical;
    min-height: 80px;
  }

  .form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
  }

  .error-message {
    padding: 1rem;
    background: #fef2f2;
    border: 1px solid #fecaca;
    border-radius: 8px;
    color: #dc2626;
    font-size: 0.875rem;
    margin-bottom: 1.5rem;
  }

  .form-actions {
    display: flex;
    gap: 1rem;
    padding-top: 2rem;
    border-top: 1px solid #e2e8f0;
  }

  .btn {
    padding: 0.75rem 1.5rem;
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

  .btn-primary:hover:not(:disabled) {
    background: #005C2E;
  }

  .btn-primary:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .btn-secondary {
    background: white;
    color: #64748b;
    border: 1px solid #e2e8f0;
  }

  .btn-secondary:hover {
    background: #f8fafc;
    color: #0f172a;
  }

  .spinner-small {
    width: 16px;
    height: 16px;
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-top-color: white;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    display: inline-block;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
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

  .loading-state p {
    color: #64748b;
  }

  @media (max-width: 768px) {
    .main-content {
      padding: 1rem;
    }

    .form-row {
      grid-template-columns: 1fr;
    }

    .form-actions {
      flex-direction: column;
    }

    .form-actions .btn {
      width: 100%;
      justify-content: center;
    }
  }
</style>
