<script>
  import { goto } from '$app/navigation';
  import { browser } from '$app/environment';
  import { fade } from 'svelte/transition';

  let { children } = $props();

  let mobileMenuOpen = $state(false);

  function logout() {
    if (browser) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
    }
    goto('/login');
  }

  function toggleMobileMenu() {
    mobileMenuOpen = !mobileMenuOpen;
  }

  function closeMobileMenu() {
    mobileMenuOpen = false;
  }
</script>

<svelte:head>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</svelte:head>

<div class="dashboard-wrapper">
  <!-- Mobile Header -->
  <header class="mobile-header">
    <button class="menu-toggle" onclick={toggleMobileMenu} aria-label="Toggle menu">
      <span></span>
      <span></span>
      <span></span>
    </button>
    <div class="mobile-logo">
      <span class="logo-icon">🌍</span>
      <span class="logo-text">LandLock</span>
    </div>
    <div class="mobile-spacer"></div>
  </header>

  <!-- Overlay for mobile menu -->
  {#if mobileMenuOpen}
    <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
    <div class="overlay" onclick={closeMobileMenu} transition:fade={{ duration: 200 }}></div>
  {/if}

  <!-- Sidebar Navigation -->
  <aside class="sidebar" class:open={mobileMenuOpen}>
    <div class="sidebar-header">
      <div class="logo">
        <span class="logo-icon">🌍</span>
        <span class="logo-text">LandLock</span>
      </div>
    </div>

    <nav class="sidebar-nav">
      <a href="/dashboard" class="nav-item active" onclick={closeMobileMenu}>
        <span class="nav-icon">📊</span>
        <span>Dashboard</span>
      </a>
      <a href="/dashboard/register-citizen" class="nav-item" onclick={closeMobileMenu}>
        <span class="nav-icon">👥</span>
        <span>Register Citizen</span>
      </a>
      <a href="/register-plot" class="nav-item" onclick={closeMobileMenu}>
        <span class="nav-icon">➕</span>
        <span>Register Plot</span>
      </a>
      <a href="/plots" class="nav-item" onclick={closeMobileMenu}>
        <span class="nav-icon">📋</span>
        <span>My Plots</span>
      </a>
      <a href="/map" class="nav-item" onclick={closeMobileMenu}>
        <span class="nav-icon">🗺️</span>
        <span>Map View</span>
      </a>
      <a href="/profile" class="nav-item" onclick={closeMobileMenu}>
        <span class="nav-icon">👤</span>
        <span>Profile</span>
      </a>
    </nav>

    <div class="sidebar-footer">
      <button onclick={logout} class="logout-btn">
        <span>🚪</span>
        <span>Logout</span>
      </button>
    </div>
  </aside>

  <!-- Main Content -->
  <main class="main-content">
    {@render children()}
  </main>
</div>

<style>
  :global(body) {
    margin: 0;
    padding: 0;
    font-family: 'Inter', sans-serif;
    background: #f8faf9;
  }

  /* Layout */
  .dashboard-wrapper {
    display: flex;
    min-height: 100vh;
  }

  /* Mobile Header */
  .mobile-header {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: 60px;
    background: white;
    border-bottom: 1px solid #e2e8f0;
    align-items: center;
    justify-content: space-between;
    padding: 0 1rem;
    z-index: 1001;
  }

  .menu-toggle {
    display: flex;
    flex-direction: column;
    gap: 4px;
    background: none;
    border: none;
    cursor: pointer;
    padding: 8px;
  }

  .menu-toggle span {
    width: 24px;
    height: 3px;
    background: #0d9488;
    border-radius: 2px;
    transition: all 0.3s;
  }

  .mobile-logo {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .mobile-spacer {
    width: 40px;
  }

  /* Overlay */
  .overlay {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    z-index: 999;
  }

  /* Sidebar */
  .sidebar {
    width: 260px;
    background: white;
    border-right: 1px solid #e2e8f0;
    display: flex;
    flex-direction: column;
    position: fixed;
    height: 100vh;
    left: 0;
    top: 0;
    z-index: 1000;
    transition: transform 0.3s ease;
  }

  .sidebar-header {
    padding: 1.5rem;
    border-bottom: 1px solid #e2e8f0;
  }

  .logo {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .logo-icon {
    width: 40px;
    height: 40px;
    background: linear-gradient(135deg, #0d9488, #10b981);
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5rem;
    box-shadow: 0 4px 8px rgba(13, 148, 136, 0.2);
  }

  .logo-text {
    font-size: 1.25rem;
    font-weight: 700;
    background: linear-gradient(90deg, #0d9488, #10b981);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }

  .sidebar-nav {
    flex: 1;
    padding: 1rem;
    overflow-y: auto;
  }

  .nav-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem 1rem;
    border-radius: 10px;
    color: #64748b;
    text-decoration: none;
    font-weight: 500;
    margin-bottom: 0.25rem;
    transition: all 0.2s;
  }

  .nav-item:hover {
    background: #f1f5f9;
    color: #0d9488;
  }

  .nav-item.active {
    background: linear-gradient(135deg, #0d9488, #10b981);
    color: white;
    box-shadow: 0 4px 12px rgba(13, 148, 136, 0.3);
  }

  .nav-icon {
    font-size: 1.25rem;
  }

  .sidebar-footer {
    padding: 1rem;
    border-top: 1px solid #e2e8f0;
  }

  .logout-btn {
    width: 100%;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem 1rem;
    border: none;
    background: #fee2e2;
    color: #dc2626;
    border-radius: 10px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
  }

  .logout-btn:hover {
    background: #fecaca;
  }

  /* Main Content */
  .main-content {
    flex: 1;
    margin-left: 260px;
    padding: 2rem;
    max-width: calc(100vw - 260px);
    min-height: 100vh;
  }

  /* Responsive - Mobile */
  @media (max-width: 768px) {
    .mobile-header {
      display: flex;
    }

    .overlay {
      display: block;
    }

    .sidebar {
      transform: translateX(-100%);
    }

    .sidebar.open {
      transform: translateX(0);
    }

    .main-content {
      margin-left: 0;
      margin-top: 60px;
      max-width: 100vw;
      padding: 1rem;
    }
  }

  /* Responsive - Small Mobile */
  @media (max-width: 480px) {
    .main-content {
      padding: 0.75rem;
    }
  }
</style>
