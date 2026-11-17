<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import Navbar from '$lib/components/Navbar.svelte';

  const API = 'http://localhost:5000';
  const roles = ['citizen', 'chief', 'official', 'admin'] as const;
  type Role = typeof roles[number];
  type AdminUser = {
    id: number;
    username: string;
    full_name: string;
    email?: string | null;
    phone: string;
    role: string;
    is_superuser: boolean | number;
    admin_access: boolean | number;
    is_active: boolean | number;
    created_at?: string;
  };
  type CurrentUser = { id: number; full_name?: string; is_superuser: boolean };
  type UserForm = {
    full_name: string;
    email: string;
    phone: string;
    role: Role;
    admin_access: boolean;
    temporary_pin: string;
    is_active: boolean;
  };

  let currentUser: CurrentUser | null = null;
  let users: AdminUser[] = [];
  let search = '';
  let roleFilter = 'all';
  let statusFilter = 'all';
  let isLoading = true;
  let isSaving = false;
  let error = '';
  let message = '';
  let showForm = false;
  let editingId: number | null = null;
  let resettingUser: AdminUser | null = null;
  let newPin = '';
  let form: UserForm = emptyForm();

  function emptyForm(): UserForm {
    return {
      full_name: '',
      email: '',
      phone: '',
      role: 'citizen',
      admin_access: false,
      temporary_pin: '',
      is_active: true
    };
  }

  function authHeaders(): Record<string, string> {
    return { Authorization: `Bearer ${localStorage.getItem('token')}` };
  }

  function isActive(user: AdminUser) {
    return user.is_active === true || user.is_active === 1;
  }

  function roleName(user: AdminUser) {
    return user.role || 'citizen';
  }

  function hasAdminAccess(user: AdminUser) {
    return user.admin_access === true || user.admin_access === 1 || user.is_superuser === true || user.is_superuser === 1;
  }

  async function loadUsers() {
    const response = await fetch(`${API}/api/admin/users`, { headers: authHeaders() });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || data.message || 'Could not load users.');
    users = data;
  }

  async function initialize() {
    isLoading = true;
    error = '';
    try {
      const response = await fetch(`${API}/api/user/me`, { headers: authHeaders() });
      if (!response.ok) {
        goto('/login');
        return;
      }
      const data: CurrentUser = await response.json();
      currentUser = data;
      if (!data.is_superuser) {
        goto('/dashboard');
        return;
      }
      await loadUsers();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not load users.';
    } finally {
      isLoading = false;
    }
  }

  $: filteredUsers = users.filter((user) => {
    const needle = search.trim().toLowerCase();
    const matchesText = !needle || [
      user.full_name,
      user.username,
      user.email,
      user.phone,
      user.id
    ].some((value) => value != null && String(value).toLowerCase().includes(needle));
    const matchesRole = roleFilter === 'all' || roleName(user) === roleFilter;
    const matchesStatus = statusFilter === 'all'
      || (statusFilter === 'active' ? isActive(user) : !isActive(user));
    return matchesText && matchesRole && matchesStatus;
  });

  function openCreateForm() {
    editingId = null;
    form = emptyForm();
    error = '';
    message = '';
    showForm = true;
  }

  function openEditForm(user: AdminUser) {
    editingId = user.id;
    form = {
      full_name: user.full_name || '',
      email: user.email || '',
      phone: user.phone || '',
      role: roleName(user) as Role,
      admin_access: hasAdminAccess(user),
      temporary_pin: '',
      is_active: isActive(user)
    };
    error = '';
    message = '';
    showForm = true;
  }

  async function saveUser() {
    if (!form.full_name.trim() || !form.phone.trim()) {
      error = 'Full name and phone number are required.';
      return;
    }
    if (!editingId && form.temporary_pin.length < 4) {
      error = 'Temporary PIN must be at least 4 characters.';
      return;
    }

    isSaving = true;
    error = '';
    message = '';
    try {
      const editing = editingId !== null;
      const response = await fetch(
        editing ? `${API}/api/admin/users/${editingId}` : `${API}/api/admin/users`,
        {
          method: editing ? 'PUT' : 'POST',
          headers: { ...authHeaders(), 'Content-Type': 'application/json' },
          body: JSON.stringify({
            full_name: form.full_name.trim(),
            email: form.email.trim() || null,
            phone: form.phone.trim(),
            role: form.role,
            admin_access: form.admin_access || form.role === 'admin',
            ...(editing ? { is_active: form.is_active } : { temporary_pin: form.temporary_pin })
          })
        }
      );
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Could not save this account.');
      showForm = false;
      message = editing ? 'Account updated.' : 'Account created. The user must change their PIN after signing in.';
      await loadUsers();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not save this account.';
    } finally {
      isSaving = false;
    }
  }

  async function toggleActive(user: AdminUser) {
    const nextActive = !isActive(user);
    if (user.id === currentUser?.id && !nextActive) {
      error = 'You cannot deactivate your own administrator account.';
      return;
    }
    error = '';
    message = '';
    try {
      const response = await fetch(`${API}/api/admin/users/${user.id}`, {
        method: 'PUT',
        headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_active: nextActive })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Could not change account access.');
      message = `${user.full_name}: account ${nextActive ? 'activated' : 'deactivated'}.`;
      await loadUsers();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not change account access.';
    }
  }

  async function resetPin() {
    if (!resettingUser || newPin.length < 4) {
      error = 'PIN must be at least 4 characters.';
      return;
    }
    isSaving = true;
    error = '';
    message = '';
    try {
      const response = await fetch(`${API}/api/admin/users/${resettingUser.id}/reset-pin`, {
        method: 'POST',
        headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ new_pin: newPin })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Could not reset the PIN.');
      message = `PIN reset for ${resettingUser.full_name}. They must change it after signing in.`;
      resettingUser = null;
      newPin = '';
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not reset the PIN.';
    } finally {
      isSaving = false;
    }
  }

  function formatDate(value?: string) {
    return value ? new Date(value).toLocaleDateString() : '—';
  }

  onMount(initialize);
