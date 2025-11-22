<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { browser } from '$app/environment';
  import { plots, status } from '$lib/store';
  import { fetchPlots } from '$lib/api';
  import { initMap } from '$lib/map';
  import SimpleBarChart from '$lib/components/SimpleBarChart.svelte';
  import { fade } from 'svelte/transition';

  let userPlots = [];
  let map;
  let loading = true;
  let mobileMenuOpen = false;
  let stats = {
    total: 0,
    pending: 0,
    approved: 0,
    rejected: 0,
    totalArea: 0
  };

  let chartData = {
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
    series: [
      { values: [0, 0, 0, 0, 0, 0] }
    ]
  };

  onMount(async () => {
    if (!browser) return;
    
    if (!localStorage.getItem('token')) {
      goto('/login');
      return;
    }

    try {
      loading = true;
      const data = await fetchPlots();
      plots.set(data);
      userPlots = data;
      updateStats(data);
      updateChartData(data);
      setTimeout(() => {
        initializeMap(data);
      }, 100);
    } catch (error) {
      console.error('Error loading dashboard data:', error);
      status.set('Failed to load dashboard data. Please try refreshing the page.');
      stats = { total: 0, pending: 0, approved: 0, rejected: 0, totalArea: 0 };
      userPlots = [];
    } finally {
      loading = false;
    }
  });

  function updateStats(plots) {
    const initialStats = { total: 0, pending: 0, approved: 0, rejected: 0, totalArea: 0 };
    stats = plots.reduce((acc, plot) => {
      acc.total++;
      if (plot.status === 'pending' || plot.status === 'approved' || plot.status === 'rejected') {
        acc[plot.status]++;
      }
      if (typeof plot.area === 'number') {
        acc.totalArea += plot.area;
      }
      return acc;
    }, { ...initialStats });
  }

  function updateChartData(plots) {
    const monthlyCounts = Array(6).fill(0);
    const now = new Date();
    
    plots.forEach(plot => {
      const plotDate = new Date(plot.created_at);
      const monthDiff = (now.getFullYear() - plotDate.getFullYear()) * 12 + 
                       (now.getMonth() - plotDate.getMonth());
      if (monthDiff >= 0 && monthDiff < 6) {
        monthlyCounts[5 - monthDiff]++;
      }
    });

    chartData = {
      ...chartData,
      values: monthlyCounts
    };
  }

  async function initializeMap(plots) {
    const mapElement = document.getElementById('dashboard-map');
    if (!mapElement) return;

    try {
      // Import Leaflet dynamically
      const leaflet = await import('leaflet');
      const L = leaflet.default || leaflet;
      
      // Initialize map with default view
      map = L.map('dashboard-map', {
        center: [-13.9626, 33.7741],
        zoom: 6,
        zoomControl: true,
        scrollWheelZoom: true
      });

      // Add OpenStreetMap tiles
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19,
        detectRetina: true
      }).addTo(map);

      // Add markers for each plot
      plots.forEach(plot => {
        if (!plot.points || plot.points.length === 0) return;

        // Calculate center of the plot
        const center = plot.points.reduce(
          (acc, point) => {
            acc.lat += point.lat;
            acc.lng += point.lng;
            return acc;
          },
          { lat: 0, lng: 0 }
        );

        const avgLat = center.lat / plot.points.length;
        const avgLng = center.lng / plot.points.length;

        // Create a custom icon
        const icon = L.divIcon({
          className: 'plot-marker',
          html: `
            <div class="marker-inner" style="background-color: ${
              plot.status === 'approved' ? '#10B981' : 
              plot.status === 'pending' ? '#F59E0B' : '#EF4444'
            };">
              <span>${plot.plot_name ? plot.plot_name.charAt(0).toUpperCase() : 'P'}</span>
            </div>
          `,
          iconSize: [32, 32],
          iconAnchor: [16, 32],
          popupAnchor: [0, -32]
        });

        // Create marker with custom icon
        const marker = L.marker([avgLat, avgLng], { icon });

        // Add popup with plot information
        const popupContent = `
          <div class="popup-content">
            <h4 class="font-bold text-lg mb-1">${plot.plot_name || 'Unnamed Plot'}</h4>
            <div class="flex items-center gap-2 mb-2">
              <span class="status-badge status-${plot.status}" style="display: inline-flex;">
                ${plot.status.charAt(0).toUpperCase() + plot.status.slice(1)}
              </span>
            </div>
            ${plot.area ? `<p class="text-sm text-gray-600">Area: ${formatArea(plot.area)}</p>` : ''}
            <a href="/plots/${plot.id}" class="text-emerald-600 hover:underline text-sm font-medium mt-2 inline-block">
              View Details →
            </a>
          </div>
        `;

        marker.bindPopup(popupContent, {
          maxWidth: 300,
          minWidth: 250,
          className: 'plot-popup'
        }).addTo(map);
      });

      // Fit bounds to show all markers if there are any plots
      if (plots.length > 0 && plots.some(plot => plot.points && plot.points.length > 0)) {
        const markers = plots
          .filter(plot => plot.points && plot.points.length > 0)
          .map(plot => {
            const center = plot.points.reduce(
              (acc, point) => {
                acc.lat += point.lat;
                acc.lng += point.lng;
                return acc;
              },
              { lat: 0, lng: 0 }
            );
            return [center.lat / plot.points.length, center.lng / plot.points.length];
          });
        
        // Add some padding around the bounds
        map.fitBounds(markers, { 
          padding: [50, 50],
          maxZoom: 15
        });
      }
    } catch (error) {
      console.error('Error initializing map:', error);
      status.set('Failed to load map. Please try refreshing the page.');
    }
  }

  function formatArea(area) {
    if (typeof area !== 'number' || isNaN(area) || area <= 0) return '0 acres';
    return `${area.toFixed(2)} acres`;
  }

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
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" crossorigin=""/>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</svelte:head>

