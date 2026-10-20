<script lang="ts">
  import { browser } from '$app/environment';
  import { goto } from '$app/navigation';
  import { onMount, onDestroy } from 'svelte';
  import { Bell, Check, CheckCheck, Clock, Shield, AlertTriangle, Ban, ArrowRight, X } from 'lucide-svelte';

  export let userType: 'citizen' | 'official' | 'chief' | 'admin' = 'citizen';
  export let activeLink: string = '';
  export let userName: string = '';
  export let showNotification: boolean = true;

  let showUserMenu = false;
  let showNotifPanel = false;

  // Notification state
  let notifications: any[] = [];
  let unreadCount = 0;
  let notifLoading = false;
  let pollTimer: ReturnType<typeof setInterval> | null = null;

  const API_BASE = 'http://localhost:5000';

  onMount(() => {
    if (!browser) return;
    if (showNotification) {
      fetchNotifications();
      // Poll every 30 seconds for new notifications
      pollTimer = setInterval(fetchNotifications, 30000);
    }
  });

  onDestroy(() => {
    if (pollTimer) clearInterval(pollTimer);
  });

  function authHeaders(): Record<string, string> {
    const token = browser ? localStorage.getItem('token') : null;
    return token ? { 'Authorization': `Bearer ${token}` } : {};
  }

  async function fetchNotifications() {
    if (!browser) return;
    try {
      const res = await fetch(`${API_BASE}/api/notifications`, {
        headers: authHeaders()
      });
      if (res.ok) {
        const data = await res.json();
        notifications = data.notifications || [];
        unreadCount = data.unread_count || 0;
      }
    } catch { /* silent */ }
  }

  async function markRead(notifId: number) {
    try {
      await fetch(`${API_BASE}/api/notifications/${notifId}/read`, {
        method: 'POST',
        headers: { ...authHeaders(), 'Content-Type': 'application/json' }
      });
      // Update locally
      notifications = notifications.map(n =>
        n.id === notifId ? { ...n, is_read: 1 } : n
      );
      unreadCount = Math.max(0, unreadCount - 1);
    } catch { /* silent */ }
  }

  async function markAllRead() {
    try {
      await fetch(`${API_BASE}/api/notifications/read-all`, {
        method: 'POST',
        headers: { ...authHeaders(), 'Content-Type': 'application/json' }
      });
      notifications = notifications.map(n => ({ ...n, is_read: 1 }));
      unreadCount = 0;
    } catch { /* silent */ }
  }

  function handleNotifClick(notif: any) {
    markRead(notif.id);
    showNotifPanel = false;
    if (notif.link && browser) {
      goto(notif.link);
    }
  }

  function toggleNotifPanel() {
    showNotifPanel = !showNotifPanel;
    if (showNotifPanel) {
      showUserMenu = false;
      fetchNotifications();
    }
  }

  function getNotifIcon(type: string) {
    switch (type) {
      case 'pending_approval': return Shield;
      case 'buyer_confirm': return ArrowRight;
      case 'approved': return Check;
      case 'completed': return CheckCheck;
      case 'rejected': return Ban;
      default: return Bell;
    }
  }

  function getNotifColor(type: string): string {
    switch (type) {
      case 'pending_approval': return '#d97706';
      case 'buyer_confirm': return '#2563eb';
      case 'approved': return '#007A3D';
      case 'completed': return '#007A3D';
      case 'rejected': return '#dc2626';
      default: return '#6b7280';
    }
  }

  function timeAgo(dateStr: string): string {
    const now = new Date();
    const then = new Date(dateStr);
    const diffMs = now.getTime() - then.getTime();
    const diffMin = Math.floor(diffMs / 60000);
    if (diffMin < 1) return 'Just now';
    if (diffMin < 60) return `${diffMin}m ago`;
    const diffHr = Math.floor(diffMin / 60);
    if (diffHr < 24) return `${diffHr}h ago`;
    const diffDay = Math.floor(diffHr / 24);
    if (diffDay < 7) return `${diffDay}d ago`;
    return then.toLocaleDateString();
  }

  function handleLogout() {
    if (browser) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      goto('/login');
    }
  }

  // Click outside to close panels
  function handleOutsideClick(e: MouseEvent) {
    const target = e.target as HTMLElement;
    if (!target.closest('.notif-wrapper')) showNotifPanel = false;
    if (!target.closest('.user-menu')) showUserMenu = false;
  }

  // Menu items based on user type
  $: menuItems = getMenuItems(userType);

  function getMenuItems(type: string) {
    switch (type) {
      case 'admin':
        return [
          { label: 'Dashboard', href: '/dashboard/admin' },
          { label: 'Chief Areas', href: '/dashboard/admin/chief-areas' },
          { label: 'Users', href: '/dashboard/admin/users' },
          { label: 'Account', href: '/profile' },
        ];
      case 'official':
        return [
          { label: 'Dashboard', href: '/dashboard/official' },
          { label: 'My Caseload', href: '/dashboard/official/caseload' },
          { label: 'Chief Areas', href: '/dashboard/official/chief-areas' },
          { label: 'Land Registration', href: '/register-plot' },
          { label: 'Map View', href: '/map' },
          { label: 'Account', href: '/profile' },
        ];
      case 'chief':
        return [
          { label: 'Dashboard', href: '/dashboard/chief' },
          { label: 'Pending Claims', href: '/dashboard/chief/pending' },
          { label: 'Verified Claims', href: '/dashboard/chief/verified' },
          { label: 'Disputed Claims', href: '/dashboard/chief/disputed' },
          { label: 'Reports', href: '/dashboard/chief/reports' },
        ];
      case 'citizen':
      default:
        return [
          { label: 'Dashboard', href: '/dashboard' },
          { label: 'Marketplace', href: '/marketplace' },
          { label: 'My Plots', href: '/my-plots' },
          { label: 'Public Map', href: '/public-map' },
          { label: 'Register Land', href: '/register-land' },
          { label: 'Transactions', href: '/transactions' },
          { label: 'Certificates', href: '/certificates' },
        ];
    }
  }

  $: brandText = getBrandText(userType);

  function getBrandText(type: string) {
    switch (type) {
      case 'admin': return 'LandLock Admin Portal';
      case 'official': return 'Land Registry Official Portal';
      case 'chief': return 'Village Authority Portal';
      case 'citizen':
      default: return 'LandLock';
    }
  }
