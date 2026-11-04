<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { browser } from '$app/environment';
  import { ClipboardList, UserPlus, CheckCircle, BarChart3, Users, Map, Activity, TrendingUp, Shield } from 'lucide-svelte';
  import Navbar from '$lib/components/Navbar.svelte';

  const API = 'http://localhost:5000';

  let dashboardStats = {
    total_plots: 0,
    total_users: 0,
    total_transactions: 0,
    plot_status: {},
    transaction_status: {},
    recent_activity: [],
    plots_by_user: {}
  };
  let isLoading = true;

  function authHeaders() {
    return { 'Authorization': `Bearer ${localStorage.getItem('token')}` };
  }

  async function fetchDashboardStats() {
    try {
      const res = await fetch(`${API}/api/dashboard/official/stats`, { headers: authHeaders() });
      if (res.ok) {
        const data = await res.json();
        dashboardStats = data;
      }
    } catch (err) {
      console.error('Error fetching dashboard stats:', err);
    } finally {
      isLoading = false;
    }
  }

  onMount(async () => {
    if (!browser) return;
    
    if (!localStorage.getItem('token')) {
      goto('/login');
      return;
    }

    try {
      const res = await fetch(`${API}/api/user/me`, { headers: authHeaders() });
      if (res.ok) {
        const u = await res.json();
        if (!u.is_superuser && !u.is_staff) {
          goto('/dashboard');
          return;
        }
      } else {
        goto('/login');
      }
    } catch (err) {
      console.error('Error verifying admin status:', err);
      goto('/login');
    }

    fetchDashboardStats();
  });

  function timeAgo(isoString: string): string {
    if (!isoString) return '';
    const diff = Date.now() - new Date(isoString).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    return `${Math.floor(hrs / 24)}d ago`;
  }

  function getStatusColor(status: string): string {
    switch (status) {
      case 'pending': return '#f59e0b';
      case 'approved': return '#10b981';
      case 'verified': return '#007A3D';
      case 'rejected': return '#ef4444';
      case 'completed': return '#10b981';
      case 'in_progress': return '#3b82f6';
      case 'cancelled': return '#6b7280';
      default: return '#6b7280';
    }
  }
</script>

