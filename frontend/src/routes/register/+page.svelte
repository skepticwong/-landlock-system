<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { status } from '$lib/store';

  let formData: {
    nationalId: string;
    fullName: string;
    phone: string;
    email: string;
    pin: string;
    confirmPin: string;
    language: 'en' | 'ny' | 'tum';
    nidFrontPhoto: string | null;
    nidBackPhoto: string | null;
  } = {
    nationalId: '',
    fullName: '',
    phone: '',
    email: '',
    pin: '',
    confirmPin: '',
    language: 'en',
    nidFrontPhoto: null,
    nidBackPhoto: null
  };

  let error = '';
  let isLoading = false;
  let isOnline = navigator.onLine;

  // Language options
  const languages = [
    { code: 'en', name: 'English' },
    { code: 'ny', name: 'Chichewa' },
    { code: 'tum', name: 'Tumbuka' }
  ];

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

    // Email validation
    if (!formData.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      error = 'Please enter a valid email address';
      return false;
    }

    // PIN validation - 4-6 digits
    if (!formData.pin || !/^\d{4,6}$/.test(formData.pin)) {
      error = 'PIN must be 4-6 digits';
      return false;
    }

    // PIN confirmation
    if (formData.pin !== formData.confirmPin) {
      error = 'PINs do not match';
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

      const payload = {
        national_id: formData.nationalId,
        full_name: formData.fullName,
        phone: formattedPhone,
        email: formData.email,
        pin: formData.pin,
        language: formData.language,
        nid_front_photo: formData.nidFrontPhoto,
        nid_back_photo: formData.nidBackPhoto
      };

      const response = await fetch('http://localhost:5000/api/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload)
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Registration failed');
      }

      // Store the token and user data
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('user', JSON.stringify(data.user));
      
      // Update the store
      status.set('Account created! You\'re logged in.');
      
      // Redirect to dashboard
      setTimeout(() => {
        goto('/dashboard');
      }, 1500);
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

  // Redirect to home if already logged in
  onMount(() => {
    if (localStorage.getItem('token')) {
      goto('/');
    }

    // Detect device language
    const browserLang = navigator.language.split('-')[0];
    if (browserLang === 'ny') formData.language = 'ny';
    else if (browserLang === 'tum') formData.language = 'tum';
    else formData.language = 'en';
  });
</script>

<div class="register-container">
  <div class="register-card">
    <div class="logo-section">
      <div class="logo-circle">🌍</div>
      <h1>LandLock</h1>
      <p>Create your secure account</p>
    </div>

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
        <div class="field-hint">Must match the name on your National ID</div>
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
        <div class="field-hint">Will be used for login (via PIN) and SMS alerts</div>
      </div>

      <!-- Email Address -->
      <div class="form-group">
        <label for="email">Email Address</label>
        <input
          id="email"
          type="email"
          placeholder="grace.banda@example.com"
          bind:value={formData.email}
          disabled={isLoading}
        />
        <div class="field-hint">For account recovery and notifications</div>
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
            <div class="field-hint">Must show ID number, name, photo, and expiry</div>
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
            <div class="field-hint">Must show barcode, signatures, and security features</div>
          </div>
        </div>
      </div>

      <!-- PIN -->
      <div class="form-group">
        <div class="section-label">Create PIN</div>
        <input
          id="pin"
          type="password"
          placeholder="1234"
          maxlength="6"
          pattern="\d{4,6}"
          bind:value={formData.pin}
          disabled={isLoading}
        />
        <div class="field-hint">Create a 4-6 digit PIN for login</div>
      </div>

      <div class="form-group">
        <label for="confirmPin">Confirm PIN</label>
        <input
          id="confirmPin"
          type="password"
          placeholder="1234"
          maxlength="6"
          pattern="\d{4,6}"
          bind:value={formData.confirmPin}
          disabled={isLoading}
        />
      </div>

      <!-- Language Preference -->
      <div class="form-group">
        <label for="language">Language Preference (Optional)</label>
        <select
          id="language"
          bind:value={formData.language}
          disabled={isLoading}
          class="select-input"
        >
          {#each languages as lang}
            <option value={lang.code}>{lang.name}</option>
          {/each}
        </select>
        <div class="field-hint">Default detected from device or English</div>
      </div>

      <button type="submit" class="btn-register" disabled={isLoading}>
        {#if isLoading}
          <span class="btn-content">
            <span class="spinner"></span>
            Creating Account...
          </span>
        {:else}
          Create Account
        {/if}
      </button>
    </form>

    <div class="footer-links">
      <a href="/login" on:click|preventDefault={() => goto('/login')}>
        Already have an account? <span class="login-link">Sign In</span>
      </a>
    </div>

    <div class="security-notice">
      <p>🔒 Your data is encrypted and secure. Account creation takes less than 2 minutes.</p>
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
    max-width: 480px;
    max-height: 90vh;
    overflow-y: auto;
  }

  .logo-section {
    text-align: center;
    margin-bottom: 2rem;
  }

  .logo-circle {
    width: 4rem;
    height: 4rem;
    border-radius: 1rem;
    background: linear-gradient(135deg, #0d9488, #0b7a71);
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 2rem;
    box-shadow: 0 4px 12px rgba(13,148,136,0.25);
    margin-bottom: 1rem;
  }

  h1 {
    font-size: 2rem;
    font-weight: 700;
    background: linear-gradient(90deg, #0d9488, #0b7a71);
    background-clip: text;
    -webkit-background-clip: text;
    color: transparent;
    margin: 0.5rem 0;
  }

  .logo-section p {
    color: #64748b;
    font-weight: 600;
  }

  .form-group {
    margin-bottom: 1.25rem;
  }

  label {
    display: block;
    font-weight: 600;
    font-size: 0.875rem;
    margin-bottom: 0.5rem;
    color: #334155;
  }

  input, .select-input {
    width: 100%;
    padding: 0.875rem 1rem;
    border: 2px solid #e2e8f0;
    border-radius: 12px;
    font-size: 1rem;
    background: #f8fafc;
    transition: border-color 0.2s;
  }

  input:focus, .select-input:focus {
    outline: none;
    border-color: #0d9488;
    box-shadow: 0 0 0 3px rgba(13,148,136,0.15);
  }

  input:disabled, .select-input:disabled {
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

  .error-message {
    background: #fee2e2;
    color: #991b1b;
    padding: 0.75rem;
    border-radius: 8px;
    font-size: 0.875rem;
    margin-bottom: 1.25rem;
    border: 1px solid #fecaca;
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

  .footer-links {
    text-align: center;
    margin-top: 1.5rem;
  }

  .footer-links a {
    color: #4b5563;
    text-decoration: none;
    font-weight: 500;
    font-size: 0.9rem;
    transition: color 0.2s ease;
  }

  .footer-links a:hover {
    color: #10b981;
  }

  .login-link {
    color: #10b981;
    font-weight: 600;
    margin-left: 0.25rem;
  }
  
  .footer-links a:hover .login-link {
    text-decoration: underline;
  }

  .security-notice {
    text-align: center;
    margin-top: 1rem;
    padding: 0.75rem;
    background: #f0fdf4;
    border-radius: 8px;
    border: 1px solid #bbf7d0;
  }

  .security-notice p {
    font-size: 0.75rem;
    color: #059669;
    margin: 0;
  }

  /* Responsive adjustments */
  @media (max-width: 640px) {
    .register-card {
      padding: 1.5rem;
      margin: 0.5rem;
    }
    
    .photo-upload-area {
      flex-direction: column;
      align-items: stretch;
    }
  }
</style>