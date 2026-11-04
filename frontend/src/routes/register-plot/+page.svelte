<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { browser } from '$app/environment';
  import { status } from '$lib/store';
  import Navbar from '$lib/components/Navbar.svelte';
  import PaymentModal from '$lib/components/PaymentModal.svelte';

  const API = 'http://localhost:5000';

  let formData = {
    plotName: '',
    area: '',
    location: '',
    description: '',
    coordinates: ''
  };

  let isLoading = false;
  let error = '';
  let map: any = null;
  
  // Payment state
  let showPaymentModal = false;
  let paymentType = 'land_registration';
  let paymentAmount = 5000;
  let paymentDescription = 'Land Registration Fee';
  let pendingPlotData: any = null;

  onMount(() => {
    if (!browser) return;
    
    if (!localStorage.getItem('token')) {
      goto('/login');
      return;
    }

    // Initialize map for location selection
    initializeMap();
  });

  import { initMap } from '$lib/map';
  import { tick } from 'svelte';

  function initializeMap() {
    tick().then(async () => {
      const mapEl = document.getElementById('location-map');
      if (mapEl) {
        try {
          const mapModule = await import('$lib/map');
          map = await mapModule.initMap(mapEl, (e: any) => {
            formData.coordinates = `${e.latlng.lat.toFixed(6)}, ${e.latlng.lng.toFixed(6)}`;
          });
        } catch (err) {
          console.error('Failed to init map in register-plot', err);
        }
      }
    });
  }

  async function handleSubmit() {
    if (!formData.plotName || !formData.area) {
      error = 'Please fill in all required fields';
      return;
    }

    // Store plot data and show payment modal
    pendingPlotData = {
      plot_name: formData.plotName,
      area: parseFloat(formData.area),
      location: formData.location,
      description: formData.description,
      coordinates: formData.coordinates
    };
    
    showPaymentModal = true;
  }

  async function handlePaymentCompleted(event: any) {
    const payment = event.detail.payment;
    
    // Now submit the plot registration with payment info
    isLoading = true;
    error = '';

    try {
      const response = await fetch(`${API}/api/plots`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          ...pendingPlotData,
          payment_id: payment.id
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Registration failed');
      }

      status.set('Plot registered successfully!');
      setTimeout(() => {
        goto('/dashboard');
      }, 1500);
    } catch (err: any) {
      error = err.message;
      status.set('Registration failed: ' + err.message);
    } finally {
      isLoading = false;
      pendingPlotData = null;
    }
  }

  function handleCancel() {
    goto('/dashboard');
  }
</script>

<svelte:head>
  <title>Register Plot - LandLock</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</svelte:head>

