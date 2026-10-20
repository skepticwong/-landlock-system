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

<div class="chief-dashboard">
  <div class="dashboard-header">
    <h1>Chief Dashboard</h1>
    <p>Village Authority Land Management Portal</p>
  </div>

  <div class="stats-grid">
    <div class="stat-card">
      <div class="stat-icon">📋</div>
      <div class="stat-content">
        <div class="stat-value">12</div>
        <div class="stat-label">Pending Claims</div>
      </div>
    </div>

    <div class="stat-card">
      <div class="stat-icon">✅</div>
      <div class="stat-content">
        <div class="stat-value">45</div>
        <div class="stat-label">Verified This Month</div>
      </div>
    </div>

    <div class="stat-card">
      <div class="stat-icon">🏘️</div>
      <div class="stat-content">
        <div class="stat-value">234</div>
        <div class="stat-label">Total Households</div>
      </div>
    </div>

    <div class="stat-card">
      <div class="stat-icon">📊</div>
      <div class="stat-content">
        <div class="stat-value">89%</div>
        <div class="stat-label">Registration Rate</div>
      </div>
    </div>
  </div>

  <div class="action-cards">
    <a href="/dashboard/chief/pending" class="action-card">
      <div class="card-icon">⏳</div>
      <h3>Pending Claims</h3>
      <p>Review and verify land claims from villagers</p>
    </a>

    <a href="/dashboard/chief/verified" class="action-card">
      <div class="card-icon">✅</div>
      <h3>Verified Claims</h3>
      <p>View all verified land registrations</p>
    </a>

    <a href="/dashboard/chief/disputed" class="action-card">
      <div class="card-icon">⚠️</div>
      <h3>Disputed Claims</h3>
      <p>Manage and resolve land disputes</p>
    </a>

    <a href="/dashboard/chief/reports" class="action-card">
      <div class="card-icon">📊</div>
      <h3>Village Reports</h3>
      <p>Generate land registry reports</p>
    </a>
  </div>

  <div class="recent-activity">
    <h2>Recent Activity</h2>
    <div class="activity-list">
      <div class="activity-item">
        <div class="activity-icon">👥</div>
        <div class="activity-content">
          <strong>Grace Banda</strong> submitted land claim for MLW-LIL-8821
          <div class="activity-time">2 hours ago</div>
        </div>
      </div>
      
      <div class="activity-item">
        <div class="activity-icon">✅</div>
        <div class="activity-content">
          <strong>James Phiri</strong> claim verified for MLW-TAK-5532
          <div class="activity-time">5 hours ago</div>
        </div>
      </div>
      
      <div class="activity-item">
        <div class="activity-icon">⚠️</div>
        <div class="activity-content">
          <strong>Dispute filed</strong> on MLW-BT-4412 by Village Headman Jere
          <div class="activity-time">1 day ago</div>
        </div>
      </div>
    </div>
  </div>
</div>

<style>
  .chief-dashboard {
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

  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1.5rem;
    margin-bottom: 3rem;
  }

  .stat-card {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    display: flex;
    align-items: center;
    gap: 1rem;
    border: 2px solid #e2e8f0;
    transition: all 0.3s ease;
  }

  .stat-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 15px rgba(0, 0, 0, 0.15);
    border-color: #0d9488;
  }

  .stat-icon {
    font-size: 2rem;
  }

  .stat-value {
    font-size: 2rem;
    font-weight: 700;
    color: #1e293b;
    line-height: 1;
  }

  .stat-label {
    color: #64748b;
    font-size: 0.875rem;
    font-weight: 500;
  }

  .action-cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
    margin-bottom: 3rem;
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

  .recent-activity {
    background: white;
    border-radius: 16px;
    padding: 2rem;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    border: 2px solid #e2e8f0;
  }

  .recent-activity h2 {
    font-size: 1.5rem;
    font-weight: 600;
    color: #1e293b;
    margin-bottom: 1.5rem;
  }

  .activity-list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .activity-item {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    padding: 1rem;
    border-radius: 8px;
    background: #f8fafc;
    transition: background-color 0.2s;
  }

  .activity-item:hover {
    background: #f1f5f9;
  }

  .activity-icon {
    font-size: 1.5rem;
    flex-shrink: 0;
  }

  .activity-content {
    flex: 1;
  }

  .activity-time {
    font-size: 0.875rem;
    color: #64748b;
    margin-top: 0.25rem;
  }

  @media (max-width: 768px) {
    .chief-dashboard {
      padding: 1rem;
    }

    .stats-grid {
      grid-template-columns: repeat(2, 1fr);
      gap: 1rem;
    }

    .action-cards {
      grid-template-columns: 1fr;
      gap: 1rem;
    }

    .action-card {
      padding: 1.5rem;
    }

    .recent-activity {
      padding: 1.5rem;
    }
  }
</style>
