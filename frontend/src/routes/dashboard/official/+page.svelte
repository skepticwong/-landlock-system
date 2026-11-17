<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { browser } from '$app/environment';
  import { ClipboardList, UserPlus, CheckCircle, BarChart3, Users, Map, Activity, TrendingUp, Shield, FolderOpen, Percent, MapPin, Landmark, Camera, CalendarDays, ChevronRight } from 'lucide-svelte';
  import Navbar from '$lib/components/Navbar.svelte';

  const API = 'http://localhost:5000';

  let dashboardUserName = 'Official';
  let dashboardStats = {
    total_plots: 0,
    total_users: 0,
    total_transactions: 0,
    plot_status: {} as Record<string, number>,
    transaction_status: {} as Record<string, number>,
    recent_activity: [] as any[],
    plots_by_user: {} as Record<string, number>,
    pending_claims: 0,
    approval_rate: null as number | null,
    boundary_mapped_pct: 0,
    protected_plots: 0,
    plots_with_media: 0,
    new_this_week: 0,
    new_prev_week: 0,
    chief_areas_total: 0,
    chief_areas_assigned: 0,
    chief_controlled_plots: 0,
    city_controlled_plots: 0,
    chief_fees_collected: 0,
    land_tax_collected: 0,
    registrations_by_month: [] as { month: string; count: number }[]
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
        if (u.is_superuser && u.role !== 'official') {
          goto('/dashboard/admin');
          return;
        }
        dashboardUserName = u.full_name || u.username || 'Official';
        if (!u.is_staff) {
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

  function trendClass(current: number, previous: number): string {
    if (current > previous) return 'trend-up';
    if (current < previous) return 'trend-down';
    return 'trend-flat';
  }

  function trendLabel(current: number, previous: number): string {
    if (previous === 0) return current > 0 ? '↑ new activity' : '—';
    const pct = Math.round(((current - previous) / previous) * 100);
    return `${pct >= 0 ? '+' : ''}${pct}% vs last week`;
  }

  $: maxTrendCount = Math.max(0, ...dashboardStats.registrations_by_month.map((m) => m.count));
</script>

<div class="official-dashboard">
  <!-- Professional Navigation -->
  <Navbar userType="official" activeLink="/dashboard/official" userName={dashboardUserName} showNotification={false} />

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
      <!-- Primary Stats -->
      <div class="stats-grid primary">
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
          <!-- Registrations Trend Chart -->
          <div class="card trend-card">
            <div class="card-header">
              <h2>Registrations — Last 6 Months</h2>
            </div>
            <div class="card-body">
              {#if dashboardStats.registrations_by_month.length > 0}
                <div class="trend-chart" role="img" aria-label="Bar chart of plot registrations per month for the last six months">
                  {#each dashboardStats.registrations_by_month as m (m.month)}
                    <div class="trend-col">
                      <div class="trend-count">{m.count}</div>
                      <div
                        class="trend-bar"
                        style="height: {maxTrendCount > 0 ? Math.max(4, (m.count / maxTrendCount) * 140) : 4}px"
                        title="{m.count} registrations in {m.month}"
                      ></div>
                      <div class="trend-month">{m.month}</div>
                    </div>
                  {/each}
                </div>
              {:else}
                <div class="empty-state"><p>No registration data available</p></div>
              {/if}
            </div>
          </div>

          <!-- Registry Overview -->
          <div class="card">
            <div class="card-header">
              <h2>Registry Overview</h2>
            </div>
            <div class="card-body">
              <div class="overview-grid">
                <a class="stat-card kpi-link pending-row" href="/dashboard/official/caseload">
                  <div class="stat-icon warning">
                    <FolderOpen size={24} />
                  </div>
                  <div class="stat-content">
                    <div class="stat-value">{dashboardStats.pending_claims}</div>
                    <div class="stat-label">Pending Claims</div>
                  </div>
                  <ChevronRight size={18} class="kpi-chevron" />
                </a>

                <div class="stat-card">
                  <div class="stat-icon success">
                    <Percent size={22} />
                  </div>
                  <div class="stat-content">
                    <div class="stat-value small">{dashboardStats.approval_rate === null ? '—' : `${dashboardStats.approval_rate}%`}</div>
                    <div class="stat-label">Approval Rate</div>
                  </div>
                </div>

                <div class="stat-card">
                  <div class="stat-icon">
                    <MapPin size={22} />
                  </div>
                  <div class="stat-content">
                    <div class="stat-value small">{dashboardStats.boundary_mapped_pct}%</div>
                    <div class="stat-label">Boundary-Mapped</div>
                  </div>
                </div>

                <div class="stat-card">
                  <div class="stat-icon">
                    <Landmark size={22} />
                  </div>
                  <div class="stat-content">
                    <div class="stat-value small">{dashboardStats.protected_plots}</div>
                    <div class="stat-label">State-Held Plots</div>
                  </div>
                </div>

                <div class="stat-card">
                  <div class="stat-icon">
                    <Camera size={22} />
                  </div>
                  <div class="stat-content">
                    <div class="stat-value small">{dashboardStats.plots_with_media}</div>
                    <div class="stat-label">With Photo Evidence</div>
                  </div>
                </div>

                <div class="stat-card">
                  <div class="stat-icon">
                    <CalendarDays size={22} />
                  </div>
                  <div class="stat-content">
                    <div class="stat-value small">
                      {dashboardStats.new_this_week}
                      <span class="trend {trendClass(dashboardStats.new_this_week, dashboardStats.new_prev_week)}">
                        {trendLabel(dashboardStats.new_this_week, dashboardStats.new_prev_week)}
                      </span>
                    </div>
                    <div class="stat-label">New This Week</div>
                  </div>
                </div>

                <div class="stat-card">
                  <div class="stat-icon">
                    <Shield size={22} />
                  </div>
                  <div class="stat-content">
                    <div class="stat-value small">{dashboardStats.chief_areas_assigned}/{dashboardStats.chief_areas_total}</div>
                    <div class="stat-label">Chiefs Assigned</div>
                  </div>
                </div>

                <div class="stat-card">
                  <div class="stat-icon success">
                    <Landmark size={22} />
                  </div>
                  <div class="stat-content">
                    <div class="stat-value small">{dashboardStats.chief_controlled_plots ?? 0}</div>
                    <div class="stat-label">Chief-Controlled Plots</div>
                  </div>
                </div>

                <div class="stat-card">
                  <div class="stat-icon info">
                    <MapPin size={22} />
                  </div>
                  <div class="stat-content">
                    <div class="stat-value small">{dashboardStats.city_controlled_plots ?? 0}</div>
                    <div class="stat-label">City-Controlled Plots</div>
                  </div>
                </div>

                <div class="stat-card">
                  <div class="stat-icon warning">
                    <CalendarDays size={22} />
                  </div>
                  <div class="stat-content">
                    <div class="stat-value small">MWK {(dashboardStats.chief_fees_collected ?? 0).toLocaleString()}</div>
                    <div class="stat-label">Chief Fees Collected</div>
                  </div>
                </div>

                <div class="stat-card">
                  <div class="stat-icon info">
                    <Percent size={22} />
                  </div>
                  <div class="stat-content">
                    <div class="stat-value small">MWK {(dashboardStats.land_tax_collected ?? 0).toLocaleString()}</div>
                    <div class="stat-label">Land Tax Collected</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Status cards side by side -->
          <div class="status-row">
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
                  <ChevronRight size={18} class="action-chevron" />
                </a>

                <a href="/dashboard/register-citizen" class="action-item">
                  <div class="action-icon">
                    <UserPlus size={20} />
                  </div>
                  <div class="action-content">
                    <div class="action-title">Register Citizen</div>
                    <div class="action-desc">Onboard new users</div>
                  </div>
                  <ChevronRight size={18} class="action-chevron" />
                </a>

                <a href="/dashboard/official/register-chief" class="action-item">
                  <div class="action-icon">
                    <Shield size={20} />
                  </div>
                  <div class="action-content">
                    <div class="action-title">Register Chief</div>
                    <div class="action-desc">Register chiefs & assign jurisdictions</div>
                  </div>
                  <ChevronRight size={18} class="action-chevron" />
                </a>

                <a href="/dashboard/official/verified" class="action-item">
                  <div class="action-icon">
                    <CheckCircle size={20} />
                  </div>
                  <div class="action-content">
                    <div class="action-title">Verified Claims</div>
                    <div class="action-desc">View verified plots</div>
                  </div>
                  <ChevronRight size={18} class="action-chevron" />
                </a>

                <a href="/dashboard/official/reports" class="action-item">
                  <div class="action-icon">
                    <BarChart3 size={20} />
                  </div>
                  <div class="action-content">
                    <div class="action-title">Reports</div>
                    <div class="action-desc">Generate reports</div>
                  </div>
                  <ChevronRight size={18} class="action-chevron" />
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
    border-left: 4px solid #007A3D;
    padding-left: 1rem;
    margin-bottom: 2.5rem;
  }

  .dashboard-header h1 {
    font-size: 2rem;
    font-weight: 700;
    color: #1e293b;
    margin-bottom: 0.25rem;
  }

  .dashboard-header p {
    font-size: 1.05rem;
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

  .stats-grid.primary {
    grid-template-columns: repeat(4, 1fr);
  }

  .stats-grid.primary .stat-card {
    padding: 1.75rem;
  }

  .stats-grid.primary .stat-value {
    font-size: 2.5rem;
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
    background: rgba(0, 122, 61, 0.08);
  }

  .stat-icon.warning { color: #d97706; background: rgba(217, 119, 6, 0.1); }
  .stat-icon.success { color: #059669; background: rgba(5, 150, 105, 0.1); }
  .stat-icon.info { color: #2563eb; background: rgba(37, 99, 235, 0.1); }

  .kpi-link { text-decoration: none; color: inherit; }
  .stat-card .kpi-chevron, .stat-card .action-chevron { color: #94a3b8; flex-shrink: 0; }

  /* Registry Overview grid */
  .overview-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
  }

  .overview-grid .stat-card {
    padding: 1rem;
    gap: 0.75rem;
  }

  .stat-value.small {
    font-size: 1.4rem;
  }

  .pending-row {
    grid-column: 1 / -1;
    background: #fffbeb;
    border-color: #fcd34d;
  }

  .pending-row:hover {
    border-color: #f59e0b;
    box-shadow: 0 4px 12px rgba(245, 158, 11, 0.12);
  }

  .pending-row .stat-value { font-size: 1.8rem; }

  /* Status cards side by side */
  .status-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.5rem;
  }

  /* Registrations trend chart */
  .trend-card {
    margin-bottom: 2rem;
  }
  .trend-chart {
    display: flex;
    align-items: flex-end;
    justify-content: space-around;
    gap: 1rem;
    padding: 0.5rem 0;
    min-height: 190px;
  }
  .trend-col {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: flex-end;
    gap: 0.35rem;
    flex: 1;
  }
  .trend-bar {
    width: 100%;
    max-width: 56px;
    background: linear-gradient(180deg, #34d399, #007A3D);
    border-radius: 6px 6px 0 0;
    transition: height 0.3s ease;
  }
  .trend-count {
    font-size: 0.8rem;
    font-weight: 700;
    color: #0f172a;
  }
  .trend-month {
    font-size: 0.75rem;
    font-weight: 600;
    color: #64748b;
  }

  .trend {
    display: block;
    font-size: 0.7rem;
    font-weight: 600;
    margin-top: 0.15rem;
  }
  .trend-up { color: #059669; }
  .trend-down { color: #dc2626; }
  .trend-flat { color: #64748b; }

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
    position: relative;
  }

  .timeline::before {
    content: '';
    position: absolute;
    left: 5px;
    top: 8px;
    bottom: 8px;
    width: 2px;
    background: #e2e8f0;
  }

  .timeline-item {
    display: flex;
    gap: 1rem;
    position: relative;
    z-index: 1;
  }

  .timeline-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    margin-top: 4px;
    flex-shrink: 0;
    border: 2px solid white;
    box-shadow: 0 0 0 2px #e2e8f0;
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

    .status-row {
      grid-template-columns: 1fr;
    }

    .stats-grid.primary {
      grid-template-columns: repeat(2, 1fr);
    }

    .overview-grid {
      grid-template-columns: repeat(2, 1fr);
    }
  }

  @media (max-width: 768px) {
    .main-content {
      padding: 1rem;
    }

    .stats-grid.primary {
      grid-template-columns: repeat(2, 1fr);
      gap: 1rem;
    }

    .overview-grid {
      grid-template-columns: 1fr;
    }
  }

  @media (max-width: 480px) {
    .stats-grid.primary {
      grid-template-columns: 1fr;
    }
  }
</style>
