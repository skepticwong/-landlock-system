<script lang="ts">
  import { browser } from "$app/environment";
  import { goto } from "$app/navigation";
  import { page } from "$app/stores";
  import { onMount, onDestroy } from "svelte";
  import {
    Bell,
    Check,
    CheckCheck,
    Clock,
    Shield,
    AlertTriangle,
    Ban,
    ArrowRight,
    X,
    LayoutDashboard,
    Store,
    Map,
    MapPinned,
    FilePlus,
    ArrowLeftRight,
    FileText,
    FolderOpen,
    Users,
    ChartBarBig as BarChartBig,
    ChevronRight,
    Search,
    LogOut,
  } from "lucide-svelte";

  export let userType: "citizen" | "official" | "chief" | "admin" = "citizen";
  export let activeLink: string = "";
  export let userName: string = "";
  export let userRole: string = "";
  export let showNotification: boolean = true;

  let showUserMenu = false;
  let showNotifPanel = false;
  let showSearchPanel = false;
  let sidebarHover = false;

  // ── User identity (name + role + avatar) ──
  let profileName = userName;
  let profileRole = userRole || "Citizen";
  let avatarUrl: string | null = null;

  // ── Search state ──
  let searchQuery = "";
  let searchResults: { parcels: any[]; transactions: any[] } = {
    parcels: [],
    transactions: [],
  };
  let searchTimer: ReturnType<typeof setTimeout> | null = null;
  let searching = false;

  // ── Notification state ──
  let notifications: any[] = [];
  let unreadCount = 0;
  let notifLoading = false;
  let pollTimer: ReturnType<typeof setInterval> | null = null;

  const API_BASE = "http://localhost:5000";

  onMount(() => {
    if (!browser) return;
    loadProfile();
    if (showNotification) {
      fetchNotifications();
      pollTimer = setInterval(fetchNotifications, 30000);
    }
  });

  onDestroy(() => {
    if (pollTimer) clearInterval(pollTimer);
    if (searchTimer) clearTimeout(searchTimer);
  });

  function authHeaders(): Record<string, string> {
    const token = browser ? localStorage.getItem("token") : null;
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  async function loadProfile() {
    try {
      const res = await fetch(`${API_BASE}/api/user/me`, {
        headers: authHeaders(),
      });
      if (!res.ok) return;
      const u = await res.json();
      if (u.full_name || u.username) profileName = u.full_name || u.username;
      if (u.is_superuser) profileRole = "Administrator";
      else if (u.role) profileRole = String(u.role);
      if (u.avatar_url || u.photo_url) avatarUrl = u.avatar_url || u.photo_url;
    } catch {
      /* silent */
    }
  }

  function initials(name: string): string {
    return (name || "U").trim().charAt(0).toUpperCase();
  }

  // ── Search across plots / transactions / ids ──
  function onSearchInput() {
    showSearchPanel = true;
    if (searchTimer) clearTimeout(searchTimer);
    const q = searchQuery.trim();
    if (q.length < 2) {
      searchResults = { parcels: [], transactions: [] };
      searching = false;
      return;
    }
    searching = true;
    searchTimer = setTimeout(() => runSearch(q), 300);
  }

  async function runSearch(q: string) {
    try {
      const [parcelsRes, txRes] = await Promise.all([
        fetch(`${API_BASE}/api/parcels`, { headers: authHeaders() }),
        fetch(`${API_BASE}/api/transactions`, { headers: authHeaders() }),
      ]);
      const parcels = parcelsRes.ok ? await parcelsRes.json() : [];
      const transactions = txRes.ok ? await txRes.json() : [];
      const needle = q.toLowerCase();
      searchResults = {
        parcels: parcels
          .filter((p: any) =>
            [p.id, p.location, p.plot_number, p.owner_name, p.size].some(
              (v) => v && String(v).toLowerCase().includes(needle),
            ),
          )
          .slice(0, 5),
        transactions: transactions
          .filter((t: any) =>
            [
              t.id,
              t.parcel_id,
              t.plot_id,
              t.transaction_type,
              t.status,
              t.counterparty,
            ].some((v) => v && String(v).toLowerCase().includes(needle)),
          )
          .slice(0, 5),
      };
    } catch {
      /* silent */
    }
    searching = false;
  }

  function goToParcel(p: any) {
    clearSearch();
    goto("/my-plots");
  }

  function goToTransaction(t: any) {
    clearSearch();
    goto("/transactions");
  }

  function clearSearch() {
    searchQuery = "";
    searchResults = { parcels: [], transactions: [] };
    showSearchPanel = false;
  }

  // ── Notifications ──
  async function fetchNotifications() {
    if (!browser) return;
    try {
      const res = await fetch(`${API_BASE}/api/notifications`, {
        headers: authHeaders(),
      });
      if (res.ok) {
        const data = await res.json();
        notifications = data.notifications || [];
        unreadCount = data.unread_count || 0;
      }
    } catch {
      /* silent */
    }
  }

  async function markRead(notifId: number) {
    try {
      await fetch(`${API_BASE}/api/notifications/${notifId}/read`, {
        method: "POST",
        headers: { ...authHeaders(), "Content-Type": "application/json" },
      });
      notifications = notifications.map((n) =>
        n.id === notifId ? { ...n, is_read: 1 } : n,
      );
      unreadCount = Math.max(0, unreadCount - 1);
    } catch {
      /* silent */
    }
  }

  async function markAllRead() {
    try {
      await fetch(`${API_BASE}/api/notifications/read-all`, {
        method: "POST",
        headers: { ...authHeaders(), "Content-Type": "application/json" },
      });
      notifications = notifications.map((n) => ({ ...n, is_read: 1 }));
      unreadCount = 0;
    } catch {
      /* silent */
    }
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
      case "pending_approval":
        return Shield;
      case "buyer_confirm":
        return ArrowRight;
      case "approved":
        return Check;
      case "completed":
        return CheckCheck;
      case "rejected":
        return Ban;
      default:
        return Bell;
    }
  }

  function getNotifColor(type: string): string {
    switch (type) {
      case "pending_approval":
        return "#d97706";
      case "buyer_confirm":
        return "#2563eb";
      case "approved":
        return "#007A3D";
      case "completed":
        return "#007A3D";
      case "rejected":
        return "#dc2626";
      default:
        return "#6b7280";
    }
  }

  function timeAgo(dateStr: string): string {
    const now = new Date();
    const then = new Date(dateStr);
    const diffMs = now.getTime() - then.getTime();
    const diffMin = Math.floor(diffMs / 60000);
    if (diffMin < 1) return "Just now";
    if (diffMin < 60) return `${diffMin}m ago`;
    const diffHr = Math.floor(diffMin / 60);
    if (diffHr < 24) return `${diffHr}h ago`;
    const diffDay = Math.floor(diffHr / 24);
    if (diffDay < 7) return `${diffDay}d ago`;
    return then.toLocaleDateString();
  }

  function handleLogout() {
    if (browser) {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      goto("/login");
    }
  }

  // Click outside to close panels
  function handleOutsideClick(e: MouseEvent) {
    const target = e.target as HTMLElement;
    if (!target.closest(".notif-wrapper")) showNotifPanel = false;
    if (!target.closest(".user-menu")) showUserMenu = false;
    if (!target.closest(".search-wrapper")) showSearchPanel = false;
  }

  // ── Sidebar menu items (with icons) per user type ──
  $: menuItems = getMenuItems(userType);

  function getMenuItems(type: string) {
    switch (type) {
      case "admin":
        return [
          {
            label: "Dashboard",
            href: "/dashboard/admin",
            icon: LayoutDashboard,
          },
          {
            label: "Chief Areas",
            href: "/dashboard/admin/chief-areas",
            icon: Map,
          },
          { label: "Users", href: "/dashboard/admin/users", icon: Users },
          { label: "Account", href: "/profile", icon: Shield },
        ];
      case "official":
        return [
          {
            label: "Dashboard",
            href: "/dashboard/official",
            icon: LayoutDashboard,
          },
          {
            label: "My Caseload",
            href: "/dashboard/official/caseload",
            icon: FolderOpen,
          },
          {
            label: "Chief Areas",
            href: "/dashboard/official/chief-areas",
            icon: Map,
          },
          {
            label: "Land Registration",
            href: "/register-plot",
            icon: FilePlus,
          },
          { label: "Map View", href: "/map", icon: MapPinned },
          { label: "Account", href: "/profile", icon: Shield },
        ];
      case "chief":
        return [
          {
            label: "Dashboard",
            href: "/dashboard/chief",
            icon: LayoutDashboard,
          },
          {
            label: "Pending Claims",
            href: "/dashboard/chief/pending",
            icon: Clock,
          },
          {
            label: "Verified Claims",
            href: "/dashboard/chief/verified",
            icon: Check,
          },
          {
            label: "Disputed Claims",
            href: "/dashboard/chief/disputed",
            icon: AlertTriangle,
          },
          {
            label: "Reports",
            href: "/dashboard/chief/reports",
            icon: BarChartBig,
          },
        ];
      case "citizen":
      default:
        return [
          { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
          { label: "Marketplace", href: "/marketplace", icon: Store },
          { label: "My Plots", href: "/my-plots", icon: Map },
          { label: "Public Map", href: "/public-map", icon: MapPinned },
          { label: "Register Land", href: "/register-land", icon: FilePlus },
          {
            label: "Transactions",
            href: "/transactions",
            icon: ArrowLeftRight,
          },
          { label: "Certificates", href: "/certificates", icon: FileText },
        ];
    }
  }

  $: brandText = getBrandText(userType);

  function getBrandText(type: string) {
    switch (type) {
      case "admin":
        return "Admin Portal";
      case "official":
        return "Official Portal";
      case "chief":
        return "Village Authority";
      case "citizen":
      default:
        return "LandLock";
    }
  }

  // ── Breadcrumbs derived from current route ──
  $: pathname = $page.url.pathname;
  $: crumbs = buildCrumbs(pathname, userType);

  function buildCrumbs(path: string, type: string) {
    const brand =
      type === "admin"
        ? "Admin"
        : type === "official"
          ? "Official"
          : type === "chief"
            ? "Chief"
            : "Home";
    const parts = path.split("/").filter(Boolean);
    const items: { label: string; href: string }[] = [
      { label: brand, href: "/" + (parts[0] || "") },
    ];
    let acc = "";
    parts.forEach((seg, i) => {
      acc += "/" + seg;
      if (i === 0) return; // first segment covered by brand
      const pretty = seg
        .replace(/-/g, " ")
        .replace(/^\d+$/, "Details") // numeric ids
        .replace(/\b\w/g, (c) => c.toUpperCase());
      items.push({ label: pretty, href: acc });
    });
    if (items.length === 1) items.push({ label: "Dashboard", href: path });
    return items;
  }
</script>

<svelte:window on:click={handleOutsideClick} />

<!-- ── Fixed sidebar rail (expands on hover) ── -->
<aside
  class="sidebar"
  class:expanded={sidebarHover}
  on:mouseenter={() => (sidebarHover = true)}
  on:mouseleave={() => (sidebarHover = false)}
>
  <a class="side-brand" href="/">
    <img
      src="/images/Coat_of_arms_of_Malawi.svg"
      alt="LandLock Logo"
      width="32"
      height="32"
    />
    <span class="side-brand-name">{brandText}</span>
  </a>

  <nav class="side-nav">
    {#each menuItems as item (item.href)}
      <a
        href={item.href}
        class="side-link"
        class:active={pathname === item.href || activeLink === item.href}
      >
        <span class="side-icon"
          ><svelte:component this={item.icon} class="w-5 h-5" /></span
        >
        <span class="side-label">{item.label}</span>
      </a>
    {/each}
  </nav>

  <div class="side-footer">
    <button class="side-link side-logout" on:click={handleLogout}>
      <span class="side-icon"><LogOut class="w-5 h-5" /></span>
      <span class="side-label">Logout</span>
    </button>
  </div>
</aside>

<!-- ── Top bar: search + breadcrumbs + notifications + user ── -->
<header class="topbar">
  <div class="topbar-inner">
    <!-- Search -->
    <div class="search-wrapper">
      <div class="search-box">
        <Search class="w-4 h-4 search-icon" />
        <input
          type="text"
          placeholder="Search plots, transactions, IDs..."
          bind:value={searchQuery}
          on:input={onSearchInput}
          on:focus={() => (showSearchPanel = true)}
        />
        {#if searchQuery}
          <button
            class="search-clear"
            on:click={clearSearch}
            aria-label="Clear search"
          >
            <X class="w-3.5 h-3.5" />
          </button>
        {/if}
      </div>

      {#if showSearchPanel && searchQuery.trim().length >= 2}
        <div class="search-panel">
          {#if searching}
            <div class="search-empty"><p>Searching…</p></div>
          {:else if searchResults.parcels.length === 0 && searchResults.transactions.length === 0}
            <div class="search-empty">
              <Search class="w-8 h-8 empty-icon" />
              <p>No results found</p>
              <span>Try a plot ID, location or transaction type</span>
            </div>
          {:else}
            {#if searchResults.parcels.length > 0}
              <div class="search-group-title">Plots</div>
              {#each searchResults.parcels as p (p.id)}
                <button class="search-item" on:click={() => goToParcel(p)}>
                  <span class="search-item-icon"><Map class="w-4 h-4" /></span>
                  <span class="search-item-body">
                    <span class="search-item-title">{p.id}</span>
                    <span class="search-item-meta"
                      >{p.location || "Unknown location"}</span
                    >
                  </span>
                </button>
              {/each}
            {/if}
            {#if searchResults.transactions.length > 0}
              <div class="search-group-title">Transactions</div>
              {#each searchResults.transactions as t (t.id)}
                <button class="search-item" on:click={() => goToTransaction(t)}>
                  <span class="search-item-icon"
                    ><ArrowLeftRight class="w-4 h-4" /></span
                  >
                  <span class="search-item-body">
                    <span class="search-item-title"
                      >{t.transaction_type || "Transaction"} · {t.plot_id ||
                        t.parcel_id ||
                        t.id}</span
                    >
                    <span class="search-item-meta">{t.status}</span>
                  </span>
                </button>
              {/each}
            {/if}
          {/if}
        </div>
      {/if}
    </div>

    <!-- Breadcrumbs -->
    <nav class="breadcrumbs" aria-label="Breadcrumb">
      {#each crumbs as crumb, i (crumb.href + i)}
        {#if i > 0}
          <ChevronRight class="w-3.5 h-3.5 crumb-sep" />
        {/if}
        {#if i === crumbs.length - 1}
          <span class="crumb current">{crumb.label}</span>
        {:else}
          <a class="crumb" href={crumb.href}>{crumb.label}</a>
        {/if}
      {/each}
    </nav>

    <!-- Actions -->
    <div class="topbar-actions">
      {#if showNotification}
        <div class="notif-wrapper">
          <button
            class="icon-btn notif-btn"
            on:click|stopPropagation={toggleNotifPanel}
          >
            <Bell class="w-5 h-5" />
            {#if unreadCount > 0}
              <span class="notif-badge"
                >{unreadCount > 99 ? "99+" : unreadCount}</span
              >
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
                      <div
                        class="notif-icon-wrap"
                        style="background: {getNotifColor(
                          notif.type,
                        )}15; color: {getNotifColor(notif.type)};"
                      >
                        <svelte:component
                          this={getNotifIcon(notif.type)}
                          class="w-4 h-4"
                        />
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

      <!-- User chip: avatar + name + role -->
      <div class="user-menu">
        <button
          class="user-chip"
          on:click|stopPropagation={() => {
            showUserMenu = !showUserMenu;
            showNotifPanel = false;
          }}
        >
          {#if avatarUrl}
            <img class="avatar-img" src={avatarUrl} alt={profileName} />
          {:else}
            <span class="avatar">{initials(profileName)}</span>
          {/if}
          <span class="user-meta">
            <span class="user-name">{profileName || "User"}</span>
            <span class="user-role">{profileRole}</span>
          </span>
        </button>
        {#if showUserMenu}
          <div class="dropdown-menu">
            <button
              on:click={() => goto("/profile")}
              class="dropdown-item profile">My Profile</button
            >
            <button on:click={handleLogout} class="dropdown-item">Logout</button
            >
          </div>
        {/if}
      </div>
    </div>
  </div>
</header>

<style>
  /* ═══════════ Sidebar ═══════════ */
  .sidebar {
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;
    width: 72px;
    background: white;
    border-right: 1px solid #e2e8f0;
    display: flex;
    flex-direction: column;
    z-index: 200;
    overflow: hidden;
    transition: width 0.25s ease;
    box-shadow: 0 0 12px rgba(0, 0, 0, 0.04);
  }

  .sidebar.expanded {
    width: 240px;
  }

  .side-brand {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    height: 64px;
    padding: 0 1.25rem;
    flex-shrink: 0;
    text-decoration: none;
    border-bottom: 1px solid #f1f5f9;
  }

  .side-brand img {
    flex-shrink: 0;
  }

  .side-brand-name {
    font-size: 1.05rem;
    font-weight: 700;
    color: #0f172a;
    letter-spacing: -0.5px;
    white-space: nowrap;
    opacity: 0;
    transition: opacity 0.2s;
  }

  .sidebar.expanded .side-brand-name {
    opacity: 1;
  }

  .side-nav {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    padding: 1rem 0.625rem;
    overflow-y: auto;
    overflow-x: hidden;
  }

  .side-link {
    display: flex;
    align-items: center;
    gap: 0.875rem;
    padding: 0.75rem 0.875rem;
    border-radius: 10px;
    text-decoration: none;
    color: #64748b;
    font-weight: 500;
    font-size: 0.9375rem;
    white-space: nowrap;
    transition: all 0.2s;
    border: none;
    background: none;
    cursor: pointer;
    width: 100%;
    text-align: left;
  }

  .side-link:hover {
    background: #f1f5f9;
    color: #334155;
  }
  .side-link.active {
    background: #007a3d;
    color: white;
  }

  .side-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .side-label {
    opacity: 0;
    transition: opacity 0.2s;
  }

  .sidebar.expanded .side-label {
    opacity: 1;
  }

  .side-footer {
    padding: 0.625rem;
    border-top: 1px solid #f1f5f9;
  }

  .side-logout {
    color: #ef4444;
  }
  .side-logout:hover {
    background: #fef2f2;
    color: #dc2626;
  }

  /* ═══════════ Topbar ═══════════ */
  .topbar {
    position: sticky;
    top: 0;
    z-index: 150;
    margin-left: 72px;
    background: white;
    border-bottom: 1px solid #e2e8f0;
    box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
    transition: margin-left 0.25s ease;
  }

  .topbar-inner {
    height: 64px;
    padding: 0 2rem 0 1rem;
    display: flex;
    align-items: center;
    gap: 1.25rem;
  }

  /* ── Search ── */
  .search-wrapper {
    position: relative;
    width: 320px;
    flex-shrink: 0;
  }

  .search-box {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 0 0.75rem;
    height: 40px;
    transition:
      border-color 0.2s,
      box-shadow 0.2s;
  }

  .search-box:focus-within {
    border-color: #007a3d;
    box-shadow: 0 0 0 3px rgba(0, 122, 61, 0.12);
    background: white;
  }

  .search-icon {
    color: #94a3b8;
    flex-shrink: 0;
  }

  .search-box input {
    flex: 1;
    border: none;
    outline: none;
    background: transparent;
    font-size: 0.875rem;
    color: #1e293b;
    min-width: 0;
  }

  .search-box input::placeholder {
    color: #94a3b8;
  }

  .search-clear {
    border: none;
    background: none;
    color: #94a3b8;
    cursor: pointer;
    display: flex;
    padding: 0.25rem;
    border-radius: 6px;
  }

  .search-clear:hover {
    color: #64748b;
    background: #e2e8f0;
  }

  .search-panel {
    position: absolute;
    top: calc(100% + 8px);
    left: 0;
    width: 100%;
    min-width: 360px;
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
    z-index: 1000;
    max-height: 420px;
    overflow-y: auto;
    animation: slideDown 0.15s ease-out;
  }

  .search-group-title {
    padding: 0.5rem 1rem 0.25rem;
    font-size: 0.6875rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #94a3b8;
  }

  .search-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    width: 100%;
    padding: 0.625rem 1rem;
    border: none;
    background: none;
    cursor: pointer;
    text-align: left;
    transition: background 0.15s;
  }

  .search-item:hover {
    background: #f0fdf4;
  }

  .search-item-icon {
    flex-shrink: 0;
    width: 32px;
    height: 32px;
    border-radius: 8px;
    background: rgba(0, 122, 61, 0.1);
    color: #007a3d;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .search-item-body {
    min-width: 0;
    display: flex;
    flex-direction: column;
  }

  .search-item-title {
    font-size: 0.875rem;
    font-weight: 600;
    color: #1a1a1a;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .search-item-meta {
    font-size: 0.75rem;
    color: #6b7280;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .search-empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 2rem 1.5rem;
    color: #9ca3af;
    text-align: center;
  }

  .search-empty .empty-icon {
    color: #d1d5db;
    margin-bottom: 0.5rem;
  }
  .search-empty p {
    font-size: 0.875rem;
    font-weight: 600;
    color: #6b7280;
    margin: 0 0 0.25rem;
  }
  .search-empty span {
    font-size: 0.75rem;
  }

  /* ── Breadcrumbs ── */
  .breadcrumbs {
    display: flex;
    align-items: center;
    gap: 0.375rem;
    flex: 1;
    min-width: 0;
    overflow: hidden;
  }

  .crumb {
    font-size: 0.8125rem;
    color: #64748b;
    text-decoration: none;
    white-space: nowrap;
    font-weight: 500;
  }

  a.crumb:hover {
    color: #007a3d;
  }

  .crumb.current {
    color: #0f172a;
    font-weight: 700;
  }

  .crumb-sep {
    color: #cbd5e1;
    flex-shrink: 0;
  }

  /* ── Actions ── */
  .topbar-actions {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    flex-shrink: 0;
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

  /* ── Notification bell ── */
  .notif-wrapper {
    position: relative;
  }
  .notif-btn {
    position: relative;
  }

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
    from {
      opacity: 0;
      transform: translateY(-8px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
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
    color: #007a3d;
    font-size: 0.75rem;
    font-weight: 600;
    cursor: pointer;
    padding: 0.25rem 0.5rem;
    border-radius: 6px;
    transition: background 0.15s;
  }

  .mark-all-btn:hover {
    background: #ecfdf5;
  }

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

  .empty-icon {
    color: #d1d5db;
    margin-bottom: 0.75rem;
  }

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

  .notif-item:hover {
    background: #f8fafc;
  }
  .notif-item:last-child {
    border-bottom: none;
  }

  .notif-item.unread {
    background: #f0fdf4;
  }
  .notif-item.unread:hover {
    background: #ecfdf5;
  }

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
    background: #007a3d;
    margin-top: 0.5rem;
  }

  /* ── User chip ── */
  .user-menu {
    position: relative;
  }

  .user-chip {
    display: flex;
    align-items: center;
    gap: 0.625rem;
    padding: 0.25rem 0.625rem 0.25rem 0.25rem;
    border-radius: 10px;
    border: 1px solid transparent;
    background: none;
    cursor: pointer;
    transition: all 0.2s;
  }

  .user-chip:hover {
    background: #f1f5f9;
    border-color: #e2e8f0;
  }

  .avatar {
    width: 40px;
    height: 40px;
    border-radius: 10px;
    background: #007a3d;
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
    font-size: 0.875rem;
    flex-shrink: 0;
  }

  .avatar-img {
    width: 40px;
    height: 40px;
    border-radius: 10px;
    object-fit: cover;
    flex-shrink: 0;
  }

  .user-meta {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    line-height: 1.2;
  }

  .user-name {
    font-size: 0.8125rem;
    font-weight: 700;
    color: #0f172a;
    white-space: nowrap;
  }

  .user-role {
    font-size: 0.6875rem;
    color: #64748b;
    font-weight: 500;
    white-space: nowrap;
  }

  .dropdown-menu {
    position: absolute;
    top: 100%;
    right: 0;
    margin-top: 0.5rem;
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    min-width: 150px;
    z-index: 1000;
    overflow: hidden;
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
    font-size: 0.875rem;
  }

  .dropdown-item.profile {
    color: #334155;
  }
  .dropdown-item.profile:hover {
    background: #f1f5f9;
  }
  .dropdown-item:hover {
    background: #fef2f2;
  }

  /* ── Responsive ── */
  @media (max-width: 1100px) {
    .breadcrumbs {
      display: none;
    }
    .search-wrapper {
      width: 260px;
    }
  }

  @media (max-width: 768px) {
    .sidebar {
      width: 0;
      border-right: none;
    }
    .sidebar.expanded {
      width: 0;
    }
    .topbar {
      margin-left: 0;
    }
    .topbar-inner {
      padding: 0 1rem;
    }
    .user-meta {
      display: none;
    }
    .notif-panel {
      width: calc(100vw - 2rem);
      right: -0.5rem;
    }
    .side-brand,
    .side-nav,
    .side-footer {
      display: none;
    }
  }
</style>
