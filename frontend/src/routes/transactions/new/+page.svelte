<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { browser } from '$app/environment';

  // Step management
  let currentStep = 1;
  const totalSteps = 3;
  
  // User's verified parcels (mock data)
  let verifiedParcels = [
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

  // Form data
  let transactionData = {
    selectedParcel: '',
    transactionType: '', // 'sale' or 'lease'
    price: '',
    leaseRate: '',
    leaseDuration: '',
    terms: ''
  };

  // UI state
  let isOnline = navigator.onLine;
  let isSubmitting = false;
  let listingStatus: 'idle' | 'success' | 'offline' = 'idle';
  let listingUrl = '';

  // Lease duration options
  const leaseDurations = Array.from({length: 99}, (_, i) => `${i + 1} year${i > 0 ? 's' : ''}`);

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

  function nextStep() {
    if (currentStep < totalSteps) {
      currentStep++;
    }
  }

  function prevStep() {
    if (currentStep > 1) {
      currentStep--;
    }
  }

  function goToStep(step: number) {
    if (step >= 1 && step <= totalSteps) {
      currentStep = step;
    }
  }

  function selectParcel(parcelId: string) {
    transactionData.selectedParcel = parcelId;
  }

  function setTransactionType(type: 'sale' | 'lease') {
    transactionData.transactionType = type;
    // Clear other type's fields
    if (type === 'sale') {
      transactionData.leaseRate = '';
      transactionData.leaseDuration = '';
    } else {
      transactionData.price = '';
    }
  }

  async function publishListing() {
    isSubmitting = true;
    
    try {
      // Generate listing URL
      listingUrl = `landlock.mw/listings/${transactionData.selectedParcel}`;
      
      if (isOnline) {
        // Publish to marketplace
        await mockPublishToMarketplace();
        listingStatus = 'success';
        
        // Send SMS confirmation
        await mockSendSMS();
      } else {
        // Save offline
        await mockOfflineSave();
        listingStatus = 'offline';
      }
      
      currentStep = 3; // Go to confirmation step
    } catch (error) {
      console.error('Publishing failed:', error);
    } finally {
      isSubmitting = false;
    }
  }

  function mockPublishToMarketplace() {
    return new Promise(resolve => setTimeout(resolve, 2000));
  }

  function mockSendSMS() {
    return new Promise(resolve => setTimeout(resolve, 1000));
  }

  function mockOfflineSave() {
    return new Promise(resolve => setTimeout(resolve, 1000));
  }

  function backToDashboard() {
    goto('/dashboard');
  }

  function viewListing() {
    // In a real app, this would open the public listing page
    console.log('View listing:', listingUrl);
  }

  // Step validation
  function isStepValid(step: number): boolean {
    switch (step) {
      case 1:
        return transactionData.selectedParcel !== '';
      case 2:
        if (!transactionData.transactionType) return false;
        if (transactionData.transactionType === 'sale') {
          return transactionData.price !== '';
        } else {
          return transactionData.leaseRate !== '' && transactionData.leaseDuration !== '';
        }
      case 3:
        return true; // Confirmation step
      default:
        return false;
    }
  }

  function getStepTitle(step: number): string {
    const titles = {
      1: 'Select Parcel',
      2: 'Choose Transaction Type',
      3: 'Publish to Marketplace'
    };
    return titles[step] || '';
  }

  function getStepSubtitle(step: number): string {
    const subtitles = {
      1: 'Choose which verified parcel you want to sell or lease.',
      2: 'Set your price and terms for the transaction.',
      3: 'Your listing will be published to the LandLock Marketplace.'
    };
    return subtitles[step] || '';
  }

  function getSelectedParcel() {
    return verifiedParcels.find(p => p.id === transactionData.selectedParcel);
  }
</script>

<svelte:head>
  <title>Sell or Lease Land - LandLock</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</svelte:head>

<div class="sell-lease-land">
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
    <!-- Progress Bar -->
    <div class="progress-container">
      <div class="progress-bar">
        {#each Array(totalSteps) as _, i}
          <div 
            class="progress-step" 
            class:active={currentStep === i + 1}
            class:completed={currentStep > i + 1}
          >
            <div class="step-number">{i + 1}</div>
            <div class="step-label">Step {i + 1}</div>
          </div>
        {/each}
      </div>
    </div>

    <!-- Step Content -->
    <div class="step-container">
      <div class="step-header">
        <h1>{getStepTitle(currentStep)}</h1>
        <p class="step-subtitle">{getStepSubtitle(currentStep)}</p>
      </div>

      <!-- Step 1: Select Parcel -->
      {#if currentStep === 1}
        <div class="step-content">
          <div class="parcels-grid">
            {#each verifiedParcels as parcel (parcel.id)}
              <div 
                class="parcel-card" 
                class:selected={transactionData.selectedParcel === parcel.id}
                on:click={() => selectParcel(parcel.id)}
              >
                <div class="parcel-header">
                  <div class="parcel-id">{parcel.id}</div>
                  <div class="parcel-badge">✅ Verified</div>
                </div>
                <div class="parcel-details">
                  <div class="parcel-location">📍 {parcel.location}</div>
                  <div class="parcel-size">📏 {parcel.size} acres</div>
                </div>
                <div class="parcel-status">
                  <div class="status-tag verified">Verified by Government</div>
                </div>
              </div>
            {/each}
          </div>

          {#if verifiedParcels.length === 0}
            <div class="empty-state">
              <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
                <circle cx="32" cy="32" r="32" fill="#f0f4ff"/>
                <path d="M32 20L42 30H36V40H28V30H22L32 20Z" fill="#667eea" opacity="0.5"/>
              </svg>
              <h3>No Verified Parcels</h3>
              <p>You need verified parcels to sell or lease land.</p>
              <button class="btn btn-primary" on:click={() => goto('/register-land')}>
                Register Land First
              </button>
            </div>
          {/if}

          <div class="step-actions">
            <button class="btn btn-secondary" on:click={backToDashboard}>
              Cancel
            </button>
            <button 
              class="btn btn-primary" 
              on:click={nextStep}
              disabled={!isStepValid(1)}
            >
              Continue
              <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd"/>
              </svg>
            </button>
          </div>
        </div>
      {/if}

      <!-- Step 2: Choose Transaction Type -->
      {#if currentStep === 2}
        <div class="step-content">
          <div class="selected-parcel-info">
            <div class="parcel-summary">
              <div class="parcel-id">{getSelectedParcel()?.id}</div>
              <div class="parcel-details">
                <span>📍 {getSelectedParcel()?.location}</span>
                <span>📏 {getSelectedParcel()?.size} acres</span>
              </div>
            </div>
          </div>

          <div class="transaction-types">
            <!-- Sale Option -->
            <div 
              class="transaction-type" 
              class:selected={transactionData.transactionType === 'sale'}
              on:click={() => setTransactionType('sale')}
            >
              <div class="transaction-header">
                <div class="transaction-icon">💰</div>
                <div class="transaction-title">Sale</div>
              </div>
              <div class="transaction-fields">
                <div class="form-group">
                  <label class="form-label">Price (₵ Kwacha)</label>
                  <input 
                    type="text" 
                    class="form-input" 
                    bind:value={transactionData.price}
                    placeholder="e.g., 500000"
                    disabled={transactionData.transactionType !== 'sale'}
                  />
                </div>
                <div class="form-group">
                  <label class="form-label">Terms (optional)</label>
                  <textarea 
                    class="form-textarea" 
                    bind:value={transactionData.terms}
                    placeholder="Buyer must be from this village"
                    rows="3"
                    disabled={transactionData.transactionType !== 'sale'}
                  ></textarea>
                </div>
              </div>
            </div>

            <!-- Lease Option -->
            <div 
              class="transaction-type" 
              class:selected={transactionData.transactionType === 'lease'}
              on:click={() => setTransactionType('lease')}
            >
              <div class="transaction-header">
                <div class="transaction-icon">📄</div>
                <div class="transaction-title">Lease</div>
              </div>
              <div class="transaction-fields">
                <div class="form-group">
                  <label class="form-label">Rate</label>
                  <input 
                    type="text" 
                    class="form-input" 
                    bind:value={transactionData.leaseRate}
                    placeholder="e.g., 10000 per month"
                    disabled={transactionData.transactionType !== 'lease'}
                  />
                </div>
                <div class="form-group">
                  <label class="form-label">Duration</label>
                  <select 
                    class="form-select" 
                    bind:value={transactionData.leaseDuration}
                    disabled={transactionData.transactionType !== 'lease'}
                  >
                    <option value="">Select duration</option>
                    {#each leaseDurations as duration}
                      <option value={duration}>{duration}</option>
                    {/each}
                  </select>
                </div>
                <div class="form-group">
                  <label class="form-label">Terms (optional)</label>
                  <textarea 
                    class="form-textarea" 
                    bind:value={transactionData.terms}
                    placeholder="Includes farming rights"
                    rows="3"
                    disabled={transactionData.transactionType !== 'lease'}
                  ></textarea>
                </div>
              </div>
            </div>
          </div>

          <div class="step-actions">
            <button class="btn btn-secondary" on:click={prevStep}>
              <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clip-rule="evenodd"/>
              </svg>
              Back
            </button>
            <button 
              class="btn btn-primary" 
              on:click={nextStep}
              disabled={!isStepValid(2)}
            >
              Continue
              <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd"/>
              </svg>
            </button>
          </div>
        </div>
      {/if}

      <!-- Step 3: Publish to Marketplace -->
      {#if currentStep === 3}
        <div class="step-content">
          <div class="publish-section">
            <div class="listing-preview">
              <h3>Listing Preview</h3>
              <div class="preview-card">
                <div class="preview-header">
                  <div class="preview-id">{getSelectedParcel()?.id}</div>
                  <div class="preview-badge verified">✅ Verified by Government</div>
                </div>
                <div class="preview-details">
                  <div class="preview-location">📍 {getSelectedParcel()?.location}</div>
                  <div class="preview-size">📏 {getSelectedParcel()?.size} acres</div>
                  <div class="preview-price">
                    {#if transactionData.transactionType === 'sale'}
                      💰 ₵{transactionData.price}
                    {:else}
                      📄 ₵{transactionData.leaseRate} for {transactionData.leaseDuration}
                    {/if}
                  </div>
                </div>
                {#if transactionData.terms}
                  <div class="preview-terms">
                    <strong>Terms:</strong> {transactionData.terms}
                  </div>
                {/if}
              </div>
            </div>

            <div class="publish-info">
              <div class="info-card">
                <h4>🔒 Privacy & Security</h4>
                <ul>
                  <li>✅ Only verified owners can list</li>
                  <li>📱 Buyer contact via consent-based SMS</li>
                  <li>👁️ No personal info shown publicly</li>
                  <li>🏛️ Government-backed verification</li>
                </ul>
              </div>

              <div class="info-card">
                <h4>🌍 Public Listing URL</h4>
                <div class="url-display">
                  <code>{listingUrl || 'landlock.mw/listings/' + transactionData.selectedParcel}</code>
                </div>
                <p class="url-description">
                  Anyone can view this listing, even without an account.
                </p>
              </div>
            </div>

            <div class="publish-actions">
              <button 
                class="btn btn-primary btn-lg" 
                on:click={publishListing}
                disabled={isSubmitting}
              >
                {#if isSubmitting}
                  <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor" class="animate-spin">
                    <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd"/>
                  </svg>
                  Publishing...
                {:else}
                  🚀 List on LandLock Marketplace
                {/if}
              </button>
            </div>
          </div>
        </div>
      {/if}

      <!-- Confirmation Screen -->
      {#if currentStep === 3 && listingStatus !== 'idle'}
        <div class="confirmation-screen">
          <div class="confirmation-card">
            <div class="confirmation-icon">
              {#if listingStatus === 'success'}
                <div class="success-icon">
                  <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
                    <circle cx="32" cy="32" r="32" fill="#dcfce7"/>
                    <path d="M20 32L28 40L44 24" stroke="#16a34a" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </div>
              {:else if listingStatus === 'offline'}
                <div class="offline-icon">
                  <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
                    <circle cx="32" cy="32" r="32" fill="#fef3c7"/>
                    <path d="M32 20v12m0 8h.01" stroke="#d97706" stroke-width="4" stroke-linecap="round"/>
                  </svg>
                </div>
              {/if}
            </div>

            <h2>Your land is now listed!</h2>
            
            <div class="status-section">
              <div class="status-badge" class:success={listingStatus === 'success'} class:warning={listingStatus === 'offline'}>
                {#if listingStatus === 'success'}
                  🟢 Published to Marketplace
                {:else if listingStatus === 'offline'}
                  🟡 Saved offline (will publish when online)
                {/if}
              </div>
            </div>

            <div class="listing-url-section">
              <div class="url-label">Public Listing URL</div>
              <div class="url-value">
                <code>{listingUrl}</code>
                <button class="btn btn-sm btn-secondary" on:click={viewListing}>
                  View Listing
                </button>
              </div>
            </div>

            <div class="message-section">
              <div class="message-card">
                <div class="message-icon">📱</div>
                <div class="message-content">
                  <h4>SMS Sent</h4>
                  <p>"Your land is now listed! View it here: {listingUrl}"</p>
                </div>
              </div>
            </div>

            <div class="next-steps">
              <h4>What happens next?</h4>
              <ul>
                <li>👀 Buyers can view your public listing</li>
                <li>📞 Interested buyers request contact via SMS</li>
                <li>✅ You approve to share contact information</li>
                <li>🤝 Transaction workspace opens in dashboard</li>
                <li>🏛️ District officer approves final transfer</li>
              </ul>
            </div>

            <div class="step-actions">
              <button class="btn btn-secondary" on:click={() => goto('/dashboard')}>
                Back to Dashboard
              </button>
              <button class="btn btn-primary" on:click={viewListing}>
                View Public Listing
              </button>
            </div>
          </div>
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

  .sell-lease-land {
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
    max-width: 900px;
    margin: 0 auto;
    padding: 2rem;
    width: 100%;
    flex: 1;
  }

  /* Progress Bar */
  .progress-container {
    margin-bottom: 3rem;
  }

  .progress-bar {
    display: flex;
    justify-content: space-between;
    position: relative;
    max-width: 600px;
    margin: 0 auto;
  }

  .progress-bar::before {
    content: '';
    position: absolute;
    top: 20px;
    left: 0;
    right: 0;
    height: 2px;
    background: #e2e8f0;
    z-index: 0;
  }

  .progress-step {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
    position: relative;
    z-index: 1;
  }

  .step-number {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: #e2e8f0;
    color: #64748b;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
    font-size: 0.875rem;
    transition: all 0.3s;
  }

  .progress-step.active .step-number {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  }

  .progress-step.completed .step-number {
    background: #dcfce7;
    color: #16a34a;
  }

  .step-label {
    font-size: 0.75rem;
    color: #64748b;
    font-weight: 500;
  }

  .progress-step.active .step-label {
    color: #0f172a;
  }

  /* Step Container */
  .step-container {
    background: white;
    border-radius: 16px;
    border: 1px solid #e2e8f0;
    padding: 2.5rem;
    box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
  }

  .step-header {
    text-align: center;
    margin-bottom: 2rem;
  }

  .step-header h1 {
    font-size: 2rem;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 0.5rem;
  }

  .step-subtitle {
    color: #64748b;
    font-size: 1rem;
  }

  .step-content {
    min-height: 400px;
  }

  /* Parcels Grid */
  .parcels-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1.5rem;
    margin-bottom: 3rem;
  }

  .parcel-card {
    background: #f8fafc;
    border: 2px solid #e2e8f0;
    border-radius: 12px;
    padding: 1.5rem;
    cursor: pointer;
    transition: all 0.3s;
    position: relative;
  }

  .parcel-card:hover {
    border-color: #667eea;
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(102, 126, 234, 0.15);
  }

  .parcel-card.selected {
    border-color: #667eea;
    background: linear-gradient(to bottom, #f0f4ff, #f8fafc);
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
  }

  .parcel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }

  .parcel-id {
    font-size: 1.125rem;
    font-weight: 700;
    color: #0f172a;
  }

  .parcel-badge {
    font-size: 0.75rem;
    color: #16a34a;
    font-weight: 600;
  }

  .parcel-details {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    margin-bottom: 1rem;
  }

  .parcel-location,
  .parcel-size {
    color: #64748b;
    font-size: 0.9375rem;
  }

  .parcel-status {
    display: flex;
    justify-content: flex-end;
  }

  .status-tag {
    padding: 0.25rem 0.75rem;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
  }

  .status-tag.verified {
    background: #dcfce7;
    color: #166534;
  }

  /* Selected Parcel Info */
  .selected-parcel-info {
    background: #f8fafc;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 2rem;
    border: 1px solid #e2e8f0;
  }

  .parcel-summary {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .parcel-summary .parcel-id {
    font-size: 1.25rem;
    font-weight: 700;
    color: #0f172a;
  }

  .parcel-summary .parcel-details {
    display: flex;
    gap: 1rem;
    color: #64748b;
  }

  /* Transaction Types */
  .transaction-types {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
    gap: 2rem;
    margin-bottom: 3rem;
  }

  .transaction-type {
    background: #f8fafc;
    border: 2px solid #e2e8f0;
    border-radius: 12px;
    padding: 1.5rem;
    cursor: pointer;
    transition: all 0.3s;
  }

  .transaction-type:hover {
    border-color: #667eea;
  }

  .transaction-type.selected {
    border-color: #667eea;
    background: linear-gradient(to bottom, #f0f4ff, #f8fafc);
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
  }

  .transaction-header {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1.5rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid #e2e8f0;
  }

  .transaction-icon {
    font-size: 2rem;
  }

  .transaction-title {
    font-size: 1.25rem;
    font-weight: 700;
    color: #0f172a;
  }

  .transaction-fields {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  /* Form Styles */
  .form-group {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .form-label {
    font-size: 0.875rem;
    font-weight: 600;
    color: #0f172a;
    text-transform: uppercase;
    letter-spacing: 0.3px;
  }

  .form-input,
  .form-select,
  .form-textarea {
    padding: 0.75rem 1rem;
    border: 1.5px solid #e0e0e0;
    background: #fafafa;
    border-radius: 8px;
    font-size: 0.9375rem;
    transition: all 0.2s;
  }

  .form-input:focus,
  .form-select:focus,
  .form-textarea:focus {
    outline: none;
    border-color: #667eea;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    background: white;
  }

  .form-input:disabled,
  .form-select:disabled,
  .form-textarea:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .form-textarea {
    resize: vertical;
    min-height: 80px;
  }

  /* Publish Section */
  .publish-section {
    max-width: 700px;
    margin: 0 auto;
  }

  .listing-preview {
    margin-bottom: 2rem;
  }

  .listing-preview h3 {
    font-size: 1.25rem;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 1rem;
  }

  .preview-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1.5rem;
  }

  .preview-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }

  .preview-id {
    font-size: 1.125rem;
    font-weight: 700;
    color: #0f172a;
  }

  .preview-badge.verified {
    background: #dcfce7;
    color: #16a34a;
    padding: 0.25rem 0.75rem;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
  }

  .preview-details {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    margin-bottom: 1rem;
  }

  .preview-location,
  .preview-size,
  .preview-price {
    color: #64748b;
  }

  .preview-price {
    font-size: 1.125rem;
    font-weight: 700;
    color: #0f172a;
  }

  .preview-terms {
    padding: 1rem;
    background: white;
    border-radius: 8px;
    border: 1px solid #e2e8f0;
    font-size: 0.9375rem;
    color: #64748b;
  }

  .publish-info {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
  }

  .info-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1.5rem;
  }

  .info-card h4 {
    font-size: 1rem;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 1rem;
  }

  .info-card ul {
    list-style: none;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .info-card li {
    color: #64748b;
    font-size: 0.9375rem;
  }

  .url-display {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 0.5rem;
  }

  .url-display code {
    color: #667eea;
    font-family: 'Courier New', monospace;
    font-size: 0.875rem;
  }

  .url-description {
    color: #64748b;
    font-size: 0.875rem;
  }

  .publish-actions {
    text-align: center;
    margin-top: 2rem;
  }

  /* Confirmation Screen */
  .confirmation-screen {
    text-align: center;
  }

  .confirmation-card {
    max-width: 600px;
    margin: 0 auto;
    padding: 3rem 2rem;
  }

  .confirmation-icon {
    margin-bottom: 2rem;
  }

  .confirmation-card h2 {
    font-size: 1.5rem;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 1.5rem;
  }

  .status-section {
    margin-bottom: 2rem;
  }

  .status-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.5rem;
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.9375rem;
  }

  .status-badge.success {
    background: #dcfce7;
    color: #16a34a;
  }

  .status-badge.warning {
    background: #fef3c7;
    color: #d97706;
  }

  .listing-url-section {
    margin-bottom: 2rem;
  }

  .url-label {
    font-size: 0.875rem;
    color: #64748b;
    margin-bottom: 0.5rem;
  }

  .url-value {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    padding: 1rem;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
  }

  .url-value code {
    color: #667eea;
    font-family: 'Courier New', monospace;
    font-size: 0.875rem;
  }

  .message-section {
    margin-bottom: 2rem;
  }

  .message-card {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1.5rem;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    text-align: left;
  }

  .message-icon {
    font-size: 2rem;
  }

  .message-content h4 {
    font-weight: 600;
    color: #0f172a;
    margin-bottom: 0.5rem;
  }

  .message-content p {
    color: #64748b;
    font-size: 0.9375rem;
  }

  .next-steps {
    text-align: left;
    background: #f8fafc;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 2rem;
  }

  .next-steps h4 {
    font-weight: 600;
    color: #0f172a;
    margin-bottom: 1rem;
  }

  .next-steps ul {
    list-style: none;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .next-steps li {
    color: #64748b;
  }

  /* Empty State */
  .empty-state {
    text-align: center;
    padding: 3rem 2rem;
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
    background: linear-gradient(135deg, #1a472a 0%, #2d5a3d 100%);
    color: white;
  }

  .btn-primary:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(45, 90, 61, 0.4);
  }

  .btn-primary:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
  }

  .btn-secondary {
    background: white;
    color: #667eea;
    border: 1px solid #e2e8f0;
  }

  .btn-secondary:hover {
    background: #f8fafc;
  }

  .btn-lg {
    padding: 0.875rem 2rem;
    font-size: 1rem;
  }

  .btn-sm {
    padding: 0.5rem 1rem;
    font-size: 0.875rem;
  }

  .step-actions {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 3rem;
    gap: 1rem;
  }

  .step-actions .btn {
    min-width: 120px;
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

    .step-container {
      padding: 1.5rem;
    }

    .step-header h1 {
      font-size: 1.5rem;
    }

    .parcels-grid {
      grid-template-columns: 1fr;
    }

    .transaction-types {
      grid-template-columns: 1fr;
    }

    .publish-info {
      grid-template-columns: 1fr;
    }

    .step-actions {
      flex-direction: column;
    }

    .step-actions .btn {
      width: 100%;
      justify-content: center;
    }
  }
</style>
