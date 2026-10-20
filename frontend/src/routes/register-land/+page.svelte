<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { browser } from '$app/environment';

  // Step management
  let currentStep = 1;
  const totalSteps = 5;
  
  // Form data
  let formData = {
    // Step 2: Location
    district: '',
    traditionalAuthority: '',
    village: '',
    landmarkDescription: '',
    boundaryPhotos: [] as File[],
    witnesses: [''],
    hasMapBoundary: false,
    mapBoundary: null as any,
    
    // Step 3: Land Details
    landUse: '',
    acquisitionMethod: '',
    estimatedSize: '',
    
    // Step 4: Confirmation
    confirmed: false
  };

  // UI state
  let isOnline = navigator.onLine;
  let isSubmitting = false;
  let submissionStatus: 'idle' | 'success' | 'offline' = 'idle';
  let tempId = '';

  // Districts and authorities (mock data)
  const districts = ['Lilongwe', 'Blantyre', 'Mzuzu', 'Zomba', 'Kasungu'];
  const traditionalAuthorities = ['Chief Mwase', 'Chief Bvumbwe', 'Chief Kuntaja', 'Chief Nkhoma', 'Chief Chapola'];
  const villages = ['Chilomoni', 'Area 25', 'Kawale', 'Mchenga', 'Njewa'];

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

  function addWitness() {
    formData.witnesses.push('');
  }

  function removeWitness(index: number) {
    if (formData.witnesses.length > 1) {
      formData.witnesses.splice(index, 1);
    }
  }

  function handlePhotoUpload(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files) {
      formData.boundaryPhotos = Array.from(input.files);
    }
  }

  async function submitRegistration() {
    isSubmitting = true;
    
    try {
      // Generate temporary ID
      tempId = `MLW-TEMP-${Math.floor(Math.random() * 10000)}`;
      
      if (isOnline) {
        // Submit to server
        await mockServerSubmit();
        submissionStatus = 'success';
      } else {
        // Save offline
        await mockOfflineSave();
        submissionStatus = 'offline';
      }
      
      currentStep = 5; // Go to confirmation step
    } catch (error) {
      console.error('Submission failed:', error);
    } finally {
      isSubmitting = false;
    }
  }

  function mockServerSubmit() {
    return new Promise(resolve => setTimeout(resolve, 2000));
  }

  function mockOfflineSave() {
    return new Promise(resolve => setTimeout(resolve, 1000));
  }

  function backToDashboard() {
    goto('/dashboard');
  }

  // Step validation
  function isStepValid(step: number): boolean {
    switch (step) {
      case 1:
        return true; // Always valid
      case 2:
        return formData.district && formData.village && formData.landmarkDescription;
      case 3:
        return formData.landUse && formData.acquisitionMethod;
      case 4:
        return formData.confirmed;
      case 5:
        return true; // Confirmation step
      default:
        return false;
    }
  }

  function getStepTitle(step: number): string {
    const titles = {
      1: 'Register Your Land',
      2: 'Define Your Boundary',
      3: 'Land Details',
      4: 'Review & Submit',
      5: 'Confirmation'
    };
    return titles[step] || '';
  }

  function getStepSubtitle(step: number): string {
    const subtitles = {
      1: 'Turn your land into a government-recognized right.',
      2: 'Describe your land. You can use words, a map, or both.',
      3: 'Tell us about how you use and acquired this land.',
      4: 'Review your information before submitting.',
      5: 'Your land claim has been created successfully.'
    };
    return subtitles[step] || '';
  }
</script>

<svelte:head>
  <title>Register Land - LandLock</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</svelte:head>