</script>

<svelte:head>
  <title>User Management - LandLock Admin</title>
</svelte:head>

<div class="page-wrapper">
  <Navbar
    userType="admin"
    activeLink="/dashboard/admin/users"
    userName={currentUser?.full_name || 'Administrator'}
  />
  <main class="main-content">
    <header class="page-header">
      <div>
        <h1>User management</h1>
        <p>Create accounts, assign roles, and revoke or restore access. Deactivation preserves records.</p>
      </div>
      <button class="button primary" on:click={openCreateForm}>Create account</button>
    </header>

    {#if error}<p class="notice error" role="alert">{error}</p>{/if}
    {#if message}<p class="notice success" role="status">{message}</p>{/if}

    <section class="filters" aria-label="Filter users">
      <label>
        <span>Search users</span>
        <input bind:value={search} placeholder="Name, username, phone, email, or ID" />
      </label>
      <label>
        <span>Role</span>
        <select bind:value={roleFilter}>
          <option value="all">All roles</option>
          {#each roles as role}<option value={role}>{role}</option>{/each}
        </select>
      </label>
      <label>
        <span>Account status</span>
        <select bind:value={statusFilter}>
          <option value="all">All accounts</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
        </select>
      </label>
      <span class="result-count">{filteredUsers.length} of {users.length} accounts</span>
    </section>

    {#if isLoading}
      <p class="empty-state">Loading accounts...</p>
    {:else if filteredUsers.length === 0}
      <section class="empty-state"><h2>No accounts found</h2><p>Try changing the search or filters.</p></section>
    {:else}
      <div class="table-wrap">
        <table>
          <thead>
            <tr><th>User</th><th>Phone</th><th>Role</th><th>Status</th><th>Created</th><th>Actions</th></tr>
          </thead>
          <tbody>
            {#each filteredUsers as user (user.id)}
              <tr>
                <td>
                  <strong>{user.full_name || 'Name not provided'}</strong>
                  <small>{user.email || user.username} · ID {user.id}</small>
                </td>
                <td>{user.phone || '—'}</td>
                <td>
                  <span class="role-badge">{roleName(user)}</span>
                  {#if hasAdminAccess(user)}<small class="admin-badge">Admin access</small>{/if}
                </td>
                <td><span class:active={isActive(user)} class="status-badge">{isActive(user) ? 'Active' : 'Inactive'}</span></td>
                <td>{formatDate(user.created_at)}</td>
                <td class="actions">
                  <button class="button secondary" on:click={() => openEditForm(user)}>Edit / role</button>
                  <button class="button secondary" on:click={() => { resettingUser = user; newPin = ''; error = ''; }}>
                    Reset PIN
                  </button>
                  <button
                    class:danger={!isActive(user)}
                    class="button secondary"
                    disabled={user.id === currentUser?.id && isActive(user)}
                    on:click={() => toggleActive(user)}
                  >
                    {isActive(user) ? 'Revoke access' : 'Restore access'}
                  </button>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
      <p class="footnote">Role changes take effect on the user's next request. Deactivated users are blocked from authenticated endpoints immediately.</p>
    {/if}
  </main>
</div>

{#if showForm}
  <div class="modal-backdrop" role="presentation" on:click={(event) => event.target === event.currentTarget && (showForm = false)}>
    <section class="modal" role="dialog" aria-modal="true" aria-labelledby="user-form-title">
      <h2 id="user-form-title">{editingId ? 'Edit account' : 'Create account'}</h2>
      <label>Full name<input bind:value={form.full_name} disabled={isSaving} /></label>
      <label>Phone<input bind:value={form.phone} type="tel" disabled={isSaving} /></label>
      <label>Email (optional)<input bind:value={form.email} type="email" disabled={isSaving} /></label>
      <label>
        Role
        <select bind:value={form.role} disabled={isSaving || editingId === currentUser?.id}>
          {#each roles as role}<option value={role}>{role}</option>{/each}
        </select>
      </label>
      <label class="checkbox">
        <input
          type="checkbox"
          bind:checked={form.admin_access}
          disabled={isSaving || editingId === currentUser?.id || form.role === 'admin'}
        />
        Grant administrator access
      </label>
      <p class="hint">This adds admin privileges without changing the user's role. Officials with this access can use both dashboards.</p>
      {#if editingId}
        <label class="checkbox"><input type="checkbox" bind:checked={form.is_active} disabled={isSaving || editingId === currentUser?.id} /> Account active</label>
        {#if editingId === currentUser?.id}<p class="hint">You cannot revoke your own administrator access.</p>{/if}
      {:else}
        <label>Temporary PIN<input bind:value={form.temporary_pin} type="password" minlength="4" autocomplete="new-password" disabled={isSaving} /></label>
        <p class="hint">The new account must change this PIN after signing in.</p>
      {/if}
      <div class="modal-actions">
        <button class="button secondary" on:click={() => showForm = false} disabled={isSaving}>Cancel</button>
        <button class="button primary" on:click={saveUser} disabled={isSaving}>{isSaving ? 'Saving...' : 'Save account'}</button>
      </div>
    </section>
  </div>
{/if}

{#if resettingUser}
  <div class="modal-backdrop">
    <section class="modal" role="dialog" aria-modal="true" aria-labelledby="reset-pin-title">
      <h2 id="reset-pin-title">Reset PIN</h2>
      <p>Set a temporary PIN for {resettingUser.full_name}. They will be required to change it after signing in.</p>
      <label>New temporary PIN<input bind:value={newPin} type="password" minlength="4" autocomplete="new-password" disabled={isSaving} /></label>
      <div class="modal-actions">
        <button class="button secondary" on:click={() => resettingUser = null} disabled={isSaving}>Cancel</button>
        <button class="button primary" on:click={resetPin} disabled={isSaving}>{isSaving ? 'Saving...' : 'Reset PIN'}</button>
      </div>
    </section>
  </div>
{/if}

<style>
  .page-wrapper { min-height: 100vh; background: #f8fafc; }
  .main-content { max-width: 1400px; margin: auto; padding: 2rem; }
  .page-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; margin-bottom: 1.5rem; }
  .page-header h1 { margin: 0; color: #1e293b; }
  .page-header p { margin: .4rem 0 0; color: #64748b; }
  .filters { display: flex; align-items: end; gap: 1rem; flex-wrap: wrap; padding: 1rem; border: 1px solid #e2e8f0; border-radius: 10px; background: white; }
  .filters label { display: grid; gap: .35rem; min-width: 170px; color: #475569; font-size: .85rem; }
  input, select { min-height: 40px; padding: .5rem .65rem; border: 1px solid #cbd5e1; border-radius: 6px; background: white; font: inherit; }
  .result-count { margin-left: auto; padding-bottom: .6rem; color: #64748b; }
  .table-wrap { margin-top: 1rem; overflow-x: auto; border: 1px solid #e2e8f0; border-radius: 10px; background: white; }
  table { width: 100%; border-collapse: collapse; text-align: left; }
  th, td { padding: .8rem 1rem; border-bottom: 1px solid #e2e8f0; vertical-align: middle; }
  th { color: #475569; background: #f8fafc; font-size: .8rem; text-transform: uppercase; }
  td strong, td small { display: block; }
  td small { margin-top: .2rem; color: #64748b; }
  .actions { display: flex; gap: .4rem; min-width: 300px; }
  .role-badge, .status-badge { display: inline-block; padding: .25rem .55rem; border-radius: 999px; background: #e2e8f0; color: #334155; font-size: .82rem; text-transform: capitalize; }
  .admin-badge { display: block; width: fit-content; margin-top: .3rem; padding: .2rem .45rem; border-radius: 999px; background: #dcfce7; color: #166534; font-size: .75rem; }
  .status-badge.active { background: #dcfce7; color: #166534; }
  .button { padding: .55rem .8rem; border: 0; border-radius: 6px; font: inherit; font-weight: 600; cursor: pointer; white-space: nowrap; }
  .button:disabled { opacity: .55; cursor: not-allowed; }
  .primary { color: white; background: #166534; }
  .secondary { color: #334155; background: #e2e8f0; }
  .danger { color: white; background: #b91c1c; }
  .notice { margin: 1rem 0; padding: .75rem 1rem; border-radius: 7px; }
  .notice.error { background: #fee2e2; color: #991b1b; }
  .notice.success { background: #dcfce7; color: #166534; }
  .empty-state { margin-top: 1.5rem; padding: 2rem; border: 1px solid #e2e8f0; border-radius: 10px; background: white; text-align: center; color: #64748b; }
  .empty-state h2 { margin: 0 0 .4rem; color: #1e293b; }
  .footnote, .hint { color: #64748b; font-size: .9rem; }
  .modal-backdrop { position: fixed; z-index: 1000; inset: 0; display: grid; place-items: center; padding: 1rem; background: rgb(15 23 42 / 55%); }
  .modal { display: grid; gap: .9rem; width: min(100%, 480px); max-height: 90vh; overflow-y: auto; padding: 1.5rem; border-radius: 12px; background: white; }
  .modal h2, .modal p { margin: 0; }
  .modal label { display: grid; gap: .35rem; color: #334155; font-weight: 600; }
  .modal label.checkbox { display: flex; align-items: center; gap: .55rem; }
  .modal .checkbox input { min-height: auto; }
  .modal-actions { display: flex; justify-content: flex-end; gap: .6rem; margin-top: .5rem; }
  @media (max-width: 700px) {
    .main-content { padding: 1rem; }
    .page-header { flex-direction: column; }
    .result-count { width: 100%; margin-left: 0; }
    .filters label { flex: 1 1 100%; }
  }
</style>
