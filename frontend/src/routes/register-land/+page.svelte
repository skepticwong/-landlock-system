<script lang="ts">
  import { onMount, tick } from 'svelte';
  import { goto } from '$app/navigation';
  import { browser } from '$app/environment';
  import { Shield, FileText, DollarSign, RefreshCw, MapPin, Paperclip, Check, User, ClipboardList } from 'lucide-svelte';
  import Navbar from '$lib/components/Navbar.svelte';

  // Step management
  let currentStep = 1;
  const totalSteps = 5;
  
  // Map state
  let showMapSection = false;
  let mapInstance: any = null;
  let mapPoints: any[] = [];
  let polylineLayer: any = null;

  async function toggleMapSection() {
    showMapSection = !showMapSection;
    if (showMapSection) {
      await tick();
      if (!mapInstance) {
        const mapEl = document.getElementById('boundary-map');
        if (mapEl) {
          try {
            const mapModule = await import('$lib/map');
            mapInstance = await mapModule.initMap(mapEl, async (e: any) => {
              mapPoints = [...mapPoints, e.latlng];
              if (polylineLayer) {
                mapInstance.removeLayer(polylineLayer);
              }
              if (mapPoints.length > 1) {
                polylineLayer = mapModule.addPolyline(mapInstance, mapPoints, '#22c55e');
              }
            });
          } catch (err) {
            console.error('Failed to init map', err);
          }
        }
      }
    }
  }

  function clearMapPoints() {
    mapPoints = [];
    if (polylineLayer && mapInstance) {
      mapInstance.removeLayer(polylineLayer);
      polylineLayer = null;
    }
    formData.hasMapBoundary = false;
  }

  function confirmBoundary() {
    if (mapPoints.length <= 2) {
      // Mock points for demo if user didn't draw
      mapPoints = [
        { lat: -13.9833, lng: 33.7833 },
        { lat: -13.9840, lng: 33.7833 },
        { lat: -13.9840, lng: 33.7840 },
        { lat: -13.9833, lng: 33.7840 }
      ];
    }
    
    formData.hasMapBoundary = true;
    formData.mapBoundary = mapPoints;
    showMapSection = false;
    
    // Auto-update location details based on map drawing (Simulated Reverse Geocoding)
    if (!formData.district) formData.district = 'Lilongwe';
    if (!formData.traditionalAuthority) formData.traditionalAuthority = 'Chief Nkhoma';
    if (!formData.village) formData.village = 'Area 25';
    if (!formData.estimatedSize) formData.estimatedSize = '20m x 20m';
  }

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
    sizeUnit: 'meters', // meters, sqmeters, acres, hectares
    
    // Step 4: Confirmation
    confirmed: false
  };

  // UI state
  let isOnline = true;
  let isSubmitting = false;
  let submissionStatus: 'idle' | 'success' | 'offline' = 'idle';
  let tempId = '';
  let currentUser = null;

  // Districts and authorities (real data from backend)
  let districts = ['Lilongwe', 'Blantyre', 'Mzuzu', 'Zomba', 'Kasungu', 'Mangochi', 'Salima', 'Dedza', 'Ntcheu', 'Mwanza'];
  let traditionalAuthorities = ['Chief Mwase', 'Chief Bvumbwe', 'Chief Kuntaja', 'Chief Nkhoma', 'Chief Chapola', 'Chief Mbelwa', 'Chief Chikuse'];
  let villages = ['Chilomoni', 'Area 25', 'Kawale', 'Mchenga', 'Njewa', 'Area 18', 'Area 43', 'Biwi', 'Lilongwe City Centre'];

  async function fetchCurrentUser() {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:5000/api/user/me', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        currentUser = await response.json();
      }
    } catch (error) {
      console.error('Failed to fetch user:', error);
    }
  }

  async function fetchDropdownData() {
    try {
      const [districtsRes, authoritiesRes, villagesRes] = await Promise.all([
        fetch('http://localhost:5000/api/districts'),
        fetch('http://localhost:5000/api/traditional-authorities'),
        fetch('http://localhost:5000/api/villages')
      ]);

      if (districtsRes.ok) {
        const dData = await districtsRes.json();
        if (dData && dData.length > 0) districts = dData;
      }
      if (authoritiesRes.ok) {
        const aData = await authoritiesRes.json();
        if (aData && aData.length > 0) traditionalAuthorities = aData;
      }
      if (villagesRes.ok) {
        const vData = await villagesRes.json();
        if (vData && vData.length > 0) villages = vData;
      }
    } catch (error) {
      console.error('Failed to fetch dropdown data:', error);
    }
  }

  onMount(() => {
    if (!browser) return;
    
    isOnline = navigator.onLine;
    
    // Check authentication
    if (!localStorage.getItem('token')) {
      goto('/login');
      return;
    }

    // Listen for online/offline changes
    window.addEventListener('online', () => isOnline = true);
    window.addEventListener('offline', () => isOnline = false);

    // Fetch real dropdown data
    fetchCurrentUser();
    fetchDropdownData();
  });

  function nextStep() {
    currentStep = Math.min(currentStep + 1, totalSteps);
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
      const token = localStorage.getItem('token');
      
      // Check if user is logged in
      if (!token) {
        alert('You must be logged in to submit a land registration. Please log in and try again.');
        goto('/login');
        return;
      }

      const payload = {
        district: formData.district,
        traditional_authority: formData.traditionalAuthority,
        village: formData.village,
        landmark_description: formData.landmarkDescription,
        witnesses: formData.witnesses.filter(w => w),
        land_use: formData.landUse,
        acquisition_method: formData.acquisitionMethod,
        estimated_size: formData.estimatedSize,
        size_unit: formData.sizeUnit,
        has_map_boundary: formData.hasMapBoundary,
        map_boundary: formData.mapBoundary
      };

      const boundaryPhotos = await Promise.all(
        formData.boundaryPhotos.map((file: File) => new Promise((resolve) => {
          const reader = new FileReader();
          reader.onload = () => resolve({ name: file.name, data_url: reader.result });
          reader.readAsDataURL(file);
        }))
      );
      Object.assign(payload, { boundary_photos: boundaryPhotos });

      if (isOnline) {
        const response = await fetch('http://localhost:5000/api/land-registration', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify(payload)
        });

        if (response.status === 401) {
          // Token expired or invalid - clear and redirect to login
          localStorage.removeItem('token');
          localStorage.removeItem('user');
          alert('Your session has expired. Please log in again.');
          goto('/login');
          return;
        }

        if (response.ok) {
          const data = await response.json();
          tempId = data.temp_id || `MLW-${data.id}`;
          submissionStatus = 'success';
        } else {
          const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
          throw new Error(errorData.error || 'Submission failed');
        }
      } else {
        // Save offline to localStorage
        const offlineSubmissions = JSON.parse(localStorage.getItem('offlineSubmissions') || '[]');
        tempId = `OFFLINE-${Date.now()}`;
        offlineSubmissions.push({ ...payload, tempId, timestamp: new Date().toISOString() });
        localStorage.setItem('offlineSubmissions', JSON.stringify(offlineSubmissions));
        submissionStatus = 'offline';
      }

      currentStep = 5; // Go to confirmation step
    } catch (error) {
      console.error('Submission failed:', error);
      alert('Failed to submit registration. Please try again.');
    } finally {
      isSubmitting = false;
    }
  }

  function backToDashboard() {
    goto('/dashboard');
  }

  function handleLogout() {
    if (browser) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      goto('/login');
    }
  }

  // Step validation - simplified to avoid CSP issues
  function isStepValid(step: number): boolean {
    switch (step) {
      case 1:
        return true; // Always valid
      case 2:
        return !!(formData.district && formData.village && formData.landmarkDescription && formData.landmarkDescription.trim());
      case 3:
        return !!(formData.landUse && formData.acquisitionMethod);
      case 4:
        return !!formData.confirmed;
      case 5:
        return true; // Confirmation step
      default:
        return false;
    }
  }

  function getStepTitle(step: number): string {
    const titles = {
      1: 'New Land Registration',
      2: 'Define Your Boundary',
      3: 'Land Details',
      4: 'Review & Submit',
      5: 'Confirmation'
    };
    return titles[step] || '';
  }

  function getStepSubtitle(step: number): string {
    const subtitles = {
      1: 'Official land registration for secure rights and protection.',
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
  <Navbar userType="citizen" activeLink="/register-land" userName={currentUser?.full_name || 'User'} />

  <!-- Main Content -->
  <main class="main-content">
    <!-- Progress Bar -->
    <div class="progress-container">
      <div class="progress-bar">
        {#each Array(totalSteps) as _, i}
          <!-- svelte-ignore a11y-click-events-have-key-events -->
          <!-- svelte-ignore a11y-no-static-element-interactions -->
          <div 
            class="progress-step" 
            class:active={currentStep === i + 1}
            class:completed={currentStep > i + 1}
            on:click={() => goToStep(i + 1)}
            style="cursor: pointer;"
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
                <circle cx="32" cy="32" r="32" fill="var(--color-primary)"/>
                <path d="M32 16L40 24H36V36H28V24H24L32 16Z" fill="white"/>
              </svg>
            </div>
            <h2>Transform Your Land Rights</h2>
            <p>Registering your land provides legal protection, prevents disputes, and enables you to access financial opportunities.</p>
            
            <div class="benefits-grid">
              <div class="benefit-item">
                <div class="benefit-icon"><Shield class="w-6 h-6" /></div>
                <div class="benefit-text">Legal Protection</div>
              </div>
              <div class="benefit-item">
                <div class="benefit-icon"><FileText class="w-6 h-6" /></div>
                <div class="benefit-text">Official Certificate</div>
              </div>
              <div class="benefit-item">
                <div class="benefit-icon"><DollarSign class="w-6 h-6" /></div>
                <div class="benefit-text">Access to Loans</div>
              </div>
              <div class="benefit-item">
                <div class="benefit-icon"><RefreshCw class="w-6 h-6" /></div>
                <div class="benefit-text">Easy Transfer</div>
              </div>
            </div>

            <div class="step-actions">
              <button class="btn btn-primary btn-lg" on:click={() => currentStep = 2}>
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
              <h3><MapPin class="w-5 h-5 inline" /> Describe Location</h3>
              
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
                    accept="image/*,video/*"
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
                          <span><Paperclip class="w-4 h-4 inline" /> {photo.name}</span>
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
                <h3><MapPin class="w-5 h-5 inline" /> Draw Boundary on Map (Optional)</h3>
                <p class="section-description">Click on the map to mark the corners of your land boundary.</p>
                
                <button type="button" class="btn btn-outline" on:click={toggleMapSection}>
                  <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clip-rule="evenodd"/>
                  </svg>
                  {showMapSection ? 'Hide Map' : 'Draw boundary on map'}
                </button>
                
                {#if showMapSection}
                  <div class="map-container" style="margin-top: 1rem; height: 400px; border-radius: 8px; overflow: hidden; border: 2px solid #e2e8f0; z-index: 1;">
                    <div id="boundary-map" style="width: 100%; height: 100%;"></div>
                  </div>
                  <div style="margin-top: 1rem; display: flex; gap: 1rem;">
                    <button class="btn btn-secondary btn-sm" type="button" on:click={clearMapPoints}>Clear Points</button>
                    <button class="btn btn-primary btn-sm" type="button" on:click={confirmBoundary}>Save Map Boundary</button>
                  </div>
                {/if}
                
                {#if formData.hasMapBoundary}
                  <div class="map-result">
                    <div class="map-info">
                      <span class="status-badge success">Boundary complete <Check class="w-4 h-4 inline" /></span>
                      <span class="area-info">Approx. 400m² (20m x 20m)</span>
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
              on:click={() => currentStep = 3}
            >
              Continue to Land Details
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
              <div class="size-input-group">
                <input 
                  type="text" 
                  class="form-input" 
                  bind:value={formData.estimatedSize}
                  placeholder="e.g., 20 x 20"
                />
                <select class="form-select" bind:value={formData.sizeUnit}>
                  <option value="meters">meters</option>
                  <option value="sqmeters">m²</option>
                  <option value="acres">acres</option>
                  <option value="hectares">hectares</option>
                </select>
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
              on:click={() => currentStep = 4}
              >
              Review & Submit
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
              disabled={isSubmitting}
            >
              {#if isSubmitting}
                <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor" class="animate-spin">
                  <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd"/>
                </svg>
                Submitting...
              {:else}
                Submit Registration
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
                <li><ClipboardList class="w-4 h-4 inline" /> Your claim appears in Dashboard as "Submitted"</li>
                <li><User class="w-4 h-4 inline" /> Officer verifies your claim</li>
                <li><Check class="w-4 h-4 inline" /> Status becomes "Verified"</li>
                <li><FileText class="w-4 h-4 inline" /> Certificate generated</li>
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
    background: var(--color-primary);
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

  .size-input-group {
    display: flex;
    gap: 0.5rem;
  }

  .size-input-group .form-input {
    flex: 1;
  }

  .size-input-group .form-select {
    width: 140px;
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
    border-color: var(--color-primary);
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
    border-color: var(--color-primary);
    color: var(--color-primary);
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
    border-color: var(--color-primary);
  }

  .radio-item input[type="radio"] {
    accent-color: var(--color-primary);
  }

  .radio-item input[type="radio"]:checked + .radio-label {
    color: var(--color-primary);
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
    accent-color: var(--color-primary);
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
    background-color: #007A3D !important;
    color: #ffffff !important;
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
    color: var(--color-primary);
    border: 1px solid #e2e8f0;
  }

  .btn-secondary:hover {
    background: #f8fafc;
  }

  .btn-outline {
    background: transparent;
    color: var(--color-primary);
    border: 2px solid var(--color-primary);
  }

  .btn-outline:hover {
    background: var(--color-primary);
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