<div class="register-plot-container">
  <Navbar userType="official" activeLink="/register-plot" userName="Official" showNotification={false} />

  <main class="main-content">
    <div class="page-header">
      <h1>Register New Plot</h1>
      <p>Add your land plot to the registry</p>
    </div>

    {#if error}
      <div class="error-message">
        {error}
      </div>
    {/if}

    <form class="registration-form" on:submit|preventDefault={handleSubmit}>
      <div class="form-grid">
        <div class="form-group">
          <label for="plotName">Plot Name *</label>
          <input
            id="plotName"
            type="text"
            bind:value={formData.plotName}
            placeholder="Enter plot name"
            required
          />
        </div>

        <div class="form-group">
          <label for="area">Area (meters) *</label>
          <input
            id="area"
            type="number"
            bind:value={formData.area}
            placeholder="Enter plot area"
            step="0.01"
            required
          />
        </div>

        <div class="form-group">
          <label for="location">Location</label>
          <input
            id="location"
            type="text"
            bind:value={formData.location}
            placeholder="Village, District"
          />
        </div>

        <div class="form-group">
          <label for="coordinates">GPS Coordinates</label>
          <input
            id="coordinates"
            type="text"
            bind:value={formData.coordinates}
            placeholder="Latitude, Longitude"
          />
        </div>
      </div>

      <div class="form-group">
        <label for="description">Description</label>
        <textarea
          id="description"
          bind:value={formData.description}
          placeholder="Describe the plot, landmarks, etc."
          rows="4"
        ></textarea>
      </div>

      <div class="map-section" style="margin-bottom: 2rem;">
        <h3>Select Plot Location</h3>
        <p class="text-sm text-gray-500 mb-2">Click on the map to set the GPS coordinates for this plot.</p>
        <div id="location-map" class="map-placeholder" style="border: 2px solid #e2e8f0; z-index: 1;">
        </div>
      </div>

      <div class="form-actions">
        <button type="button" class="btn-cancel" on:click={handleCancel}>
          Cancel
        </button>
        <button type="submit" class="btn-submit" disabled={isLoading}>
          {isLoading ? 'Registering...' : 'Register Plot'}
        </button>
      </div>
    </form>
  </main>

  <PaymentModal
    bind:isOpen={showPaymentModal}
    paymentType={paymentType}
    amount={paymentAmount}
    description={paymentDescription}
    on:paymentCompleted={handlePaymentCompleted}
  />
</div>

<style>
  :global(body) {
    margin: 0;
    padding: 0;
    font-family: 'Inter', sans-serif;
    background: #f8faf9;
  }

  .register-plot-container {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  .main-content {
    max-width: 1400px;
    margin: 0 auto;
    padding: 2rem;
    width: 100%;
    flex: 1;
  }

  .page-header {
    text-align: center;
    margin-bottom: 2rem;
  }

  .page-header h1 {
    font-size: 2rem;
    font-weight: 700;
    color: #1e293b;
    margin: 0 0 0.5rem 0;
  }

  .page-header p {
    color: #64748b;
    font-size: 1rem;
  }

  .error-message {
    background: #fee2e2;
    color: #dc2626;
    padding: 1rem;
    border-radius: 8px;
    margin-bottom: 1.5rem;
    border: 1px solid #fecaca;
  }

  .registration-form {
    background: white;
    border-radius: 12px;
    padding: 2rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    border: 1px solid #e2e8f0;
    margin-bottom: 2rem;
  }

  .form-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1.5rem;
    margin-bottom: 1.5rem;
  }

  .form-group {
    display: flex;
    flex-direction: column;
  }

  .form-group label {
    font-weight: 600;
    color: #374151;
    margin-bottom: 0.5rem;
    font-size: 0.875rem;
  }

  .form-group input,
  .form-group textarea {
    padding: 0.75rem;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    font-size: 1rem;
    transition: border-color 0.2s;
  }

  .form-group input:focus,
  .form-group textarea:focus {
    outline: none;
    border-color: var(--color-primary);
    box-shadow: 0 0 0 3px rgba(0, 122, 61, 0.15);
  }

  .form-group textarea {
    resize: vertical;
  }

  .form-actions {
    display: flex;
    gap: 1rem;
    justify-content: flex-end;
    margin-top: 2rem;
  }

  .btn-cancel {
    padding: 0.75rem 1.5rem;
    border: 1px solid #d1d5db;
    background: white;
    color: #374151;
    border-radius: 6px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
  }

  .btn-cancel:hover {
    background: #f3f4f6;
  }

  .btn-submit {
    padding: 0.75rem 1.5rem;
    border: none;
    background: var(--color-primary);
    color: white;
    border-radius: 6px;
    font-weight: 500;
    cursor: pointer;
    transition: background-color 0.2s;
  }

  .btn-submit:hover:not(:disabled) {
    background: var(--color-primary-hover);
  }

  .btn-submit:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .map-section {
    background: white;
    border-radius: 12px;
    padding: 2rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    border: 1px solid #e2e8f0;
  }

  .map-section h3 {
    font-size: 1.125rem;
    font-weight: 600;
    color: #374151;
    margin: 0 0 1rem 0;
  }

  .map-placeholder {
    height: 300px;
    background: #f3f4f6;
    border: 2px dashed #d1d5db;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #6b7280;
  }

  @media (max-width: 768px) {
    .register-plot-container {
      margin: 1rem auto;
    }

    .form-grid {
      grid-template-columns: 1fr;
    }

    .form-actions {
      flex-direction: column;
    }

    .btn-cancel,
    .btn-submit {
      width: 100%;
    }
  }
</style>
