<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { browser } from '$app/environment';

  onMount(() => {
    if (!browser) return;
    
    if (!localStorage.getItem('token')) {
      goto('/login');
      return;
    }
  });
</script>

<div class="official-dashboard">
  <!-- Professional Navigation -->
  <nav class="professional-nav">
    <div class="nav-brand">
      <span class="brand-text">Land Registry Official Portal</span>
    </div>
    <div class="nav-menu">
      <a href="/dashboard/official" class="nav-item active">Dashboard</a>
      <a href="/dashboard/official/caseload" class="nav-item">My Caseload</a>
      <a href="/register-plot" class="nav-item">Registration</a>
      <a href="/map" class="nav-item">Map View</a>
      <a href="/profile" class="nav-item">Account</a>
    </div>
  </nav>

  <div class="dashboard-header">
    <h1>Official Dashboard</h1>
    <p>Land Registry Officer Portal</p>
  </div>

  <div class="action-cards">
    <a href="/dashboard/official/caseload" class="action-card">
      <div class="card-icon">📋</div>
      <h3>My Caseload</h3>
      <p>View and manage pending applications</p>
    </a>

    <a href="/dashboard/register-citizen" class="action-card">
      <div class="card-icon">👥</div>
      <h3>Register Citizen</h3>
      <p>Onboard new citizens to LandLock</p>
    </a>

    <a href="/dashboard/official/verified" class="action-card">
      <div class="card-icon">✅</div>
      <h3>Verified Claims</h3>
      <p>View recently verified land claims</p>
    </a>

    <a href="/dashboard/official/reports" class="action-card">
      <div class="card-icon">📊</div>
      <h3>Reports</h3>
      <p>Generate activity and status reports</p>
    </a>
  </div>
</div>

<style>
  .official-dashboard {
    padding: 2rem;
    max-width: 1200px;
    margin: 0 auto;
  }

  .dashboard-header {
    text-align: center;
    margin-bottom: 3rem;
  }

  .dashboard-header h1 {
    font-size: 2.5rem;
    font-weight: 700;
    color: #1e293b;
    margin-bottom: 0.5rem;
  }

  .dashboard-header p {
    font-size: 1.125rem;
    color: #64748b;
  }

  /* Professional Navigation */
  .professional-nav {
    background: #ffffff;
    border-bottom: 1px solid #e5e7eb;
    padding: 0 2rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 64px;
    margin-bottom: 2rem;
  }

  .nav-brand {
    display: flex;
    align-items: center;
  }

  .brand-text {
    font-size: 1.25rem;
    font-weight: 600;
    color: #111827;
  }

  .nav-menu {
    display: flex;
    gap: 0.5rem;
  }

  .nav-item {
    padding: 0.5rem 1rem;
    border-radius: 4px;
    text-decoration: none;
    font-weight: 500;
    color: #6b7280;
    transition: all 0.2s;
  }

  .nav-item:hover {
    background: #f3f4f6;
    color: #111827;
  }

  .nav-item.active {
    background: #2563eb;
    color: white;
  }

  .action-cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
  }

  .action-card {
    background: white;
    border-radius: 16px;
    padding: 2rem;
    text-decoration: none;
    color: inherit;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    transition: all 0.3s ease;
    border: 2px solid transparent;
  }

  .action-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
    border-color: #0d9488;
  }

  .card-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
  }

  .action-card h3 {
    font-size: 1.5rem;
    font-weight: 600;
    color: #1e293b;
    margin-bottom: 0.5rem;
  }

  .action-card p {
    color: #64748b;
    line-height: 1.6;
  }

  @media (max-width: 768px) {
    .official-dashboard {
      padding: 1rem;
    }

    .action-cards {
      grid-template-columns: 1fr;
      gap: 1rem;
    }

    .action-card {
      padding: 1.5rem;
    }
  }
</style>