<div class="official-dashboard">
  <!-- Professional Navigation -->
  <Navbar userType="official" activeLink="/dashboard/official" userName="Official" showNotification={false} />

  <!-- Main Content -->
  <main class="main-content">
    <div class="dashboard-header">
      <h1>Official Dashboard</h1>
      <p>Land Registry Officer Portal</p>
    </div>

    {#if isLoading}
      <div class="loading-state">
        <p>Loading dashboard data...</p>
      </div>
    {:else}
      <!-- Stats Grid -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon">
            <Map size={24} />
          </div>
          <div class="stat-content">
            <div class="stat-value">{dashboardStats.total_plots}</div>
            <div class="stat-label">Total Plots</div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon">
            <Users size={24} />
          </div>
          <div class="stat-content">
            <div class="stat-value">{dashboardStats.total_users}</div>
            <div class="stat-label">Total Users</div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon">
            <Activity size={24} />
          </div>
          <div class="stat-content">
            <div class="stat-value">{dashboardStats.total_transactions}</div>
            <div class="stat-label">Transactions</div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon">
            <TrendingUp size={24} />
          </div>
          <div class="stat-content">
            <div class="stat-value">{Object.keys(dashboardStats.plots_by_user).length}</div>
            <div class="stat-label">Active Landowners</div>
          </div>
        </div>
      </div>

      <!-- Content Grid -->
      <div class="content-grid">
        <!-- Main Column -->
        <div class="main-column">
          <!-- Plot Status Breakdown -->
          <div class="card">
            <div class="card-header">
              <h2>Plot Status Breakdown</h2>
            </div>
            <div class="card-body">
              {#if Object.keys(dashboardStats.plot_status).length > 0}
                <div class="status-breakdown">
                  {#each Object.entries(dashboardStats.plot_status) as [status, count]}
                    <div class="status-item">
                      <div class="status-label">{status}</div>
                      <div class="status-bar">
                        <div class="status-fill" style="width: {(count / dashboardStats.total_plots * 100)}%; background: {getStatusColor(status)};"></div>
                      </div>
                      <div class="status-count">{count}</div>
                    </div>
                  {/each}
                </div>
              {:else}
                <div class="empty-state">
                  <p>No plot data available</p>
                </div>
              {/if}
            </div>
          </div>

          <!-- Transaction Status Breakdown -->
          <div class="card">
            <div class="card-header">
              <h2>Transaction Status</h2>
            </div>
            <div class="card-body">
              {#if Object.keys(dashboardStats.transaction_status).length > 0}
                <div class="status-breakdown">
                  {#each Object.entries(dashboardStats.transaction_status) as [status, count]}
                    <div class="status-item">
                      <div class="status-label">{status}</div>
                      <div class="status-bar">
                        <div class="status-fill" style="width: {(count / dashboardStats.total_transactions * 100)}%; background: {getStatusColor(status)};"></div>
                      </div>
                      <div class="status-count">{count}</div>
                    </div>
                  {/each}
                </div>
              {:else}
                <div class="empty-state">
                  <p>No transaction data available</p>
                </div>
              {/if}
            </div>
          </div>
        </div>

        <!-- Sidebar -->
        <aside class="sidebar">
          <!-- Quick Actions -->
          <div class="card">
            <div class="card-header">
              <h3>Quick Actions</h3>
            </div>
            <div class="card-body">
              <div class="action-list">
                <a href="/dashboard/official/caseload" class="action-item">
                  <div class="action-icon">
                    <ClipboardList size={20} />
                  </div>
                  <div class="action-content">
                    <div class="action-title">My Caseload</div>
                    <div class="action-desc">View pending applications</div>
                  </div>
                </a>

                <a href="/dashboard/register-citizen" class="action-item">
                  <div class="action-icon">
                    <UserPlus size={20} />
                  </div>
                  <div class="action-content">
                    <div class="action-title">Register Citizen</div>
                    <div class="action-desc">Onboard new users</div>
                  </div>
                </a>

                <a href="/dashboard/official/register-chief" class="action-item">
                  <div class="action-icon">
                    <Shield size={20} />
                  </div>
                  <div class="action-content">
                    <div class="action-title">Register Chief</div>
                    <div class="action-desc">Register chiefs & assign jurisdictions</div>
                  </div>
                </a>

                <a href="/dashboard/official/verified" class="action-item">
                  <div class="action-icon">
                    <CheckCircle size={20} />
                  </div>
                  <div class="action-content">
                    <div class="action-title">Verified Claims</div>
                    <div class="action-desc">View verified plots</div>
                  </div>
                </a>

                <a href="/dashboard/official/reports" class="action-item">
                  <div class="action-icon">
                    <BarChart3 size={20} />
                  </div>
                  <div class="action-content">
                    <div class="action-title">Reports</div>
                    <div class="action-desc">Generate reports</div>
                  </div>
                </a>
              </div>
            </div>
          </div>

          <!-- Recent Activity -->
          <div class="card">
            <div class="card-header">
              <h3>Recent Activity</h3>
            </div>
            <div class="card-body">
              {#if dashboardStats.recent_activity.length > 0}
                <div class="timeline">
                  {#each dashboardStats.recent_activity as activity (activity.created_at)}
                    <div class="timeline-item">
                      <div class="timeline-dot" style="background: {activity.type === 'plot_registered' ? '#007A3D' : '#0D6EFD'};"></div>
                      <div class="timeline-content">
                        <div class="timeline-title">{activity.title}</div>
                        <div class="timeline-time">{timeAgo(activity.created_at)}</div>
                      </div>
                    </div>
                  {/each}
                </div>
              {:else}
                <div class="empty-state">
                  <p>No recent activity</p>
                </div>
              {/if}
            </div>
          </div>
        </aside>
      </div>
    {/if}
  </main>
</div>

<style>
  .official-dashboard {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  .main-content {
    max-width: 1400px;
    margin: 0 auto;
    padding: 2rem;
    width: 100%;
    flex: 1;
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

  /* Stats Grid */
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
  }

  .stat-card {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    border: 1px solid #e2e8f0;
    display: flex;
    align-items: center;
    gap: 1rem;
    transition: all 0.2s;
  }

  .stat-card:hover {
    border-color: #cbd5e1;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
    transform: translateY(-2px);
  }

  .stat-icon {
    width: 48px;
    height: 48px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    color: #007A3D;
  }

  .stat-content {
    flex: 1;
  }

  .stat-value {
    font-size: 2rem;
    font-weight: 700;
    color: #0f172a;
    line-height: 1;
    margin-bottom: 0.25rem;
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
    gap: 2rem;
  }

  .main-column {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  /* Card */
  .card {
    background: white;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
    overflow: hidden;
  }

  .card-header {
    padding: 1.5rem;
    border-bottom: 1px solid #e2e8f0;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .card-header h2,
  .card-header h3 {
    font-size: 1.125rem;
    font-weight: 700;
    color: #0f172a;
  }

  .card-body {
    padding: 1.5rem;
  }

  /* Status Breakdown */
  .status-breakdown {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .status-item {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .status-label {
    width: 100px;
    font-size: 0.875rem;
    font-weight: 600;
    color: #374151;
    text-transform: capitalize;
  }

  .status-bar {
    flex: 1;
    height: 8px;
    background: #f1f5f9;
    border-radius: 4px;
    overflow: hidden;
  }

  .status-fill {
    height: 100%;
    border-radius: 4px;
    transition: width 0.3s ease;
  }

  .status-count {
    width: 40px;
    text-align: right;
    font-weight: 700;
    color: #0f172a;
  }

  /* Empty State */
  .empty-state {
    text-align: center;
    padding: 2rem;
    color: #64748b;
  }

  /* Sidebar */
  .sidebar {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  /* Action List */
  .action-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .action-item {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem;
    border-radius: 8px;
    background: #f8fafc;
    text-decoration: none;
    transition: all 0.2s;
  }

  .action-item:hover {
    background: #f1f5f9;
    transform: translateX(4px);
  }

  .action-icon {
    width: 40px;
    height: 40px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    color: #007A3D;
  }

  .action-content {
    flex: 1;
  }

  .action-title {
    font-weight: 600;
    color: #0f172a;
    font-size: 0.9375rem;
  }

  .action-desc {
    font-size: 0.8125rem;
    color: #64748b;
  }

  /* Timeline */
  .timeline {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .timeline-item {
    display: flex;
    gap: 1rem;
  }

  .timeline-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    margin-top: 4px;
    flex-shrink: 0;
  }

  .timeline-content {
    flex: 1;
  }

  .timeline-title {
    font-weight: 600;
    color: #0f172a;
    font-size: 0.9375rem;
    margin-bottom: 0.125rem;
  }

  .timeline-time {
    font-size: 0.8125rem;
    color: #94a3b8;
  }

  @media (max-width: 1024px) {
    .content-grid {
      grid-template-columns: 1fr;
    }

    .sidebar {
      order: -1;
    }
  }

  @media (max-width: 768px) {
    .main-content {
      padding: 1rem;
    }

    .stats-grid {
      grid-template-columns: repeat(2, 1fr);
      gap: 1rem;
    }

    .dashboard-header {
      flex-direction: column;
      align-items: flex-start;
    }
  }

  @media (max-width: 480px) {
    .stats-grid {
      grid-template-columns: 1fr;
    }
  }
</style>