<div class="register-land">
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
        <a href="/register-land" class="nav-link active">
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

      <!-- Step 1: Start -->
      {#if currentStep === 1}
        <div class="step-content">
          <div class="welcome-card">
            <div class="welcome-icon">
              <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
                <circle cx="32" cy="32" r="32" fill="url(#welcome-gradient)"/>
                <path d="M32 16L40 24H36V36H28V24H24L32 16Z" fill="white"/>
                <defs>
                  <linearGradient id="welcome-gradient" x1="0" y1="0" x2="64" y2="64">
                    <stop stop-color="#667eea"/>
                    <stop offset="1" stop-color="#764ba2"/>
                  </linearGradient>
                </defs>
              </svg>
            </div>
            <h2>Transform Your Land Rights</h2>
            <p>Registering your land provides legal protection, prevents disputes, and enables you to access financial opportunities.</p>
            
            <div class="benefits-grid">
              <div class="benefit-item">
                <div class="benefit-icon">🛡️</div>
                <div class="benefit-text">Legal Protection</div>
              </div>
              <div class="benefit-item">
                <div class="benefit-icon">📄</div>
                <div class="benefit-text">Official Certificate</div>
              </div>
              <div class="benefit-item">
                <div class="benefit-icon">💰</div>
                <div class="benefit-text">Access to Loans</div>
              </div>
              <div class="benefit-item">
                <div class="benefit-icon">🔄</div>
                <div class="benefit-text">Easy Transfer</div>
              </div>
            </div>

            <div class="step-actions">
              <button class="btn btn-primary btn-lg" on:click={nextStep}>
                Continue
                <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd"/>
                </svg>
              </button>
            </div>
          </div>
        </div>
      {/if}

      <!-- Step 2: Define Boundary -->
      {#if currentStep === 2}
        <div class="step-content">
          <div class="form-sections">
            <!-- Option A: Describe Location -->
            <div class="form-section">
              <h3>📍 Describe Location</h3>
              
              <div class="form-grid">
                <div class="form-group">
                  <label class="form-label">District</label>
                  <select class="form-select" bind:value={formData.district}>
                    <option value="">Select district</option>
                    {#each districts as district}
                      <option value={district}>{district}</option>
                    {/each}
                  </select>
                </div>

                <div class="form-group">
                  <label class="form-label">Traditional Authority</label>
                  <select class="form-select" bind:value={formData.traditionalAuthority}>
                    <option value="">Select authority</option>
                    {#each traditionalAuthorities as authority}
                      <option value={authority}>{authority}</option>
                    {/each}
                  </select>
                </div>

                <div class="form-group">
                  <label class="form-label">Village</label>
                  <select class="form-select" bind:value={formData.village}>
                    <option value="">Select village</option>
                    {#each villages as village}
                      <option value={village}>{village}</option>
                    {/each}
                  </select>
                </div>
              </div>

              <div class="form-group">
                <label class="form-label">Landmark Description</label>
                <textarea 
                  class="form-textarea" 
                  bind:value={formData.landmarkDescription}
                  placeholder="Next to the big mango tree, behind Banda's shop"
                  rows="3"
                ></textarea>
              </div>

              <div class="form-group">
                <label class="form-label">Photos</label>
                <div class="file-upload">
                  <input 
                    type="file" 
                    id="boundary-photos" 
                    multiple 
                    accept="image/*"
                    on:change={handlePhotoUpload}
                    class="file-input"
                  />
                  <label for="boundary-photos" class="file-label">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M9 16.2L4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4L9 16.2z"/>
                    </svg>
                    Add photos or sketch
                  </label>
                  {#if formData.boundaryPhotos.length > 0}
                    <div class="file-list">
                      {#each formData.boundaryPhotos as photo}
                        <div class="file-item">
                          <span>📎 {photo.name}</span>
                        </div>
                      {/each}
                    </div>
                  {/if}
                </div>
              </div>

              <div class="form-group">
                <label class="form-label">Witnesses</label>
                <div class="witnesses-list">
                  {#each formData.witnesses as witness, index}
                    <div class="witness-input">
                      <input 
                        type="tel" 
                        class="form-input" 
                        bind:value={formData.witnesses[index]}
                        placeholder="Witness phone number"
                      />
                      {#if formData.witnesses.length > 1}
                        <button 
                          type="button" 
                          class="btn btn-icon btn-danger"
                          on:click={() => removeWitness(index)}
                        >
                          <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                            <path d="M2 4h12M4 4v8a2 2 0 002 2h4a2 2 0 002-2V4M6 4V2a1 1 0 011-1h2a1 1 0 011 1v2"/>
                          </svg>
                        </button>
                      {/if}
                    </div>
                  {/each}
                  <button type="button" class="btn btn-secondary btn-sm" on:click={addWitness}>
                    + Add another witness
                  </button>
                </div>
                <p class="form-hint">Witnesses will receive SMS to confirm.</p>
              </div>
            </div>

            <!-- Option B: Draw on Map -->
            {#if isOnline}
              <div class="form-section">
                <h3>🗺️ Draw Boundary on Map (Optional)</h3>
                <p class="section-description">Click on the map to mark the corners of your land boundary.</p>
                
                <button class="btn btn-outline">
                  <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clip-rule="evenodd"/>
                  </svg>
                  Draw boundary on map
                </button>
                
                {#if formData.hasMapBoundary}
                  <div class="map-result">
                    <div class="map-info">
                      <span class="status-badge success">Boundary complete ✅</span>
                      <span class="area-info">Approx. 0.82 acres</span>
                    </div>
                  </div>
                {/if}
              </div>
            {/if}
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

      <!-- Step 3: Land Details -->
      {#if currentStep === 3}
        <div class="step-content">
          <div class="form-section">
            <h3>Land Information</h3>
            
            <div class="form-group">
              <label class="form-label">Land Use</label>
              <div class="radio-group">
                {#each ['Farm', 'Home', 'Business', 'Other'] as use}
                  <label class="radio-item">
                    <input 
                      type="radio" 
                      name="landUse" 
                      bind:group={formData.landUse} 
                      value={use}
                    />
                    <span class="radio-label">{use}</span>
                  </label>
                {/each}
              </div>
            </div>

            <div class="form-group">
              <label class="form-label">How you got it</label>
              <div class="radio-group">
                {#each ['Inherited', 'Bought', 'Chief-allocated', 'First-time'] as method}
                  <label class="radio-item">
                    <input 
                      type="radio" 
                      name="acquisitionMethod" 
                      bind:group={formData.acquisitionMethod} 
                      value={method}
                    />
                    <span class="radio-label">{method}</span>
                  </label>
                {/each}
              </div>
            </div>

            <div class="form-group">
              <label class="form-label">Size (optional)</label>
              <input 
                type="text" 
                class="form-input" 
                bind:value={formData.estimatedSize}
                placeholder="e.g., 0.8 acres (can be confirmed later)"
              />
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
              disabled={!isStepValid(3)}
            >
              Continue
              <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd"/>
              </svg>
            </button>
          </div>
        </div>
      {/if}

      <!-- Step 4: Review & Submit -->
      {#if currentStep === 4}
        <div class="step-content">
          <div class="review-section">
            <h3>Review Your Information</h3>
            
            <div class="review-grid">
              <div class="review-item">
                <div class="review-label">Location</div>
                <div class="review-value">
                  {formData.village}, {formData.district}
                </div>
              </div>
              
              <div class="review-item">
                <div class="review-label">Description</div>
                <div class="review-value">{formData.landmarkDescription}</div>
              </div>
              
              <div class="review-item">
                <div class="review-label">Witnesses</div>
                <div class="review-value">{formData.witnesses.filter(w => w).length}</div>
              </div>
              
              <div class="review-item">
                <div class="review-label">Map Boundary</div>
                <div class="review-value">
                  {formData.hasMapBoundary ? 'Yes' : 'No'}
                </div>
              </div>
              
              <div class="review-item">
                <div class="review-label">Land Use</div>
                <div class="review-value">{formData.landUse}</div>
              </div>
              
              <div class="review-item">
                <div class="review-label">Acquisition</div>
                <div class="review-value">{formData.acquisitionMethod}</div>
              </div>
            </div>

            <div class="confirmation-section">
              <label class="checkbox-item">
                <input 
                  type="checkbox" 
                  bind:checked={formData.confirmed}
                />
                <span class="checkbox-label">
                  I confirm this information is true and accurate.
                </span>
              </label>
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
              class="btn btn-primary btn-lg" 
              on:click={submitRegistration}
              disabled={!isStepValid(4) || isSubmitting}
            >
              {#if isSubmitting}
                <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor" class="animate-spin">
                  <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd"/>
                </svg>
                Submitting...
              {:else}
                Register Land
                <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd"/>
                </svg>
              {/if}
            </button>
          </div>
        </div>
      {/if}

      <!-- Step 5: Confirmation -->
      {#if currentStep === 5}
        <div class="step-content">
          <div class="confirmation-card">
            <div class="confirmation-icon">
              {#if submissionStatus === 'success'}
                <div class="success-icon">
                  <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
                    <circle cx="32" cy="32" r="32" fill="#dcfce7"/>
                    <path d="M20 32L28 40L44 24" stroke="#16a34a" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </div>
              {:else if submissionStatus === 'offline'}
                <div class="offline-icon">
                  <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
                    <circle cx="32" cy="32" r="32" fill="#fef3c7"/>
                    <path d="M32 20v12m0 8h.01" stroke="#d97706" stroke-width="4" stroke-linecap="round"/>
                  </svg>
                </div>
              {/if}
            </div>

            <h2>Your claim has been created</h2>
            
            <div class="status-section">
              <div class="status-badge" class:success={submissionStatus === 'success'} class:warning={submissionStatus === 'offline'}>
                {#if submissionStatus === 'success'}
                  🟢 Submitted (online)
                {:else if submissionStatus === 'offline'}
                  🟡 Saved offline (will submit when online)
                {/if}
              </div>
            </div>

            <div class="temp-id-section">
              <div class="temp-id-label">Temporary ID</div>
              <div class="temp-id-value">{tempId}</div>
            </div>

            <div class="message-section">
              <p>A land officer will contact you within 10 days to verify your claim.</p>
            </div>

            <div class="next-steps">
              <h4>What happens next?</h4>
              <ul>
                <li>📋 Your claim appears in Dashboard as "Submitted"</li>
                <li>👮 Officer verifies your claim</li>
                <li>✅ Status becomes "Verified"</li>
                <li>📄 Certificate generated</li>
              </ul>
            </div>

            <div class="step-actions">
              <button class="btn btn-primary btn-lg" on:click={backToDashboard}>
                Back to Dashboard
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

  .register-land {
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

  /* Welcome Card */
  .welcome-card {
    text-align: center;
    padding: 3rem 2rem;
  }

  .welcome-icon {
    margin-bottom: 2rem;
  }

  .welcome-card h2 {
    font-size: 1.5rem;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 1rem;
  }

  .welcome-card p {
    color: #64748b;
    margin-bottom: 2rem;
    max-width: 500px;
    margin-left: auto;
    margin-right: auto;
  }

  .benefits-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1.5rem;
    margin-bottom: 3rem;
  }

  .benefit-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.75rem;
    padding: 1.5rem;
    background: #f8fafc;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
  }

  .benefit-icon {
    font-size: 2rem;
  }

  .benefit-text {
    font-weight: 600;
    color: #0f172a;
  }

  /* Form Sections */
  .form-sections {
    display: flex;
    flex-direction: column;
    gap: 2rem;
  }

  .form-section {
    padding: 1.5rem;
    background: #f8fafc;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
  }

  .form-section h3 {
    font-size: 1.125rem;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 1.5rem;
  }

  .section-description {
    color: #64748b;
    margin-bottom: 1rem;
    font-size: 0.875rem;
  }

  .form-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1.5rem;
    margin-bottom: 1.5rem;
  }

  .form-group {
    margin-bottom: 1.5rem;
  }

  .form-label {
    display: block;
    font-size: 0.875rem;
    font-weight: 600;
    color: #0f172a;
    text-transform: uppercase;
    letter-spacing: 0.3px;
    margin-bottom: 0.5rem;
  }

  .form-input,
  .form-select,
  .form-textarea {
    width: 100%;
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

  .form-textarea {
    resize: vertical;
    min-height: 100px;
  }

  .form-hint {
    font-size: 0.8125rem;
    color: #64748b;
    margin-top: 0.5rem;
  }

  /* File Upload */
  .file-upload {
    position: relative;
  }

  .file-input {
    display: none;
  }

  .file-label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
    background: white;
    border: 2px dashed #e2e8f0;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s;
    font-weight: 500;
    color: #64748b;
  }

  .file-label:hover {
    border-color: #667eea;
    color: #667eea;
  }

  .file-list {
    margin-top: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .file-item {
    padding: 0.5rem 1rem;
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    font-size: 0.875rem;
    color: #0f172a;
  }

  /* Witnesses */
  .witnesses-list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .witness-input {
    display: flex;
    gap: 0.5rem;
  }

  .witness-input .form-input {
    flex: 1;
  }

  /* Radio Groups */
  .radio-group {
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
  }

  .radio-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
    background: white;
    border: 1.5px solid #e0e0e0;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s;
  }

  .radio-item:hover {
    border-color: #667eea;
  }

  .radio-item input[type="radio"] {
    accent-color: #667eea;
  }

  .radio-item input[type="radio"]:checked + .radio-label {
    color: #667eea;
    font-weight: 600;
  }

  .radio-label {
    font-weight: 500;
    color: #0f172a;
  }

  /* Review Section */
  .review-section {
    max-width: 600px;
    margin: 0 auto;
  }

  .review-grid {
    display: grid;
    gap: 1rem;
    margin-bottom: 2rem;
  }

  .review-item {
    display: flex;
    justify-content: space-between;
    padding: 1rem;
    background: #f8fafc;
    border-radius: 8px;
    border: 1px solid #e2e8f0;
  }

  .review-label {
    font-weight: 600;
    color: #64748b;
  }

  .review-value {
    font-weight: 500;
    color: #0f172a;
  }

  .confirmation-section {
    margin-bottom: 2rem;
  }

  .checkbox-item {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    padding: 1rem;
    background: #f8fafc;
    border-radius: 8px;
    border: 1px solid #e2e8f0;
    cursor: pointer;
  }

  .checkbox-item input[type="checkbox"] {
    accent-color: #667eea;
    margin-top: 2px;
  }

  .checkbox-label {
    font-weight: 500;
    color: #0f172a;
  }

  /* Confirmation Card */
  .confirmation-card {
    text-align: center;
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

  .temp-id-section {
    margin-bottom: 2rem;
  }

  .temp-id-label {
    font-size: 0.875rem;
    color: #64748b;
    margin-bottom: 0.25rem;
  }

  .temp-id-value {
    font-size: 1.25rem;
    font-weight: 700;
    color: #0f172a;
    font-family: 'Courier New', monospace;
  }

  .message-section {
    margin-bottom: 2rem;
  }

  .message-section p {
    color: #64748b;
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

  .btn-outline {
    background: transparent;
    color: #667eea;
    border: 2px solid #667eea;
  }

  .btn-outline:hover {
    background: #667eea;
    color: white;
  }

  .btn-danger {
    background: #ef4444;
    color: white;
  }

  .btn-icon {
    padding: 0.5rem;
    border-radius: 6px;
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

    .form-grid {
      grid-template-columns: 1fr;
    }

    .benefits-grid {
      grid-template-columns: repeat(2, 1fr);
    }

    .step-actions {
      flex-direction: column;
    }

    .step-actions .btn {
      width: 100%;
      justify-content: center;
    }
  }

  @media (max-width: 480px) {
    .benefits-grid {
      grid-template-columns: 1fr;
    }

    .radio-group {
      flex-direction: column;
    }

    .progress-bar {
      gap: 0.5rem;
    }

    .step-label {
      font-size: 0.625rem;
    }
  }
</style>
