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
    created_at: ''
  };
  let showUserMenu = false;
  let isLoading = true;
  let isEditing = false;
  let editData = { ...userData };

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