</script>

<svelte:window on:click={handleOutsideClick} />

<nav class="navbar">
  <div class="navbar-content">
    <div class="navbar-brand">
      <div class="logo">
        <img src="/images/Coat_of_arms_of_Malawi.svg" alt="LandLock Logo" width="32" height="32" />
      </div>
      <span class="brand-name">{brandText}</span>
    </div>
    
    <div class="navbar-menu">
      {#each menuItems as item}
        <a href={item.href} class="nav-link {activeLink === item.href ? 'active' : ''}">
          <span>{item.label}</span>
        </a>
      {/each}
    </div>

    <div class="navbar-actions">
      {#if showNotification}
        <div class="notif-wrapper">
          <button class="icon-btn notif-btn" on:click|stopPropagation={toggleNotifPanel}>
            <Bell class="w-5 h-5" />
            {#if unreadCount > 0}
              <span class="notif-badge">{unreadCount > 99 ? '99+' : unreadCount}</span>
            {/if}
          </button>

          {#if showNotifPanel}
            <div class="notif-panel" on:click|stopPropagation>
              <div class="notif-header">
                <h3>Notifications</h3>
                {#if unreadCount > 0}
                  <button class="mark-all-btn" on:click={markAllRead}>
                    <CheckCheck class="w-3.5 h-3.5" />
                    Mark all read
                  </button>
                {/if}
              </div>

              <div class="notif-list">
                {#if notifications.length === 0}
                  <div class="notif-empty">
                    <Bell class="w-8 h-8 empty-icon" />
                    <p>No notifications yet</p>
                    <span>Transaction updates will appear here</span>
                  </div>
                {:else}
                  {#each notifications as notif (notif.id)}
                    <button
                      class="notif-item"
                      class:unread={!notif.is_read}
                      on:click={() => handleNotifClick(notif)}
                    >
                      <div class="notif-icon-wrap" style="background: {getNotifColor(notif.type)}15; color: {getNotifColor(notif.type)};">
                        <svelte:component this={getNotifIcon(notif.type)} class="w-4 h-4" />
                      </div>
                      <div class="notif-content">
                        <div class="notif-title">{notif.title}</div>
                        <div class="notif-message">{notif.message}</div>
                        <div class="notif-time">
                          <Clock class="w-3 h-3" />
                          {timeAgo(notif.created_at)}
                        </div>
                      </div>
                      {#if !notif.is_read}
                        <div class="unread-dot"></div>
                      {/if}
                    </button>
                  {/each}
                {/if}
              </div>
            </div>
          {/if}
        </div>
      {/if}

      <div class="user-menu" style="position: relative;">
        <button class="avatar" on:click|stopPropagation={() => { showUserMenu = !showUserMenu; showNotifPanel = false; }} style="border: none;">
          <span>{userName.charAt(0).toUpperCase()}</span>
        </button>
        {#if showUserMenu}
          <div class="dropdown-menu">
            <button on:click={handleLogout} class="dropdown-item">Logout</button>
          </div>
        {/if}
      </div>
    </div>
  </div>
</nav>

<style>
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

  .logo { display: flex; align-items: center; }

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

  .nav-link:hover { background: #f1f5f9; color: #334155; }
  .nav-link.active { background: #007A3D; color: white; }

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

  .icon-btn:hover { background: #f1f5f9; color: #334155; }

  /* ── Notification bell ── */
  .notif-wrapper { position: relative; }

  .notif-btn { position: relative; }

  .notif-badge {
    position: absolute;
    top: -4px;
    right: -4px;
    background: #dc2626;
    color: white;
    font-size: 0.625rem;
    font-weight: 700;
    min-width: 18px;
    height: 18px;
    border-radius: 9px;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0 4px;
    line-height: 1;
    border: 2px solid white;
  }

  /* ── Notification panel ── */
  .notif-panel {
    position: absolute;
    top: calc(100% + 8px);
    right: 0;
    width: 400px;
    max-height: 520px;
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
    display: flex;
    flex-direction: column;
    overflow: hidden;
    z-index: 1000;
    animation: slideDown 0.15s ease-out;
  }

  @keyframes slideDown {
    from { opacity: 0; transform: translateY(-8px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .notif-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.875rem 1rem;
    border-bottom: 1px solid #e2e8f0;
    background: #f8fafc;
  }

  .notif-header h3 {
    font-size: 0.9375rem;
    font-weight: 700;
    color: #1a1a1a;
    margin: 0;
  }

  .mark-all-btn {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    background: none;
    border: none;
    color: #007A3D;
    font-size: 0.75rem;
    font-weight: 600;
    cursor: pointer;
    padding: 0.25rem 0.5rem;
    border-radius: 6px;
    transition: background 0.15s;
  }

  .mark-all-btn:hover { background: #ecfdf5; }

  .notif-list {
    overflow-y: auto;
    flex: 1;
    max-height: 440px;
  }

  .notif-empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 3rem 1.5rem;
    color: #9ca3af;
  }

  .empty-icon { color: #d1d5db; margin-bottom: 0.75rem; }

  .notif-empty p {
    font-size: 0.875rem;
    font-weight: 600;
    color: #6b7280;
    margin: 0 0 0.25rem;
  }

  .notif-empty span {
    font-size: 0.75rem;
    color: #9ca3af;
  }

  .notif-item {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    width: 100%;
    padding: 0.875rem 1rem;
    border: none;
    background: none;
    cursor: pointer;
    text-align: left;
    border-bottom: 1px solid #f3f4f6;
    transition: background 0.15s;
    position: relative;
  }

  .notif-item:hover { background: #f8fafc; }
  .notif-item:last-child { border-bottom: none; }

  .notif-item.unread { background: #f0fdf4; }
  .notif-item.unread:hover { background: #ecfdf5; }

  .notif-icon-wrap {
    flex-shrink: 0;
    width: 36px;
    height: 36px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .notif-content {
    flex: 1;
    min-width: 0;
  }

  .notif-title {
    font-size: 0.8125rem;
    font-weight: 600;
    color: #1a1a1a;
    margin-bottom: 0.125rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .notif-message {
    font-size: 0.75rem;
    color: #6b7280;
    line-height: 1.4;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .notif-time {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    font-size: 0.6875rem;
    color: #9ca3af;
    margin-top: 0.375rem;
  }

  .unread-dot {
    flex-shrink: 0;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #007A3D;
    margin-top: 0.5rem;
  }

  /* ── User menu ── */
  .user-menu { display: flex; align-items: center; }

  .avatar {
    width: 40px;
    height: 40px;
    border-radius: 10px;
    background: #007A3D;
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
  
  .dropdown-item:hover { background: #fef2f2; border-radius: 8px; }

  @media (max-width: 768px) {
    .navbar-content { padding: 0 1rem; }
    .navbar-menu { display: none; }
    .notif-panel { width: calc(100vw - 2rem); right: -0.5rem; }
  }
</style>
