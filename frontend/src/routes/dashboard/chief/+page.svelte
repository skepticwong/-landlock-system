<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { browser } from '$app/environment';
  import { Clipboard, Check, Home, BarChart, AlertTriangle, Users, FileText, Clock } from 'lucide-svelte';
  import Navbar from '$lib/components/Navbar.svelte';

  const API = 'http://localhost:5000';

  let currentUser = null;
  let dashboardStats = {
    pending_claims: 0,
    verified_this_month: 0,
    total_households: 0,
    registration_rate: 0,
    pending_transactions: 0
  };
  let recentActivity = [];
  let isLoading = true;

  function authHeaders() {
    return { 'Authorization': `Bearer ${localStorage.getItem('token')}` };
  }

  async function fetchCurrentUser() {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API}/api/user/me`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        currentUser = await response.json();
      } else {
        goto('/login');
      }
    } catch (error) {
      console.error('Failed to fetch user:', error);
      goto('/login');
    }
  }

  async function fetchDashboardStats() {
    try {
      const response = await fetch(`${API}/api/chief/dashboard-stats`, { headers: authHeaders() });
      if (response.ok) {
        dashboardStats = await response.json();
      }
    } catch (error) {
      console.error('Failed to fetch dashboard stats:', error);
    }
  }

  async function fetchRecentActivity() {
    try {
      const response = await fetch(`${API}/api/chief/recent-activity`, { headers: authHeaders() });
      if (response.ok) {
        recentActivity = await response.json();
      }
    } catch (error) {
      console.error('Failed to fetch recent activity:', error);
    }
  }

  function formatTime(dateString: string): string {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} minutes ago`;
    if (diffHours < 24) return `${diffHours} hours ago`;
    return `${diffDays} days ago`;
  }

  onMount(async () => {
    if (!browser) return;
    
    if (!localStorage.getItem('token')) {
      goto('/login');
      return;
    }
    
    await fetchCurrentUser();
    await Promise.all([fetchDashboardStats(), fetchRecentActivity()]);
    isLoading = false;
  });
</script>

<div class="chief-dashboard">
  <Navbar userType="chief" activeLink="/dashboard/chief" userName={currentUser?.full_name || 'Chief'} showNotification={false} />

  <div class="dashboard-header">
    <h1>Chief Dashboard</h1>
    <p>Village Authority Land Management Portal</p>
  </div>

  {#if isLoading}
    <div class="loading-state">
      <p>Loading dashboard data...</p>
    </div>
  {:else}
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon"><Clipboard class="w-8 h-8" /></div>
        <div class="stat-content">
          <div class="stat-value">{dashboardStats.pending_claims}</div>
          <div class="stat-label">Pending Claims</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon"><Check class="w-8 h-8" /></div>
        <div class="stat-content">
          <div class="stat-value">{dashboardStats.verified_this_month}</div>
          <div class="stat-label">Verified This Month</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon"><Home class="w-8 h-8" /></div>
        <div class="stat-content">
          <div class="stat-value">{dashboardStats.total_households}</div>
          <div class="stat-label">Total Households</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon"><BarChart class="w-8 h-8" /></div>
        <div class="stat-content">
          <div class="stat-value">{dashboardStats.registration_rate}%</div>
          <div class="stat-label">Registration Rate</div>
        </div>
      </div>
    </div>

  <div class="action-cards">
    <a href="/dashboard/chief/pending" class="action-card">
      <div class="card-icon"><Clock class="w-6 h-6" /></div>
      <h3>Pending Claims</h3>
      <p>Review and verify land claims from villagers</p>
    </a>

    <a href="/dashboard/chief/verified" class="action-card">
      <div class="card-icon"><Check class="w-6 h-6" /></div>
      <h3>Verified Claims</h3>
      <p>View all verified land registrations</p>
    </a>

    <a href="/dashboard/chief/disputed" class="action-card">
      <div class="card-icon"><AlertTriangle class="w-6 h-6" /></div>
      <h3>Disputed Claims</h3>
      <p>Manage and resolve land disputes</p>
    </a>

    <a href="/dashboard/chief/reports" class="action-card">
      <div class="card-icon"><BarChart class="w-6 h-6" /></div>
      <h3>Village Reports</h3>
      <p>Generate land registry reports</p>
    </a>
  </div>

  <div class="recent-activity">
    <h2>Recent Activity</h2>
    {#if recentActivity.length === 0}
      <div class="empty-activity">
        <p>No recent activity in your jurisdiction</p>
      </div>
    {:else}
      <div class="activity-list">
        {#each recentActivity as activity}
          <div class="activity-item">
            <div class="activity-icon">
              {#if activity.type === 'claim_submitted'}
                <Users class="w-5 h-5" />
              {:else if activity.type === 'claim_verified'}
                <Check class="w-5 h-5" />
              {:else}
                <AlertTriangle class="w-5 h-5" />
              {/if}
            </div>
            <div class="activity-content">
              <strong>{activity.owner_name}</strong> {activity.type === 'claim_submitted' ? 'submitted' : 'verified'} land claim for {activity.plot_name}
              <div class="activity-time">{formatTime(activity.created_at)}</div>
            </div>
          </div>
        {/each}
      </div>
    {/if}
  </div>
  {/if}
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

  .loading-state {
    text-align: center;
    padding: 4rem;
    color: #64748b;
  }

  .empty-activity {
    text-align: center;
    padding: 2rem;
    color: #94a3b8;
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
    border-color: var(--color-primary);
  }

  .stat-icon {
    font-size: 2rem;
    color: var(--color-primary);
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
    border-color: var(--color-primary);
  }

  .card-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
    color: var(--color-primary);
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
