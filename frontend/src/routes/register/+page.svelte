<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { status } from '$lib/store';
  import { Globe, Camera, Check, Lock } from 'lucide-svelte';
  let formData: {
    nationalId: string;
    fullName: string;
    phone: string;
    email: string;
    password: string;
    confirmPassword: string;
    language: 'en' | 'ny' | 'tum';
    nidFrontPhoto: string | null;
    nidBackPhoto: string | null;
  } = {
    nationalId: '',
    fullName: '',
    phone: '',
    email: '',
    password: '',
    confirmPassword: '',
    language: 'en',
    nidFrontPhoto: null,
    nidBackPhoto: null
  };
  let error = '';
  let isLoading = false;
  let isOnline = true;
  let currentStep = 1;
  const stepTitles = ['Identity', 'Contact', 'National ID Photos', 'Create Password'];
  // Language options
  const languages = [
    { code: 'en', name: 'English' },
    { code: 'ny', name: 'Chichewa' },
    { code: 'tum', name: 'Tumbuka' }
  ];
  function validateForm() {
    // National ID validation - extremely permissive, just check length
    const nid = formData.nationalId.trim();
    if (!nid || nid.length < 1) {
      error = 'Please enter your National ID Number';
      return false;
    }
    formData.nationalId = nid.toUpperCase(); // Store cleaned version
    // Full name validation
    if (!formData.fullName || formData.fullName.trim().length < 3) {
      error = 'Full name is required (no initials)';
      return false;
    }
    // Phone validation - Malawi format (starting with 0)
    if (!formData.phone || !/^0\d{9}$/.test(formData.phone.replace(/\s/g, ''))) {
      error = 'Please enter a valid Malawi phone number starting with 0';
      return false;
    }
    // Email validation
    if (!formData.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      error = 'Please enter a valid email address';
      return false;
    }
    if (!formData.password || formData.password.length < 8) {
      error = 'Password must be at least 8 characters';
      return false;
    }
    if (formData.password !== formData.confirmPassword) {
      error = 'Passwords do not match';
      return false;
    }
    // ID photos validation
    if (!formData.nidFrontPhoto || !formData.nidBackPhoto) {
      error = 'Both National ID photos are required';
      return false;
    }
    return true;
  }

  function validateStep() {
    error = '';

    if (currentStep === 1) {
      if (!formData.nationalId.trim()) {
        error = 'Please enter your National ID Number';
        return false;
      }
      if (!formData.fullName.trim() || formData.fullName.trim().length < 3) {
        error = 'Full name is required (no initials)';
        return false;
      }
    } else if (currentStep === 2) {
      if (!/^0\d{9}$/.test(formData.phone.replace(/\s/g, ''))) {
        error = 'Please enter a valid Malawi phone number starting with 0';
        return false;
      }
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
        error = 'Please enter a valid email address';
        return false;
      }
    } else if (currentStep === 3 && (!formData.nidFrontPhoto || !formData.nidBackPhoto)) {
      error = 'Both National ID photos are required';
      return false;
    } else if (currentStep === 4) {
      if (formData.password.length < 8) {
        error = 'Password must be at least 8 characters';
        return false;
      }
      if (formData.password !== formData.confirmPassword) {
        error = 'Passwords do not match';
        return false;
      }
    }

    return true;
  }

  function nextStep() {
    if (!validateStep()) return;
    if (currentStep < 4) {
      currentStep += 1;
    }
  }

  function previousStep() {
    error = '';
    if (currentStep > 1) currentStep -= 1;
  }
  async function handleSubmit() {
    if (!validateForm()) {
      return;
    }
    error = '';
    isLoading = true;
    try {
      // Format phone number (remove spaces)
      const formattedPhone = formData.phone.replace(/\s/g, '');
      const payload = {
        national_id: formData.nationalId,
        full_name: formData.fullName,
        phone: formattedPhone,
        email: formData.email,
        password: formData.password,
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
  onMount(() => {
    isOnline = navigator.onLine;
    // Detect device language
    const browserLang = navigator.language.split('-')[0];
    if (browserLang === 'ny') formData.language = 'ny';
    else if (browserLang === 'tum') formData.language = 'tum';
    else formData.language = 'en';
  });
</script>

<svelte:head>
  <title>Create Account - LandLock</title>
</svelte:head>

<div class="register-container">
  <div class="register-shell">
    <!-- Form side -->
    <div class="form-panel">
      <div class="register-card">
        <div class="logo-section">
          <div class="logo-circle">
            <img src="/images/Coat_of_arms_of_Malawi.svg" alt="LandLock Logo" class="logo-image" />
          </div>
          <div>
            <h1>Account Creation</h1>
            <p>Secure your identity on the Land Registry</p>
          </div>
        </div>

        <form on:submit|preventDefault={handleSubmit}>
          <div class="wizard-progress" aria-label="Registration progress">
            <div class="wizard-progress-text">
              Step {currentStep} of 4 <span>{stepTitles[currentStep - 1]}</span>
            </div>
            <div class="wizard-progress-track">
              <span style={`width: ${(currentStep / 4) * 100}%`}></span>
            </div>
            <div class="wizard-steps">
              {#each stepTitles as title, index}
                <div
                  class:active={currentStep === index + 1}
                  class:complete={currentStep > index + 1}
                  aria-current={currentStep === index + 1 ? 'step' : undefined}
                >
                  <span>{index + 1}</span>
                  <small>{title}</small>
                </div>
              {/each}
            </div>
          </div>

          <!-- 1 · Identity -->
          {#if currentStep === 1}
          <fieldset class="form-section">
            <legend><span class="step-num">1</span> Identity</legend>

            <div class="form-group">
              <label for="nationalId">National ID Number</label>
              <input
                id="nationalId"
                type="text"
                placeholder="e.g. 8Z7X5Y2W"
                maxlength="32"
                autocomplete="off"
                bind:value={formData.nationalId}
                disabled={isLoading}
              />
              <div class="field-hint">Enter your ID exactly as it appears on your card</div>
            </div>

            <div class="form-group">
              <label for="fullName">Full Name</label>
              <input
                id="fullName"
                type="text"
                placeholder="Grace Banda"
                autocomplete="name"
                bind:value={formData.fullName}
                disabled={isLoading}
              />
              <div class="field-hint">Must match the name on your National ID</div>
            </div>
          </fieldset>
          {/if}

          <!-- 2 · Contact -->
          {#if currentStep === 2}
          <fieldset class="form-section">
            <legend><span class="step-num">2</span> Contact</legend>

            <div class="form-group">
              <label for="phone">Phone Number</label>
              <input
                id="phone"
                type="tel"
                placeholder="0888123456"
                autocomplete="tel"
                bind:value={formData.phone}
                disabled={isLoading}
              />
              <div class="field-hint">Will be used for login and SMS alerts</div>
            </div>

            <div class="form-group">
              <label for="email">Email Address</label>
              <input
                id="email"
                type="email"
                placeholder="grace.banda@example.com"
                autocomplete="email"
                bind:value={formData.email}
                disabled={isLoading}
              />
              <div class="field-hint">For account recovery and notifications</div>
            </div>

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
          </fieldset>
          {/if}

          <!-- 3 · ID photos -->
          {#if currentStep === 3}
          <fieldset class="form-section">
            <legend><span class="step-num">3</span> National ID Photos</legend>

            <div class="photo-upload-section">
              <div class="photo-upload-group" class:done={formData.nidFrontPhoto}>
                <div class="photo-label">Front of National ID</div>
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
                    <Camera size={16} /> Take Photo
                  </label>
                  {#if formData.nidFrontPhoto}
                    <span class="photo-success"><Check size={16} /> Front photo captured</span>
                  {/if}
                </div>
                <div class="field-hint">Must show ID number, name, photo, and expiry</div>
              </div>

              <div class="photo-upload-group" class:done={formData.nidBackPhoto}>
                <div class="photo-label">Back of National ID</div>
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
                    <Camera size={16} /> Take Photo
                  </label>
                  {#if formData.nidBackPhoto}
                    <span class="photo-success"><Check size={16} /> Back photo captured</span>
                  {/if}
                </div>
                <div class="field-hint">Must show barcode, signatures, and security features</div>
              </div>
            </div>
          </fieldset>
          {/if}

          <!-- 4 · Password -->
          {#if currentStep === 4}
          <fieldset class="form-section">
            <legend><span class="step-num">4</span> Create Password</legend>

            <div class="form-row">
              <div class="form-group">
                <label for="password">Password</label>
                <input
                  id="password"
                  type="password"
                  autocomplete="new-password"
                  placeholder="At least 8 characters"
                  minlength="8"
                  bind:value={formData.password}
                  disabled={isLoading}
                />
              </div>

              <div class="form-group">
                <label for="confirm-password">Confirm Password</label>
                <input
                  id="confirm-password"
                  type="password"
                  autocomplete="new-password"
                  placeholder="Enter password again"
                  minlength="8"
                  bind:value={formData.confirmPassword}
                  disabled={isLoading}
                />
              </div>
            </div>
            <div class="field-hint hint-tight">Create a password with at least 8 characters</div>
          </fieldset>
          {/if}

          <div class="form-actions">
            {#if error}
              <div class="error-message" role="alert">{error}</div>
            {/if}

            <div class="wizard-actions">
              {#if currentStep > 1}
                <button type="button" class="btn-secondary" on:click={previousStep} disabled={isLoading}>
                  Back
                </button>
              {/if}

              {#if currentStep < 4}
                <button type="button" class="btn-register" on:click={nextStep} disabled={isLoading}>
                  Continue
                </button>
              {:else}
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
              {/if}
            </div>
          </div>
        </form>

        <div class="footer-links">
          <a href="/login" on:click|preventDefault={() => goto('/login')}>
            Already have an account? <span class="login-link">Sign In</span>
          </a>
        </div>

        <div class="security-notice">
          <Lock size={14} /> Your data is encrypted and secure. Takes less than 2 minutes.
        </div>
      </div>
    </div>

    <!-- Brand side -->
    <div class="brand-panel">
      <div class="flag-stripe" aria-hidden="true"><i></i><i></i><i></i></div>
      <div class="brand-inner">
        <div class="brand-logo-wrap">
          <img src="/images/Coat_of_arms_of_Malawi.svg" alt="LandLock Logo" class="brand-logo" />
        </div>
        <h2>LandLock</h2>
        <p>Secure Land Registry for Malawi</p>
        <ul class="brand-points">
          <li><Check size={18} />Verified, tamper-proof ownership records</li>
          <li><Check size={18} />Available in English, Chichewa and Tumbuka</li>
          <li><Check size={18} />SMS alerts on every change to your land</li>
        </ul>
      </div>
    </div>
  </div>
</div>

<style>
  /* ═══════════ Tokens (shared with the login page) ═══════════ */
  .register-container {
    --green: #007a3d;
    --green-dark: #005c2e;
    --ink: #0f172a;
    --text: #212529;
    --muted: #64748b;
    --line: #dee2e6;
    --field: #f8f9fa;
    --danger: #ce1126;
    --radius: 10px;
  }

  :global(body) {
    margin: 0;
    background-color: #edf4f1;
    background-image:
      linear-gradient(rgba(0, 122, 61, 0.22) 1px, transparent 1px),
      linear-gradient(to right, rgba(0, 122, 61, 0.22) 1px, #edf4f1 1px);
    background-size: 20px 20px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    color: #212529;
    line-height: 1.5;
  }

  /* ═══════════ Page: centers the card, page scrolls if ever needed ═══════════ */
  .register-container {
    min-height: 100dvh;
    display: grid;
    place-items: center;
    padding: 1rem;
    box-sizing: border-box;
  }

  .register-container *,
  .register-container *::before,
  .register-container *::after {
    box-sizing: border-box;
  }

  /* ═══════════ Card ═══════════ */
  .register-shell {
    display: flex;
    width: min(980px, 100%);
    height: min(760px, calc(100dvh - 2rem));
    background: #fff;
    border-radius: 20px;
    overflow: hidden; /* only for rounded corners; the form panel scrolls */
    box-shadow: 0 24px 70px rgba(15, 23, 42, 0.18);
  }

  /* ═══════════ Form panel (scrolls on its own) ═══════════ */
  .form-panel {
    flex: 1 1 54%;
    min-width: 0;
    display: flex;
    padding: 0 2.5rem;
    overflow-y: auto;
    scrollbar-width: thin;
  }

  .register-card {
    width: 100%;
    max-width: 440px;
    margin: auto; /* safe centering */
  }

  .logo-section {
    display: flex;
    align-items: center;
    gap: 0.9rem;
    padding-top: 2rem;
    margin-bottom: 1.5rem;
  }

  .logo-circle {
    width: 3.25rem;
    height: 3.25rem;
    flex-shrink: 0;
    display: grid;
    place-items: center;
    padding: 0.4rem;
    background: #fff;
    border: 1px solid var(--line);
    border-radius: 12px;
  }

  .logo-image {
    width: 100%;
    height: 100%;
    object-fit: contain;
  }

  h1 {
    margin: 0;
    font-size: 1.5rem;
    line-height: 1.2;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: var(--ink);
  }

  .logo-section p {
    margin: 0.15rem 0 0;
    font-size: 0.875rem;
    color: var(--muted);
  }

  .wizard-progress {
    margin-bottom: 1.5rem;
  }

  .wizard-progress-text {
    display: flex;
    justify-content: space-between;
    margin-bottom: 0.55rem;
    font-size: 0.75rem;
    font-weight: 700;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }

  .wizard-progress-text span {
    color: var(--green);
  }

  .wizard-progress-track {
    height: 4px;
    overflow: hidden;
    border-radius: 999px;
    background: #e9eeeb;
  }

  .wizard-progress-track span {
    display: block;
    height: 100%;
    border-radius: inherit;
    background: var(--green);
    transition: width 0.25s ease;
  }

  .wizard-steps {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    margin-top: 0.75rem;
  }

  .wizard-steps div {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.3rem;
    color: #a0a8b1;
    text-align: center;
  }

  .wizard-steps div span {
    width: 24px;
    height: 24px;
    display: grid;
    place-items: center;
    border: 1px solid #d9dedb;
    border-radius: 50%;
    background: #fff;
    font-size: 0.72rem;
    font-weight: 700;
  }

  .wizard-steps small {
    font-size: 0.65rem;
    line-height: 1.2;
  }

  .wizard-steps div.active,
  .wizard-steps div.complete {
    color: var(--green);
  }

  .wizard-steps div.active span {
    border-color: var(--green);
    box-shadow: 0 0 0 3px rgba(0, 122, 61, 0.12);
  }

  .wizard-steps div.complete span {
    border-color: var(--green);
    background: var(--green);
    color: #fff;
  }

  /* ═══════════ Sections ═══════════ */
  .form-section {
    border: 0;
    margin: 0 0 1.5rem;
    padding: 0;
    min-width: 0;
  }

  .form-section legend {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    width: 100%;
    margin-bottom: 0.9rem;
    padding: 0 0 0.6rem;
    border-bottom: 1px solid #eef1f4;
    font-size: 0.95rem;
    font-weight: 700;
    letter-spacing: -0.01em;
    color: var(--ink);
  }

  .step-num {
    width: 22px;
    height: 22px;
    display: inline-grid;
    place-items: center;
    border-radius: 50%;
    background: var(--green);
    color: #fff;
    font-size: 0.7rem;
    font-weight: 700;
  }

  /* ═══════════ Fields ═══════════ */
  .form-group {
    margin-bottom: 1rem;
  }

  .form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.75rem;
  }

  label {
    display: block;
    margin-bottom: 0.4rem;
    font-size: 0.8125rem;
    font-weight: 600;
    color: var(--text);
  }

  input,
  .select-input {
    width: 100%;
    padding: 0.7rem 0.9rem;
    border: 1.5px solid var(--line);
    border-radius: var(--radius);
    font: inherit;
    font-size: 0.95rem;
    background: var(--field);
    color: var(--text);
    transition: border-color 0.2s, box-shadow 0.2s, background 0.2s;
  }

  input::placeholder {
    color: #a0a8b1;
  }

  input:hover,
  .select-input:hover {
    border-color: #c4cbd2;
  }

  input:focus,
  .select-input:focus {
    outline: none;
    background: #fff;
    border-color: var(--green);
    box-shadow: 0 0 0 3px rgba(0, 122, 61, 0.15);
  }

  input:disabled,
  .select-input:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .select-input {
    appearance: none;
    padding-right: 2.5rem;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='none' stroke='%2364748b' stroke-width='2' stroke-linecap='round' stroke-linejoin='round' viewBox='0 0 24 24'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right 0.8rem center;
  }

  .field-hint {
    margin-top: 0.3rem;
    font-size: 0.75rem;
    color: #6c757d;
  }

  .hint-tight {
    margin-top: -0.4rem;
  }

  /* ═══════════ Photo upload ═══════════ */
  .photo-upload-section {
    display: flex;
    flex-direction: column;
    gap: 0.85rem;
  }

  .photo-upload-group {
    padding: 0.9rem;
    border: 1.5px dashed #c4cbd2;
    border-radius: 12px;
    background: var(--field);
    transition: border-color 0.2s, background 0.2s;
  }

  .photo-upload-group:hover {
    border-color: var(--green);
    background: #f3faf6;
  }

  .photo-upload-group.done {
    border-style: solid;
    border-color: var(--green);
    background: #f3faf6;
  }

  .photo-label {
    margin-bottom: 0.6rem;
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--text);
  }

  .photo-upload-area {
    position: relative;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    flex-wrap: wrap;
  }

  /* The real file input stays focusable but is visually hidden; its label is the button. */
  .photo-upload-area input.hidden {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0 0 0 0);
    white-space: nowrap;
    border: 0;
  }

  .photo-upload-btn {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    margin: 0;
    padding: 0.5rem 0.9rem;
    border: 1px solid var(--green);
    border-radius: 8px;
    background: #fff;
    color: var(--green);
    font-weight: 600;
    font-size: 0.85rem;
    cursor: pointer;
    transition: background 0.2s, color 0.2s;
  }

  .photo-upload-btn:hover:not(.disabled) {
    background: var(--green);
    color: #fff;
  }

  input.hidden:focus-visible + .photo-upload-btn {
    outline: 3px solid rgba(0, 122, 61, 0.35);
    outline-offset: 2px;
  }

  .photo-upload-btn.disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .photo-success {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    color: var(--green);
    font-size: 0.85rem;
    font-weight: 600;
  }

  /* ═══════════ Sticky footer: error + submit ═══════════ */
  .form-actions {
    position: sticky;
    bottom: 0;
    z-index: 5;
    padding: 1.1rem 0 0.85rem;
    background: linear-gradient(to bottom, rgba(255, 255, 255, 0), #fff 24%);
  }

  .error-message {
    margin-bottom: 0.75rem;
    padding: 0.7rem 0.85rem;
    border: 1px solid #fed7d7;
    border-left: 3px solid var(--danger);
    border-radius: var(--radius);
    background: #fff5f5;
    color: var(--danger);
    font-size: 0.85rem;
  }

  .btn-register {
    width: 100%;
    padding: 0.85rem;
    border: 0;
    border-radius: var(--radius);
    background: var(--green);
    color: #fff;
    font: inherit;
    font-weight: 600;
    font-size: 0.975rem;
    cursor: pointer;
    box-shadow: 0 4px 10px rgba(0, 122, 61, 0.2);
    transition: background 0.2s, transform 0.2s, box-shadow 0.2s;
  }

  .btn-register:hover:not(:disabled) {
    background: var(--green-dark);
    transform: translateY(-1px);
    box-shadow: 0 6px 14px rgba(0, 122, 61, 0.28);
  }

  .btn-register:focus-visible {
    outline: 3px solid rgba(0, 122, 61, 0.35);
    outline-offset: 2px;
  }

  .btn-register:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
  }

  .wizard-actions {
    display: grid;
    grid-template-columns: 1fr;
    gap: 0.75rem;
  }

  .wizard-actions:has(.btn-secondary) {
    grid-template-columns: 120px 1fr;
  }

  .btn-secondary {
    min-height: 46px;
    border: 1.5px solid var(--line);
    border-radius: var(--radius);
    background: #fff;
    color: var(--text);
    font: inherit;
    font-weight: 600;
    cursor: pointer;
  }

  .btn-secondary:hover:not(:disabled) {
    border-color: var(--green);
    color: var(--green);
  }

  .btn-secondary:disabled {
    opacity: 0.6;
    cursor: not-allowed;
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
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-top-color: #fff;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  /* ═══════════ Footer ═══════════ */
  .footer-links {
    text-align: center;
  }

  .footer-links a {
    color: #495057;
    text-decoration: none;
    font-weight: 500;
    font-size: 0.9rem;
  }

  .login-link {
    margin-left: 0.25rem;
    color: var(--green);
    font-weight: 600;
  }

  .footer-links a:hover .login-link {
    text-decoration: underline;
  }

  .security-notice {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.4rem;
    margin: 0.9rem 0 1.5rem;
    font-size: 0.75rem;
    color: var(--muted);
    text-align: center;
  }

  .security-notice :global(svg) {
    flex-shrink: 0;
    color: var(--green);
  }

  /* ═══════════ Brand panel ═══════════ */
  .brand-panel {
    flex: 1 1 46%;
    min-width: 0;
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 2rem;
    overflow: hidden;
    color: #fff;
    background:
      radial-gradient(120% 90% at 100% 0%, rgba(255, 255, 255, 0.14), transparent 55%),
      linear-gradient(160deg, #008a45 0%, #007a3d 45%, #005c2e 100%);
  }

  .brand-panel::before {
    content: "";
    position: absolute;
    top: -120px;
    right: -120px;
    width: 320px;
    height: 320px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.08);
  }

  .brand-panel::after {
    content: "";
    position: absolute;
    bottom: -160px;
    left: -80px;
    width: 380px;
    height: 380px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.06);
  }

  /* Malawi flag stripe: black / red / green */
  .flag-stripe {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 6px;
    display: flex;
    z-index: 2;
  }
  .flag-stripe i {
    flex: 1;
  }
  .flag-stripe i:nth-child(1) {
    background: #000;
  }
  .flag-stripe i:nth-child(2) {
    background: #ce1126;
  }
  .flag-stripe i:nth-child(3) {
    background: #339e35;
  }

  .brand-inner {
    position: relative;
    z-index: 1;
    max-width: 300px;
    text-align: center;
  }

  .brand-logo-wrap {
    width: 8.5rem;
    height: 8.5rem;
    margin: 0 auto 1.5rem;
    display: grid;
    place-items: center;
    padding: 1.1rem;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.96);
    box-shadow: 0 12px 32px rgba(0, 0, 0, 0.22), 0 0 0 10px rgba(255, 255, 255, 0.12);
  }

  .brand-logo {
    width: 100%;
    height: 100%;
    object-fit: contain;
  }

  .brand-inner h2 {
    margin: 0 0 0.4rem;
    font-size: 2.25rem;
    font-weight: 700;
    letter-spacing: -0.03em;
    color: #fff;
  }

  .brand-inner p {
    margin: 0;
    font-size: 1.05rem;
    font-weight: 500;
    color: rgba(255, 255, 255, 0.88);
  }

  .brand-points {
    list-style: none;
    margin: 2rem 0 0;
    padding: 1.25rem 0 0;
    border-top: 1px solid rgba(255, 255, 255, 0.22);
    display: grid;
    gap: 0.7rem;
    text-align: left;
    font-size: 0.875rem;
    color: rgba(255, 255, 255, 0.9);
  }

  .brand-points li {
    display: flex;
    gap: 0.6rem;
    align-items: center;
  }

  .brand-points :global(svg) {
    flex-shrink: 0;
    padding: 3px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.18);
  }

  /* ═══════════ Responsive ═══════════ */
  @media (max-width: 900px) {
    .brand-panel {
      display: none;
    }
    .register-shell {
      width: min(560px, 100%);
    }
    .form-panel {
      padding: 0 1.75rem;
    }
  }

  @media (max-width: 640px) {
    .register-container {
      padding: 0;
      background: #fff;
    }
    .register-shell {
      width: 100%;
      height: 100dvh;
      border-radius: 0;
      box-shadow: none;
    }
    .form-panel {
      padding: 0 1.25rem;
    }
    .logo-section {
      padding-top: 1.25rem;
    }
    .form-row {
      grid-template-columns: 1fr;
      gap: 0;
    }
    .hint-tight {
      margin-top: 0;
    }
    .photo-upload-area {
      flex-direction: column;
      align-items: stretch;
    }
    .photo-upload-btn {
      justify-content: center;
    }
    input,
    .select-input {
      font-size: 16px; /* stops iOS zoom on focus */
    }
  }

  @media (prefers-reduced-motion: reduce) {
    * {
      animation: none !important;
      transition: none !important;
    }
  }
</style>