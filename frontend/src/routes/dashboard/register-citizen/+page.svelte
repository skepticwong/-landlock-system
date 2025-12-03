<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { status } from '$lib/store';

  let formData: {
    nationalId: string;
    fullName: string;
    phone: string;
    district: string;
    traditionalAuthority: string;
    village: string;
    relationshipToLand: string;
    additionalNotes: string;
    nidFrontPhoto: string | null;
    nidBackPhoto: string | null;
  } = {
    nationalId: '',
    fullName: '',
    phone: '',
    district: '',
    traditionalAuthority: '',
    village: '',
    relationshipToLand: '',
    additionalNotes: '',
    nidFrontPhoto: null,
    nidBackPhoto: null
  };

  let error = '';
  let isLoading = false;
  let generatedPin = '';
  let showSuccess = false;

  // Mock data for dropdowns - in production, this would come from API
  const districts = [
    { id: 'lilongwe', name: 'Lilongwe' },
    { id: 'blantyre', name: 'Blantyre' },
    { id: 'mzuzu', name: 'Mzuzu' },
    { id: 'zomba', name: 'Zomba' },
    { id: 'kasungu', name: 'Kasungu' }
  ];

  const traditionalAuthorities = {
    lilongwe: [
      { id: 'kapeni', name: 'TA Kapeni' },
      { id: 'jim', name: 'TA Jim' },
      { id: 'masumbankhunda', name: 'TA Masumbankhunda' }
    ],
    blantyre: [
      { id: 'chikowi', name: 'TA Chikowi' },
      { id: 'kuntaja', name: 'TA Kuntaja' },
      { id: 'machinjiri', name: 'TA Machinjiri' }
    ],
    mzuzu: [
      { id: 'mmbelwa', name: 'TA Mmbelwa' },
      { id: 'khosolo', name: 'TA Khosolo' }
    ],
    zomba: [
      { id: 'mwambo', name: 'TA Mwambo' },
      { id: 'malemia', name: 'TA Malemia' }
    ],
    kasungu: [
      { id: 'kawamba', name: 'TA Kawamba' },
      { id: 'mwanza', name: 'TA Mwanza' }
    ]
  };

  const villages = {
    'kapeni': [
      { id: 'chilomoni', name: 'Chilomoni' },
      { id: 'nsenga', name: 'Nsenga' },
      { id: 'matawale', name: 'Matawale' }
    ],
    'jim': [
      { id: 'area-1', name: 'Area 1' },
      { id: 'area-2', name: 'Area 2' }
    ],
    'masumbankhunda': [
      { id: 'city-center', name: 'City Center' },
      { id: 'biwi', name: 'Biwi' }
    ],
    'chikowi': [
      { id: 'limbe', name: 'Limbe' },
      { id: 'sigelege', name: 'Sigelege' }
    ],
    'kuntaja': [
      { id: 'naperi', name: 'Naperi' },
      { id: 'chigumula', name: 'Chigumula' }
    ],
    'machinjiri': [
      { id: 'machinjiri', name: 'Machinjiri' },
      { id: 'misesa', name: 'Misesa' }
    ]
  };

  let availableTAs: typeof traditionalAuthorities.lilongwe = [];
  let availableVillages: typeof villages.kapeni = [];

  function validateForm() {
    // National ID validation - exactly 12 digits
    if (!formData.nationalId || !/^\d{12}$/.test(formData.nationalId)) {
      error = 'National ID must be exactly 12 digits';
      return false;
    }

    // Full name validation
    if (!formData.fullName || formData.fullName.trim().length < 3) {
      error = 'Full name is required (no initials)';
      return false;
    }

    // Phone validation - Malawi format
    if (!formData.phone || !/^(265|0)\d{8,9}$/.test(formData.phone.replace(/\s/g, ''))) {
      error = 'Please enter a valid Malawi phone number';
      return false;
    }

    // Village validation
    if (!formData.district || !formData.traditionalAuthority || !formData.village) {
      error = 'Please select district, traditional authority, and village';
      return false;
    }

    // ID photos validation
    if (!formData.nidFrontPhoto || !formData.nidBackPhoto) {
      error = 'Both National ID photos are required';
      return false;
    }

    return true;
  }

  async function handleSubmit() {
    if (!validateForm()) {
      return;
    }

    error = '';
    isLoading = true;

    try {
      // Format phone number to standard format
      const formattedPhone = formData.phone.replace(/\s/g, '').replace(/^0/, '265');

      // Generate temporary 4-digit PIN
      generatedPin = Math.floor(1000 + Math.random() * 9000).toString();

      const payload = {
        national_id: formData.nationalId,
        full_name: formData.fullName,
        phone: formattedPhone,
        district: formData.district,
        traditional_authority: formData.traditionalAuthority,
        village: formData.village,
        relationship_to_land: formData.relationshipToLand,
        additional_notes: formData.additionalNotes,
        nid_front_photo: formData.nidFrontPhoto,
        nid_back_photo: formData.nidBackPhoto,
        temporary_pin: generatedPin,
        registered_by_officer: true
      };

      // TODO: Replace with actual API endpoint
      const response = await fetch('http://localhost:5000/api/auth/register-citizen', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(payload)
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Registration failed');
      }

      // Show success message
      showSuccess = true;
      status.set('Citizen registered successfully!');

      // Send SMS to citizen (in production, this would be handled by backend)
      console.log(`SMS sent to ${formattedPhone}: Welcome to LandLock! Your account is ready. Temporary PIN: ${generatedPin}. Change it on first login.`);

      // Reset form after 3 seconds
      setTimeout(() => {
        resetForm();
        showSuccess = false;
      }, 5000);

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      error = errorMessage;
      status.set('Registration failed: ' + errorMessage);
    } finally {
      isLoading = false;
    }
  }

  function handlePhotoUpload(event: Event, side: 'front' | 'back') {
    const target = event.target as HTMLInputElement;
    if (!target) return;
    const file = target.files?.[0];
    if (file) {
      // Validate file type and size
      if (!file.type.startsWith('image/')) {
        error = 'Please select an image file';
        return;
      }
      
      if (file.size > 5 * 1024 * 1024) { // 5MB limit
        error = 'Image file must be less than 5MB';
        return;
      }

      // Convert to base64 for upload
      const reader = new FileReader();
      reader.onload = (e: ProgressEvent<FileReader>) => {
        if (e.target?.result && typeof e.target.result === 'string') {
          if (side === 'front') {
            formData.nidFrontPhoto = e.target.result;
          } else {
            formData.nidBackPhoto = e.target.result;
          }
        }
      };
      reader.readAsDataURL(file);
    }
  }

  function resetForm() {
    formData = {
      nationalId: '',
      fullName: '',
      phone: '',
      district: '',
      traditionalAuthority: '',
      village: '',
      relationshipToLand: '',
      additionalNotes: '',
      nidFrontPhoto: null,
      nidBackPhoto: null
    };
    generatedPin = '';
    availableTAs = [];
    availableVillages = [];
  }

  function handleDistrictChange() {
    formData.traditionalAuthority = '';
    formData.village = '';
    availableTAs = traditionalAuthorities[formData.district as keyof typeof traditionalAuthorities] || [];
    availableVillages = [];
  }

  function handleTAChange() {
    formData.village = '';
    availableVillages = villages[formData.traditionalAuthority as keyof typeof villages] || [];
  }

  // Redirect to login if not authenticated
  onMount(() => {
    if (!localStorage.getItem('token')) {
      goto('/login');
      return;
    }
  });