<div class="dashboard-wrapper">
  <!-- Mobile Header -->
  <header class="mobile-header">
    <button class="menu-toggle" on:click={toggleMobileMenu} aria-label="Toggle menu">
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
    <div class="overlay" on:click={closeMobileMenu} transition:fade={{ duration: 200 }}></div>
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
      <a href="/dashboard" class="nav-item active" on:click={closeMobileMenu}>
        <span class="nav-icon">📊</span>
        <span>Dashboard</span>
      </a>
      <a href="/register-plot" class="nav-item" on:click={closeMobileMenu}>
        <span class="nav-icon">➕</span>
        <span>Register Plot</span>
      </a>
      <a href="/plots" class="nav-item" on:click={closeMobileMenu}>
        <span class="nav-icon">📋</span>
        <span>My Plots</span>
      </a>
      <a href="/map" class="nav-item" on:click={closeMobileMenu}>
        <span class="nav-icon">🗺️</span>
        <span>Map View</span>
      </a>
      <a href="/profile" class="nav-item" on:click={closeMobileMenu}>
        <span class="nav-icon">👤</span>
        <span>Profile</span>
      </a>
    </nav>

    <div class="sidebar-footer">
      <button on:click={logout} class="logout-btn">
        <span>🚪</span>
        <span>Logout</span>
      </button>
    </div>
  </aside>

  <!-- Main Content -->
  <main class="main-content">
    <div class="content-header">
      <div>
        <h1 class="page-title">Dashboard</h1>
        <p class="page-subtitle">Welcome back! Here's your land registry overview.</p>
      </div>
    </div>

    {#if loading}
      <div class="loading-state">
        <div class="spinner"></div>
        <p>Loading dashboard...</p>
      </div>
    {:else}
      <!-- Stats Grid -->
      <div class="stats-grid">
        <div class="stat-card stat-primary">
          <div class="stat-icon">📋</div>
          <div class="stat-content">
            <div class="stat-value">{stats.total}</div>
            <div class="stat-label">Total Plots</div>
          </div>
        </div>

        <div class="stat-card stat-warning">
          <div class="stat-icon">⏳</div>
          <div class="stat-content">
            <div class="stat-value">{stats.pending}</div>
            <div class="stat-label">Pending</div>
          </div>
        </div>

        <div class="stat-card stat-success">
          <div class="stat-icon">✅</div>
          <div class="stat-content">
            <div class="stat-value">{stats.approved}</div>
            <div class="stat-label">Approved</div>
          </div>
        </div>

        <div class="stat-card stat-info">
          <div class="stat-icon">📐</div>
          <div class="stat-content">
            <div class="stat-value">{formatArea(stats.totalArea)}</div>
            <div class="stat-label">Total Area</div>
          </div>
        </div>
      </div>

      <!-- Content Grid -->
      <div class="content-grid">
        <!-- Recent Plots -->
        <div class="card recent-plots">
          <div class="card-header">
            <h2>Recent Plots</h2>
          </div>
          <div class="plot-list">
            {#if userPlots.length === 0}
              <div class="empty-state">
                <p>No plots found.</p>
                <a href="/register-plot" class="link">Register your first plot</a>
              </div>
            {:else}
              {#each userPlots.slice(0, 5) as plot}
                <a href={`/plots/${plot.id}`} class="plot-item">
                  <div class="plot-info">
                    <div class="plot-name">{plot.plot_name || 'Unnamed Plot'}</div>
                    <div class="plot-date">{new Date(plot.created_at).toLocaleDateString()}</div>
                    {#if plot.area}
                      <div class="plot-area">Area: {formatArea(plot.area)}</div>
                    {/if}
                  </div>
                  <span class="status-badge status-{plot.status}">
                    {plot.status}
                  </span>
                </a>
              {/each}
            {/if}
          </div>
          {#if userPlots.length > 0}
            <div class="card-footer">
              <a href="/plots" class="link">View all plots →</a>
            </div>
          {/if}
        </div>

        <!-- Sidebar Content -->
        <div class="sidebar-content">
          <!-- Quick Actions -->
          <div class="card quick-actions">
            <div class="card-header">
              <h2>Quick Actions</h2>
            </div>
            <div class="action-list">
              <a href="/register-plot" class="action-item action-primary">
                <span class="action-icon">➕</span>
                <span>Register New Plot</span>
              </a>
              <a href="/profile" class="action-item action-secondary">
                <span class="action-icon">👤</span>
                <span>Update Profile</span>
              </a>
              <a href="/help" class="action-item action-tertiary">
                <span class="action-icon">❓</span>
                <span>Get Help</span>
              </a>
            </div>
          </div>

          <!-- Chart -->
          <div class="card chart-card">
            <div class="card-header">
              <h2>Monthly Registrations</h2>
            </div>
            <div class="chart-container">
              <SimpleBarChart 
                data={chartData.series[0].values} 
                labels={chartData.labels} 
                barColor="#0d9488"
                height="200px"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Map -->
      <div class="card map-card">
        <div class="card-header">
          <h2>Your Plots on Map</h2>
          <a href="/map" class="link">View Full Map →</a>
        </div>
        <div id="dashboard-map" class="map-container"></div>
      </div>
    {/if}
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
  }

  .content-header {
    margin-bottom: 2rem;
  }

  .page-title {
    font-size: 2rem;
    font-weight: 700;
    color: #1e293b;
    margin: 0 0 0.5rem 0;
  }

  .page-subtitle {
    color: #64748b;
    font-size: 1rem;
  }

  /* Loading */
  .loading-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 4rem;
    gap: 1rem;
    color: #64748b;
  }

  .spinner {
    width: 48px;
    height: 48px;
    border: 4px solid #e2e8f0;
    border-top-color: #0d9488;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  /* Stats Grid */
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
  }

  .stat-card {
    background: white;
    border-radius: 16px;
    padding: 1.5rem;
    display: flex;
    align-items: center;
    gap: 1rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    border: 1px solid #e2e8f0;
    transition: all 0.3s;
  }

  .stat-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 16px rgba(0,0,0,0.08);
  }

  .stat-icon {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5rem;
    flex-shrink: 0;
  }

  .stat-primary .stat-icon { background: #e0f2f1; }
  .stat-warning .stat-icon { background: #fff4e6; }
  .stat-success .stat-icon { background: #dcfce7; }
  .stat-info .stat-icon { background: #dbeafe; }

  .stat-value {
    font-size: 1.875rem;
    font-weight: 700;
    color: #1e293b;
  }

  .stat-label {
    font-size: 0.875rem;
    color: #64748b;
    font-weight: 500;
  }

  /* Content Grid */
  .content-grid {
    display: grid;
    grid-template-columns: 1fr 380px;
    gap: 1.5rem;
    margin-bottom: 2rem;
  }

  /* Card */
  .card {
    background: white;
    border-radius: 16px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    border: 1px solid #e2e8f0;
    overflow: hidden;
  }

  .card-header {
    padding: 1.25rem 1.5rem;
    border-bottom: 1px solid #e2e8f0;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .card-header h2 {
    font-size: 1.125rem;
    font-weight: 600;
    color: #1e293b;
    margin: 0;
  }

  .card-footer {
    padding: 1rem 1.5rem;
    border-top: 1px solid #e2e8f0;
    text-align: right;
  }

  /* Plot List */
  .plot-list {
    padding: 0.5rem;
  }

  .plot-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem;
    border-radius: 12px;
    margin-bottom: 0.5rem;
    text-decoration: none;
    color: inherit;
    transition: all 0.2s;
  }

  .plot-item:hover {
    background: #f8faf9;
  }

  .plot-name {
    font-weight: 600;
    color: #1e293b;
    margin-bottom: 0.25rem;
  }

  .plot-date, .plot-area {
    font-size: 0.875rem;
    color: #64748b;
  }

  .status-badge {
    padding: 0.25rem 0.75rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: capitalize;
    white-space: nowrap;
  }

  .status-pending { background: #fef3c7; color: #92400e; }
  .status-approved { background: #dcfce7; color: #166534; }
  .status-rejected { background: #fee2e2; color: #991b1b; }

  .empty-state {
    padding: 2rem;
    text-align: center;
    color: #64748b;
  }
  
  /* Map Container */
  .map-container {
    height: 400px;
    width: 100%;
    border-radius: 0 0 16px 16px;
    overflow: hidden;
  }
  
  .map-card {
    margin-bottom: 2rem;
  }

  /* Map Marker Styles */
  .plot-marker {
    background: none !important;
    border: none !important;
  }

  .marker-inner {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: bold;
    font-size: 14px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.3);
    border: 2px solid white;
    transition: all 0.2s ease;
  }

  .marker-inner:hover {
    transform: scale(1.1);
    z-index: 1000;
  }

  /* Popup Styles */
  .plot-popup {
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.15);
    border: none;
    padding: 0;
    overflow: hidden;
  }

  .plot-popup .leaflet-popup-content-wrapper {
    padding: 0;
    border-radius: 12px;
    overflow: hidden;
  }

  .plot-popup .leaflet-popup-content {
    margin: 0;
    width: 100% !important;
  }

  .popup-content {
    padding: 1rem;
  }

  .plot-popup .leaflet-popup-tip {
    background: white;
    box-shadow: -1px -1px 2px rgba(0,0,0,0.1);
  }

  .status-badge {
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: capitalize;
    white-space: nowrap;
  }

  .status-pending { background: #fef3c7; color: #92400e; }
  .status-approved { background: #dcfce7; color: #166534; }
  .status-rejected { background: #fee2e2; color: #991b1b; }

  /* Quick Actions */
  .action-list {
    padding: 0.5rem;
  }

  .action-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 1rem;
    border-radius: 12px;
    text-decoration: none;
    font-weight: 500;
    margin-bottom: 0.5rem;
    transition: all 0.2s;
  }

  .action-icon {
    width: 36px;
    height: 36px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.25rem;
  }

  .action-primary {
    background: linear-gradient(135deg, #0d9488, #10b981);
    color: white;
  }

  .action-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(13, 148, 136, 0.3);
  }

  .action-secondary {
    background: #f1f5f9;
    color: #475569;
  }

  .action-secondary:hover {
    background: #e2e8f0;
  }

  .action-tertiary {
    background: #fef3c7;
    color: #92400e;
  }

  .action-tertiary:hover {
    background: #fde68a;
  }

  /* Map */
  .map-card {
    height: 400px;
  }

  .map-container {
    height: calc(100% - 60px);
  }

  #dashboard-map {
    width: 100%;
    height: 100%;
  }

  :global(.leaflet-container) {
    height: 100% !important;
  }

  /* Chart */
  .chart-container {
    padding: 1.5rem;
  }

  /* Links */
  .link {
    color: #0d9488;
    text-decoration: none;
    font-weight: 600;
    font-size: 0.875rem;
  }

  .link:hover {
    text-decoration: underline;
  }

  /* Responsive - Tablet */
  @media (max-width: 1200px) {
    .content-grid {
      grid-template-columns: 1fr;
    }
    
    .stats-grid {
      grid-template-columns: repeat(2, 1fr);
    }
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

    .page-title {
      font-size: 1.5rem;
    }

    .page-subtitle {
      font-size: 0.875rem;
    }

    .stats-grid {
      grid-template-columns: 1fr;
      gap: 1rem;
    }

    .stat-card {
      padding: 1.25rem;
    }

    .stat-value {
      font-size: 1.5rem;
    }

    .content-grid {
      gap: 1rem;
    }

    .card-header {
      padding: 1rem;
      flex-wrap: wrap;
      gap: 0.5rem;
    }

    .plot-item {
      flex-direction: column;
      align-items: flex-start;
      gap: 0.75rem;
    }

    .status-badge {
      align-self: flex-start;
    }

    .map-card {
      height: 300px;
    }

    .action-item {
      padding: 0.875rem;
    }

    .chart-container {
      padding: 1rem;
    }
  }

  /* Responsive - Small Mobile */
  @media (max-width: 480px) {
    .main-content {
      padding: 0.75rem;
    }

    .content-header {
      margin-bottom: 1.5rem;
    }

    .page-title {
      font-size: 1.25rem;
    }

    .stat-icon {
      width: 40px;
      height: 40px;
      font-size: 1.25rem;
    }

    .stat-value {
      font-size: 1.25rem;
    }

    .stat-label {
      font-size: 0.75rem;
    }

    .card-header h2 {
      font-size: 1rem;
    }

    .plot-name {
      font-size: 0.9rem;
    }

    .plot-date, .plot-area {
      font-size: 0.75rem;
    }
  }
</style>