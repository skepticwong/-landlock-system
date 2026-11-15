<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { browser } from '$app/environment';
  import { User, Mail, Phone, MapPin, Calendar, Shield, Edit, LogOut } from 'lucide-svelte';
  import Navbar from '$lib/components/Navbar.svelte';

  const API = 'http://localhost:5000';

  let userData = {
    username: '',
    full_name: '',
    email: '',
    phone: '',
    location: '',
    role: '',
    is_superuser: false,
    created_at: '',
    identity_status: 'unverified',
    identity_review_reason: ''
  };
  let showUserMenu = false;
  let isLoading = true;
  let isEditing = false;
  let editData = { ...userData };
  let nationalId = '';
  let frontIdImage: File | null = null;
  let backIdImage: File | null = null;
  let isSubmittingIdentity = false;
  let identityMessage = '';
  let identityError = '';

  function authHeaders() {
    return { 'Authorization': `Bearer ${localStorage.getItem('token')}` };
  }

  async function fetchUserData() {
    isLoading = true;
    try {
      const res = await fetch(`${API}/api/user/me`, { headers: authHeaders() });
      if (res.ok) {
        const data = await res.json();
        userData = data;
        editData = { ...data };
      } else {
        goto('/login');
      }
    } catch (err) {
      console.error('Error fetching user data:', err);
    } finally {
      isLoading = false;
    }
  }

  async function handleSave() {
    try {
      const res = await fetch(`${API}/api/user/me`, {
        method: 'PUT',
        headers: {
          ...authHeaders(),
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(editData)
      });
      if (res.ok) {
        userData = { ...editData };
        isEditing = false;
      }
    } catch (err) {
      console.error('Error updating profile:', err);
    }
  }

  async function submitIdentityDocuments() {
    if (!nationalId.trim() || !frontIdImage || !backIdImage) {
      identityError = 'Enter your National ID number and upload both sides of your ID.';
      identityMessage = '';
      return;
    }
    if (frontIdImage.size > 5 * 1024 * 1024 || backIdImage.size > 5 * 1024 * 1024) {
      identityError = 'Each ID image must be 5 MB or smaller.';
      identityMessage = '';
      return;
    }

    const body = new FormData();
    body.append('national_id', nationalId.trim());
    body.append('front', frontIdImage);
    body.append('back', backIdImage);
    identityError = '';
    identityMessage = '';
    isSubmittingIdentity = true;

    try {
      const response = await fetch(`${API}/api/user/me/identity-verification`, {
        method: 'POST',
        headers: authHeaders(),
        body
      });
      const result = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(result.error || 'Could not submit your ID.');

      identityMessage = result.message;
      nationalId = '';
      frontIdImage = null;
      backIdImage = null;
      await fetchUserData();
    } catch (err) {
      identityError = err instanceof Error ? err.message : 'Could not submit your ID.';
    } finally {
      isSubmittingIdentity = false;
    }
  }

  function handleLogout() {
    if (browser) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      goto('/login');
    }
  }

  onMount(() => {
    if (!browser) return;
    if (!localStorage.getItem('token')) {
      goto('/login');
      return;
    }
    fetchUserData();
  });

  function formatDate(dateString: string): string {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  }
</script>

<svelte:head>
  <title>Profile - LandLock</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</svelte:head>