</script>

<div class="register-container">
  <div class="register-card">
    <div class="header-section">
      <div class="back-button" on:click={() => goto('/dashboard')}>
        ← Back to Dashboard
      </div>
      <div class="title-section">
        <h1>Register New Citizen</h1>
        <p>Securely onboard citizens for LandLock registration</p>
      </div>
    </div>

    {#if showSuccess}
      <div class="success-message">
        <div class="success-icon">✅</div>
        <h3>Citizen Registered Successfully!</h3>
        <div class="pin-display">
          <strong>Temporary PIN:</strong> <span class="pin-number">{generatedPin}</span>
        </div>
        <p class="success-instructions">
          Please inform the citizen of their PIN. They will receive an SMS confirmation.
        </p>
      </div>
    {:else}
      {#if error}
        <div class="error-message">
          {error}
        </div>
      {/if}

      <form on:submit|preventDefault={handleSubmit}>
        <!-- National ID Number -->
        <div class="form-group">
          <label for="nationalId">National ID Number</label>
          <input
            id="nationalId"
            type="text"
            placeholder="123456789012"
            maxlength="12"
            pattern="\d{12}"
            bind:value={formData.nationalId}
            disabled={isLoading}
          />
          <div class="field-hint">Must be exactly 12 digits</div>
        </div>

        <!-- Full Name -->
        <div class="form-group">
          <label for="fullName">Full Name</label>
          <input
            id="fullName"
            type="text"
            placeholder="Grace Banda"
            bind:value={formData.fullName}
            disabled={isLoading}
          />
          <div class="field-hint">Enter exactly as written on National ID (no nicknames, no initials)</div>
        </div>

        <!-- Phone Number -->
        <div class="form-group">
          <label for="phone">Phone Number</label>
          <input
            id="phone"
            type="tel"
            placeholder="265888123456 or 0888123456"
            bind:value={formData.phone}
            disabled={isLoading}
          />
          <div class="field-hint">Ask citizen to show their SIM (SIM registration requires NID)</div>
        </div>

        <!-- Village Selection -->
        <div class="form-group">
          <label>Village Location</label>
          <div class="location-selects">
            <select bind:value={formData.district} on:change={handleDistrictChange} disabled={isLoading}>
              <option value="">Select District</option>
              {#each districts as district}
                <option value={district.id}>{district.name}</option>
              {/each}
            </select>

            <select bind:value={formData.traditionalAuthority} on:change={handleTAChange} disabled={isLoading || !formData.district}>
              <option value="">Select Traditional Authority</option>
              {#each availableTAs as ta}
                <option value={ta.id}>{ta.name}</option>
              {/each}
            </select>

            <select bind:value={formData.village} disabled={isLoading || !formData.traditionalAuthority}>
              <option value="">Select Village</option>
              {#each availableVillages as village}
                <option value={village.id}>{village.name}</option>
              {/each}
            </select>
          </div>
          <div class="field-hint">Ensures citizen is registered in the correct jurisdiction</div>
        </div>

        <!-- National ID Photos -->
        <div class="form-group">
          <div class="section-label">National ID Photos</div>
          <div class="photo-upload-section">
            <div class="photo-upload-group">
              <label for="nidFront" class="photo-label">Front of National ID</label>
              <div class="photo-upload-area">
                <input
                  id="nidFront"
                  name="nidFront"
                  type="file"
                  accept="image/*"
                  capture="environment"
                  on:change={(e) => handlePhotoUpload(e, 'front')}
                  class="hidden"
                  disabled={isLoading}
                />
                <label for="nidFront" class="photo-upload-btn" class:disabled={isLoading}>
                  📷 Take Photo
                </label>
                {#if formData.nidFrontPhoto}
                  <span class="photo-success">✅ Front photo captured</span>
                {/if}
              </div>
              <div class="field-hint">ID number, name, photo, and expiry must be visible</div>
            </div>

            <div class="photo-upload-group">
              <label for="nidBack" class="photo-label">Back of National ID</label>
              <div class="photo-upload-area">
                <input
                  id="nidBack"
                  name="nidBack"
                  type="file"
                  accept="image/*"
                  capture="environment"
                  on:change={(e) => handlePhotoUpload(e, 'back')}
                  class="hidden"
                  disabled={isLoading}
                />
                <label for="nidBack" class="photo-upload-btn" class:disabled={isLoading}>
                  📷 Take Photo
                </label>
                {#if formData.nidBackPhoto}
                  <span class="photo-success">✅ Back photo captured</span>
                {/if}
              </div>
              <div class="field-hint">Barcode and security features must be visible</div>
            </div>
          </div>
        </div>

        <!-- Relationship to Land -->
        <div class="form-group">
          <label>Relationship to Land (Optional but Recommended)</label>
          <div class="radio-group">
            <label class="radio-option">
              <input type="radio" bind:group={formData.relationshipToLand} value="register_today" disabled={isLoading} />
              <span>This citizen will register land today</span>
            </label>
            <label class="radio-option">
              <input type="radio" bind:group={formData.relationshipToLand} value="followup_needed" disabled={isLoading} />
              <span>Follow-up needed for parcel verification</span>
            </label>
            <label class="radio-option">
              <input type="radio" bind:group={formData.relationshipToLand} value="no_land" disabled={isLoading} />
              <span>No land to register at this time</span>
            </label>
          </div>
        </div>

        <!-- Additional Notes -->
        <div class="form-group">
          <label for="additionalNotes">Additional Notes</label>
          <textarea
            id="additionalNotes"
            placeholder="e.g., Claims plot near mango tree in Chilomoni"
            bind:value={formData.additionalNotes}
            disabled={isLoading}
            rows="3"
          ></textarea>
        </div>

        <button type="submit" class="btn-register" disabled={isLoading}>
          {#if isLoading}
            <span class="btn-content">
              <span class="spinner"></span>
              Registering Citizen...
            </span>
          {:else}
            Register Citizen
          {/if}
        </button>
      </form>
    {/if}

    <div class="audit-notice">
      <h4>🛡️ Security & Audit Trail</h4>
      <ul>
        <li>Full audit log: Officer ID, timestamp, and device recorded</li>
        <li>No edits allowed: Once registered, NID and name cannot be changed</li>
        <li>Images immutable: Stored with write-once policy</li>
      </ul>
    </div>
  </div>
</div>

<style>
  .register-container {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(to bottom, #f0fdf4, #e6f7ee);
    padding: 1rem;
  }

  .register-card {
    background: white;
    border-radius: 16px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.1);
    padding: 2rem;
    width: 100%;
    max-width: 600px;
    max-height: 90vh;
    overflow-y: auto;
  }

  .header-section {
    margin-bottom: 2rem;
  }

  .back-button {
    color: #0d9488;
    cursor: pointer;
    font-weight: 600;
    margin-bottom: 1rem;
    transition: color 0.2s;
  }

  .back-button:hover {
    color: #0b7a71;
  }

  .title-section h1 {
    font-size: 1.75rem;
    font-weight: 700;
    background: linear-gradient(90deg, #0d9488, #0b7a71);
    background-clip: text;
    -webkit-background-clip: text;
    color: transparent;
    margin: 0.5rem 0;
  }

  .title-section p {
    color: #64748b;
    font-weight: 600;
  }

  .form-group {
    margin-bottom: 1.5rem;
  }

  label {
    display: block;
    font-weight: 600;
    font-size: 0.875rem;
    margin-bottom: 0.5rem;
    color: #334155;
  }

  input, select, textarea {
    width: 100%;
    padding: 0.875rem 1rem;
    border: 2px solid #e2e8f0;
    border-radius: 12px;
    font-size: 1rem;
    background: #f8fafc;
    transition: border-color 0.2s;
  }

  input:focus, select:focus, textarea:focus {
    outline: none;
    border-color: #0d9488;
    box-shadow: 0 0 0 3px rgba(13,148,136,0.15);
  }

  input:disabled, select:disabled, textarea:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .field-hint {
    font-size: 0.75rem;
    color: #64748b;
    margin-top: 0.25rem;
  }

  .section-label {
    display: block;
    font-weight: 600;
    font-size: 0.875rem;
    margin-bottom: 0.5rem;
    color: #334155;
  }

  .location-selects {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 0.75rem;
  }

  .photo-upload-section {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .photo-upload-group {
    border: 2px solid #e2e8f0;
    border-radius: 12px;
    padding: 1rem;
    background: #f8fafc;
  }

  .photo-label {
    font-weight: 600;
    font-size: 0.875rem;
    color: #334155;
    margin-bottom: 0.5rem;
  }

  .photo-upload-area {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .photo-upload-btn {
    padding: 0.5rem 1rem;
    background: #f1f5f9;
    color: #475569;
    border: 2px solid #e2e8f0;
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.875rem;
    cursor: pointer;
    transition: all 0.2s;
  }

  .photo-upload-btn:hover:not(.disabled) {
    background: #e2e8f0;
    border-color: #0d9488;
  }

  .photo-upload-btn.disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .photo-success {
    color: #059669;
    font-size: 0.875rem;
    font-weight: 500;
  }

  .radio-group {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .radio-option {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    cursor: pointer;
    padding: 0.5rem;
    border-radius: 8px;
    transition: background-color 0.2s;
  }

  .radio-option:hover {
    background: #f8fafc;
  }

  .radio-option input[type="radio"] {
    width: auto;
    margin: 0;
  }

  .error-message {
    background: #fee2e2;
    color: #991b1b;
    padding: 0.75rem;
    border-radius: 8px;
    font-size: 0.875rem;
    margin-bottom: 1.25rem;
    border: 1px solid #fecaca;
  }

  .success-message {
    background: #f0fdf4;
    color: #059669;
    padding: 1.5rem;
    border-radius: 12px;
    text-align: center;
    margin-bottom: 1.25rem;
    border: 2px solid #bbf7d0;
  }

  .success-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
  }

  .success-message h3 {
    margin: 0 0 1rem 0;
    font-size: 1.25rem;
    color: #059669;
  }

  .pin-display {
    background: white;
    padding: 1rem;
    border-radius: 8px;
    margin: 1rem 0;
    border: 1px solid #bbf7d0;
  }

  .pin-number {
    font-size: 1.5rem;
    font-weight: 700;
    color: #0d9488;
    letter-spacing: 0.1em;
  }

  .success-instructions {
    font-size: 0.875rem;
    margin: 0;
    opacity: 0.8;
  }

  .btn-register {
    width: 100%;
    padding: 1rem;
    background: linear-gradient(135deg, #0d9488, #0b7a71);
    color: white;
    border: none;
    border-radius: 12px;
    font-weight: 600;
    font-size: 1rem;
    cursor: pointer;
    box-shadow: 0 4px 10px rgba(13,148,136,0.3);
    transition: all 0.2s;
    margin-top: 1rem;
  }

  .btn-register:hover:not(:disabled) {
    background: linear-gradient(135deg, #0b7a71, #09615b);
    transform: translateY(-2px);
    box-shadow: 0 6px 14px rgba(13,148,136,0.4);
  }

  .btn-register:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
  }

  .btn-content {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
  }

  .spinner {
    width: 16px;
    height: 16px;
    border: 2px solid rgba(255,255,255,0.3);
    border-top: 2px solid white;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  .audit-notice {
    margin-top: 2rem;
    padding: 1rem;
    background: #f8fafc;
    border-radius: 8px;
    border: 1px solid #e2e8f0;
  }

  .audit-notice h4 {
    margin: 0 0 0.5rem 0;
    color: #334155;
    font-size: 0.875rem;
  }

  .audit-notice ul {
    margin: 0;
    padding-left: 1.25rem;
    font-size: 0.75rem;
    color: #64748b;
  }

  .audit-notice li {
    margin-bottom: 0.25rem;
  }

  /* Responsive adjustments */
  @media (max-width: 768px) {
    .register-card {
      padding: 1.5rem;
      margin: 0.5rem;
    }
    
    .location-selects {
      grid-template-columns: 1fr;
      gap: 0.5rem;
    }
    
    .photo-upload-area {
      flex-direction: column;
      align-items: stretch;
    }
  }
</style>