<div class="profile-page">
  <!-- Navigation -->
  <Navbar 
    userType={userData.is_superuser ? 'official' : 'citizen'} 
    activeLink="/profile" 
    userName={userData.full_name || userData.username || 'User'} 
    showNotification={false} 
  />

  <!-- Main Content -->
  <main class="main-content">
    <div class="profile-container">
      <!-- Profile Header -->
      <div class="profile-header">
        <div class="profile-avatar">
          <span>{userData.full_name?.charAt(0).toUpperCase() || userData.username?.charAt(0).toUpperCase() || 'U'}</span>
        </div>
        <div class="profile-info">
          <h1>{userData.full_name || userData.username || 'User'}</h1>
          <p class="role-badge">
            <Shield class="w-4 h-4 inline" />
            {userData.is_superuser ? 'Official' : userData.role || 'Landowner'}
          </p>
          <p class="join-date">Member since {formatDate(userData.created_at)}</p>
        </div>
        <button class="btn btn-secondary" on:click={() => isEditing = !isEditing}>
          <Edit class="w-4 h-4 inline" />
          {isEditing ? 'Cancel' : 'Edit Profile'}
        </button>
      </div>

      <!-- Profile Details -->
      <div class="profile-details">
        <div class="detail-section">
          <h2>Personal Information</h2>
          <div class="detail-grid">
            <div class="detail-item">
              <label>Username</label>
              {#if isEditing}
                <input type="text" bind:value={editData.username} class="input-field" />
              {:else}
                <div class="detail-value">{userData.username || 'N/A'}</div>
              {/if}
            </div>
            <div class="detail-item">
              <label>Full Name</label>
              {#if isEditing}
                <input type="text" bind:value={editData.full_name} class="input-field" />
              {:else}
                <div class="detail-value">{userData.full_name || 'N/A'}</div>
              {/if}
            </div>
            <div class="detail-item">
              <label>Email</label>
              {#if isEditing}
                <input type="email" bind:value={editData.email} class="input-field" />
              {:else}
                <div class="detail-value">{userData.email || 'N/A'}</div>
              {/if}
            </div>
            <div class="detail-item">
              <label>Phone</label>
              {#if isEditing}
                <input type="tel" bind:value={editData.phone} class="input-field" />
              {:else}
                <div class="detail-value">{userData.phone || 'N/A'}</div>
              {/if}
            </div>
            <div class="detail-item">
              <label>Location</label>
              {#if isEditing}
                <input type="text" bind:value={editData.location} class="input-field" />
              {:else}
                <div class="detail-value">{userData.location || 'N/A'}</div>
              {/if}
            </div>
          </div>
          {#if isEditing}
            <div class="edit-actions">
              <button class="btn btn-primary" on:click={handleSave}>Save Changes</button>
              <button class="btn btn-secondary" on:click={() => { isEditing = false; editData = { ...userData }; }}>Cancel</button>
            </div>
          {/if}
        </div>

        <!-- Account Settings -->
        <div class="detail-section">
          <h2>Account Settings</h2>
          <div class="setting-item">
            <div class="setting-info">
              <h3>Account Status</h3>
              <p>Your account is active and in good standing</p>
            </div>
            <span class="badge badge-success">Active</span>
          </div>
          <div class="setting-item">
            <div class="setting-info">
              <h3>Role</h3>
              <p>{userData.is_superuser ? 'Official with administrative privileges' : 'Standard landowner account'}</p>
            </div>
            <span class="badge badge-info">{userData.is_superuser ? 'Official' : 'Landowner'}</span>
          </div>
        </div>

        {#if !userData.is_superuser}
          <section class="detail-section identity-section" aria-labelledby="identity-heading">
            <h2 id="identity-heading">Identity verification</h2>
            <div class="identity-status" class:verified={userData.identity_status === 'verified'}>
              <Shield class="w-5 h-5" />
              <div>
                <strong>
                  {userData.identity_status === 'verified'
                    ? 'Verified'
                    : userData.identity_status === 'pending'
                      ? 'Waiting for administrator review'
                      : userData.identity_status === 'rejected'
                        ? 'Not verified'
                        : 'Not verified'}
                </strong>
                <p>
                  {userData.identity_status === 'verified'
                    ? 'An administrator has approved your ID.'
                    : 'You can submit land claims while unverified. ID approval is required for sales, listings, and transfers.'}
                </p>
              </div>
            </div>
            {#if userData.identity_review_reason}
              <p class="identity-review-reason">Administrator note: {userData.identity_review_reason}</p>
            {/if}
            {#if userData.identity_status !== 'verified'}
              {#if identityError}<p class="identity-message error" role="alert">{identityError}</p>{/if}
              {#if identityMessage}<p class="identity-message success" role="status">{identityMessage}</p>{/if}
              <form class="identity-form" on:submit|preventDefault={submitIdentityDocuments}>
                <p class="identity-help">Upload clear images of the front and back of your National ID. Documents are encrypted and only administrators can review them.</p>
                <div class="form-group">
                  <label for="national-id">National ID number</label>
                  <input id="national-id" bind:value={nationalId} autocomplete="off" disabled={isSubmittingIdentity} />
                </div>
                <div class="id-upload-grid">
                  <div class="form-group">
                    <label for="id-front">Front of National ID</label>
                    <input id="id-front" type="file" accept="image/jpeg,image/png,image/webp" disabled={isSubmittingIdentity} on:change={(event) => { frontIdImage = (event.currentTarget as HTMLInputElement).files?.[0] || null; }} />
                    {#if frontIdImage}<small>{frontIdImage.name}</small>{/if}
                  </div>
                  <div class="form-group">
                    <label for="id-back">Back of National ID</label>
                    <input id="id-back" type="file" accept="image/jpeg,image/png,image/webp" disabled={isSubmittingIdentity} on:change={(event) => { backIdImage = (event.currentTarget as HTMLInputElement).files?.[0] || null; }} />
                    {#if backIdImage}<small>{backIdImage.name}</small>{/if}
                  </div>
                </div>
                <button class="btn btn-primary" type="submit" disabled={isSubmittingIdentity}>
                  {isSubmittingIdentity ? 'Submitting...' : userData.identity_status === 'pending' ? 'Replace ID submission' : 'Submit ID for review'}
                </button>
              </form>
            {/if}
          </section>
        {/if}
      </div>
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

  .profile-page {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  /* Main Content */
  .main-content {
    max-width: 1400px;
    margin: 0 auto;
    padding: 2rem;
    width: 100%;
    flex: 1;
  }

  .profile-container {
    max-width: 900px;
    margin: 0 auto;
  }

  /* Profile Header */
  .profile-header {
    background: white;
    border-radius: 12px;
    padding: 2rem;
    border: 1px solid #e2e8f0;
    display: flex;
    align-items: center;
    gap: 2rem;
    margin-bottom: 2rem;
  }

  .profile-avatar {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    background: linear-gradient(135deg, #007A3D, #005C2E);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2rem;
    font-weight: 700;
  }

  .profile-info {
    flex: 1;
  }

  .profile-info h1 {
    font-size: 1.875rem;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 0.5rem;
  }

  .role-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    background: #dcfce7;
    color: #166534;
    padding: 0.5rem 1rem;
    border-radius: 8px;
    font-size: 0.875rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
  }

  .join-date {
    color: #64748b;
    font-size: 0.9375rem;
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
    background: #007A3D;
    color: white;
  }

  .btn-primary:hover {
    transform: translateY(-1px);
    background: #005C2E;
    box-shadow: 0 4px 12px rgba(0, 122, 61, 0.25);
  }

  .btn-secondary {
    background: white;
    color: #007A3D;
    border: 1px solid #e2e8f0;
  }

  .btn-secondary:hover {
    background: #f8fafc;
  }

  /* Profile Details */
  .profile-details {
    display: flex;
    flex-direction: column;
    gap: 2rem;
  }

  .detail-section {
    background: white;
    border-radius: 12px;
    padding: 2rem;
    border: 1px solid #e2e8f0;
  }

  .detail-section h2 {
    font-size: 1.25rem;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 1.5rem;
  }

  .identity-status {
    display: flex;
    align-items: flex-start;
    gap: .75rem;
    padding: 1rem;
    border-radius: 8px;
    background: #fef3c7;
    color: #92400e;
  }

  .identity-status.verified {
    background: #dcfce7;
    color: #166534;
  }

  .identity-status p { margin-top: .25rem; }
  .identity-review-reason { margin-top: 1rem; color: #b91c1c; }
  .identity-form { margin-top: 1.25rem; }
  .identity-help { margin-bottom: 1rem; color: #64748b; }
  .id-upload-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem; margin-bottom: 1rem; }
  .id-upload-grid input { width: 100%; margin-top: .5rem; }
  .id-upload-grid small { display: block; margin-top: .35rem; color: #64748b; }
  .identity-message { margin: 1rem 0; font-weight: 600; }
  .identity-message.error { color: #b91c1c; }
  .identity-message.success { color: #166534; }

  .detail-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1.5rem;
  }

  .detail-item {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .detail-item label {
    font-size: 0.875rem;
    font-weight: 600;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .detail-value {
    font-size: 1rem;
    color: #0f172a;
    font-weight: 500;
  }

  .input-field {
    padding: 0.75rem 1rem;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    font-size: 1rem;
    font-family: inherit;
    transition: all 0.2s;
  }

  .input-field:focus {
    outline: none;
    border-color: #007A3D;
    box-shadow: 0 0 0 3px rgba(0, 122, 61, 0.1);
  }

  .edit-actions {
    display: flex;
    gap: 1rem;
    margin-top: 1.5rem;
  }

  /* Settings */
  .setting-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1.5rem 0;
    border-bottom: 1px solid #e2e8f0;
  }

  .setting-item:last-child {
    border-bottom: none;
  }

  .setting-info h3 {
    font-size: 1rem;
    font-weight: 600;
    color: #0f172a;
    margin-bottom: 0.25rem;
  }

  .setting-info p {
    font-size: 0.875rem;
    color: #64748b;
  }

  /* Badge */
  .badge {
    padding: 0.25rem 0.75rem;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    white-space: nowrap;
  }

  .badge-success {
    background: #dcfce7;
    color: #166534;
  }

  .badge-info {
    background: #dbeafe;
    color: #1e40af;
  }

  /* Responsive */
  @media (max-width: 768px) {
    .main-content {
      padding: 1rem;
    }

    .profile-header {
      flex-direction: column;
      text-align: center;
    }

    .detail-grid {
      grid-template-columns: 1fr;
    }

    .edit-actions {
      flex-direction: column;
    }
  }
</style>
