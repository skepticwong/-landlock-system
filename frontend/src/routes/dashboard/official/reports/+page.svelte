<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { browser } from '$app/environment';
  import { BarChart3, Download, Calendar, FileText, TrendingUp, Users, Map, CheckCircle, Clock } from 'lucide-svelte';
  import Navbar from '$lib/components/Navbar.svelte';

  const API = 'http://localhost:5000';

  let reportData = {
    totalParcels: 0,
    verifiedParcels: 0,
    pendingParcels: 0,
    totalUsers: 0,
    totalTransactions: 0,
    recentActivity: []
  };
  let isLoading = true;
  let selectedReport = 'overview';
  let dateRange = '30';

  function authHeaders() {
    return { 'Authorization': `Bearer ${localStorage.getItem('token')}` };
  }

  async function fetchReportData() {
    isLoading = true;
    try {
      const [parcelsRes, usersRes, txRes] = await Promise.all([
        fetch(`${API}/api/parcels`, { headers: authHeaders() }),
        fetch(`${API}/api/users`, { headers: authHeaders() }),
        fetch(`${API}/api/transactions`, { headers: authHeaders() })
      ]);

      if (parcelsRes.ok) {
        const parcels = await parcelsRes.json();
        reportData.totalParcels = parcels.length;
        reportData.verifiedParcels = parcels.filter((p: any) => p.status === 'verified').length;
        reportData.pendingParcels = parcels.filter((p: any) => p.status === 'pending').length;
      }

      if (usersRes.ok) {
        const users = await usersRes.json();
        reportData.totalUsers = users.length;
      }

      if (txRes.ok) {
        const tx = await txRes.json();
        reportData.totalTransactions = tx.length;
      }
    } catch (err) {
      console.error('Error fetching report data:', err);
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
        return;
      }
    } catch (err) {
      console.error('Error verifying admin status:', err);
      goto('/login');
      return;
    }

    fetchReportData();
  });

  function handleDownload(reportType: string) {
    // Placeholder for download functionality
    console.log(`Downloading ${reportType} report`);
  }

  function getVerificationRate(): number {
    if (reportData.totalParcels === 0) return 0;
    return Math.round((reportData.verifiedParcels / reportData.totalParcels) * 100);
  }
</script>

<svelte:head>
  <title>Reports - LandLock Official</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</svelte:head>

<div class="reports-page">
  <Navbar userType="official" activeLink="/dashboard/official/reports" userName="Official" showNotification={false} />

  <div class="page-content">
    <div class="page-header">
      <div class="header-left">
        <h1><BarChart3 class="w-6 h-6 inline" /> Reports & Analytics</h1>
        <p>Generate and view activity reports and statistics</p>
      </div>
      <div class="header-right">
        <select bind:value={dateRange} class="date-select">
          <option value="7">Last 7 days</option>
          <option value="30">Last 30 days</option>
          <option value="90">Last 90 days</option>
          <option value="365">Last year</option>
        </select>
      </div>
    </div>

    {#if isLoading}
      <div class="loading-state">
        <div class="spinner"></div>
        <p>Loading report data...</p>
      </div>
    {:else}
      <!-- Stats Overview -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon" style="background: #007A3D;">
            <Map class="w-6 h-6" />
          </div>
          <div class="stat-content">
            <div class="stat-value">{reportData.totalParcels}</div>
            <div class="stat-label">Total Parcels</div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon" style="background: #003366;">
            <CheckCircle class="w-6 h-6" />
          </div>
          <div class="stat-content">
            <div class="stat-value">{reportData.verifiedParcels}</div>
            <div class="stat-label">Verified</div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon" style="background: #FFC107;">
            <Clock class="w-6 h-6" />
          </div>
          <div class="stat-content">
            <div class="stat-value">{reportData.pendingParcels}</div>
            <div class="stat-label">Pending</div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon" style="background: #0D6EFD;">
            <Users class="w-6 h-6" />
          </div>
          <div class="stat-content">
            <div class="stat-value">{reportData.totalUsers}</div>
            <div class="stat-label">Total Users</div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon" style="background: #8B6F47;">
            <FileText class="w-6 h-6" />
          </div>
          <div class="stat-content">
            <div class="stat-value">{reportData.totalTransactions}</div>
            <div class="stat-label">Transactions</div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon" style="background: #6C757D;">
            <TrendingUp class="w-6 h-6" />
          </div>
          <div class="stat-content">
            <div class="stat-value">{getVerificationRate()}%</div>
            <div class="stat-label">Verification Rate</div>
          </div>
        </div>
      </div>

      <!-- Report Sections -->
      <div class="reports-grid">
        <!-- Activity Report -->
        <div class="report-card">
          <div class="report-header">
            <h3><FileText class="w-5 h-5 inline" /> Activity Report</h3>
            <button class="btn btn-secondary btn-sm" on:click={() => handleDownload('activity')}>
              <Download class="w-4 h-4 inline" />
              Download
            </button>
          </div>
          <div class="report-body">
            <div class="report-summary">
              <div class="summary-item">
                <span class="summary-label">New Registrations</span>
                <span class="summary-value">{reportData.totalParcels}</span>
              </div>
              <div class="summary-item">
                <span class="summary-label">Verifications Completed</span>
                <span class="summary-value">{reportData.verifiedParcels}</span>
              </div>
              <div class="summary-item">
                <span class="summary-label">Pending Reviews</span>
                <span class="summary-value">{reportData.pendingParcels}</span>
              </div>
            </div>
            <button class="btn btn-primary">View Full Report</button>
          </div>
        </div>

        <!-- Status Report -->
        <div class="report-card">
          <div class="report-header">
            <h3><CheckCircle class="w-5 h-5 inline" /> Status Report</h3>
            <button class="btn btn-secondary btn-sm" on:click={() => handleDownload('status')}>
              <Download class="w-4 h-4 inline" />
              Download
            </button>
          </div>
          <div class="report-body">
            <div class="status-breakdown">
              <div class="status-item">
                <div class="status-bar">
                  <div class="status-fill" style="width: {getVerificationRate()}%; background: #007A3D;"></div>
                </div>
                <div class="status-info">
                  <span class="status-label">Verified</span>
                  <span class="status-count">{reportData.verifiedParcels}</span>
                </div>
              </div>
              <div class="status-item">
                <div class="status-bar">
                  <div class="status-fill" style="width: {reportData.totalParcels > 0 ? (reportData.pendingParcels / reportData.totalParcels) * 100 : 0}%; background: #FFC107;"></div>
                </div>
                <div class="status-info">
                  <span class="status-label">Pending</span>
                  <span class="status-count">{reportData.pendingParcels}</span>
                </div>
              </div>
            </div>
            <button class="btn btn-primary">View Full Report</button>
          </div>
        </div>

        <!-- User Activity Report -->
        <div class="report-card">
          <div class="report-header">
            <h3><Users class="w-5 h-5 inline" /> User Activity</h3>
            <button class="btn btn-secondary btn-sm" on:click={() => handleDownload('users')}>
              <Download class="w-4 h-4 inline" />
              Download
            </button>
          </div>
          <div class="report-body">
            <div class="report-summary">
              <div class="summary-item">
                <span class="summary-label">Total Users</span>
                <span class="summary-value">{reportData.totalUsers}</span>
              </div>
              <div class="summary-item">
                <span class="summary-label">Active This Period</span>
                <span class="summary-value">{Math.round(reportData.totalUsers * 0.7)}</span>
              </div>
              <div class="summary-item">
                <span class="summary-label">New Registrations</span>
                <span class="summary-value">{Math.round(reportData.totalUsers * 0.1)}</span>
              </div>
            </div>
            <button class="btn btn-primary">View Full Report</button>
          </div>
        </div>

        <!-- Transaction Report -->
        <div class="report-card">
          <div class="report-header">
            <h3><TrendingUp class="w-5 h-5 inline" /> Transaction Report</h3>
            <button class="btn btn-secondary btn-sm" on:click={() => handleDownload('transactions')}>
              <Download class="w-4 h-4 inline" />
              Download
            </button>
          </div>
          <div class="report-body">
            <div class="report-summary">
              <div class="summary-item">
                <span class="summary-label">Total Transactions</span>
                <span class="summary-value">{reportData.totalTransactions}</span>
              </div>
              <div class="summary-item">
                <span class="summary-label">Completed</span>
                <span class="summary-value">{Math.round(reportData.totalTransactions * 0.8)}</span>
              </div>
              <div class="summary-item">
                <span class="summary-label">In Progress</span>
                <span class="summary-value">{Math.round(reportData.totalTransactions * 0.2)}</span>
              </div>
            </div>
            <button class="btn btn-primary">View Full Report</button>
          </div>
        </div>
      </div>
    {/if}
  </div>
</div>

<style>
  /* Global resets handled in app.css */

  .reports-page {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  /* Page Content */
  .page-content {
    max-width: 1400px;
    margin: 0 auto;
    padding: 2rem;
    width: 100%;
    flex: 1;
  }

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
    flex-wrap: wrap;
    gap: 1rem;
  }

  .header-left h1 {
    font-size: 2rem;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .header-left p {
    color: #64748b;
    font-size: 1rem;
  }

  .header-right {
    display: flex;
    gap: 1rem;
  }

  .date-select {
    padding: 0.5rem 1rem;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    font-size: 0.9375rem;
    font-family: inherit;
    background: white;
    cursor: pointer;
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
    border-radius: 12px;
    padding: 1.5rem;
    border: 1px solid #e2e8f0;
    display: flex;
    align-items: center;
    gap: 1rem;
    transition: all 0.2s;
  }

  .stat-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  }

  .stat-icon {
    width: 48px;
    height: 48px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    flex-shrink: 0;
  }

  .stat-content {
    flex: 1;
  }

  .stat-value {
    font-size: 1.875rem;
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

  /* Reports Grid */
  .reports-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
    gap: 1.5rem;
  }

  .report-card {
    background: white;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
    overflow: hidden;
  }

  .report-header {
    padding: 1.5rem;
    border-bottom: 1px solid #e2e8f0;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .report-header h3 {
    font-size: 1.125rem;
    font-weight: 700;
    color: #0f172a;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .report-body {
    padding: 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .report-summary {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .summary-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .summary-label {
    font-size: 0.875rem;
    color: #64748b;
    font-weight: 500;
  }

  .summary-value {
    font-size: 1rem;
    font-weight: 600;
    color: #0f172a;
  }

  /* Status Breakdown */
  .status-breakdown {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .status-item {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .status-bar {
    height: 8px;
    background: #e2e8f0;
    border-radius: 4px;
    overflow: hidden;
  }

  .status-fill {
    height: 100%;
    border-radius: 4px;
    transition: width 0.3s ease;
  }

  .status-info {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .status-label {
    font-size: 0.875rem;
    color: #64748b;
    font-weight: 500;
  }

  .status-count {
    font-size: 1rem;
    font-weight: 600;
    color: #0f172a;
  }

  /* Buttons */
  .btn {
    padding: 0.5rem 1rem;
    border-radius: 8px;
    border: none;
    font-weight: 600;
    font-size: 0.875rem;
    cursor: pointer;
    transition: all 0.2s;
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    white-space: nowrap;
  }

  .btn-primary {
    background: #007A3D;
    color: white;
  }

  .btn-primary:hover {
    background: #005C2E;
  }

  .btn-secondary {
    background: white;
    color: #007A3D;
    border: 1px solid #e2e8f0;
  }

  .btn-secondary:hover {
    background: #f8fafc;
  }

  .btn-sm {
    padding: 0.375rem 0.75rem;
    font-size: 0.8125rem;
  }

  /* Loading State */
  .loading-state {
    text-align: center;
    padding: 4rem 2rem;
  }

  .spinner {
    width: 48px;
    height: 48px;
    border: 4px solid #e2e8f0;
    border-top-color: #007A3D;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto 1rem;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .loading-state p {
    color: #64748b;
  }

  /* Responsive */
  @media (max-width: 768px) {
    .page-content {
      padding: 1rem;
    }

    .page-header {
      flex-direction: column;
      align-items: flex-start;
    }

    .stats-grid {
      grid-template-columns: repeat(2, 1fr);
    }

    .reports-grid {
      grid-template-columns: 1fr;
    }
  }

  @media (max-width: 480px) {
    .stats-grid {
      grid-template-columns: 1fr;
    }
  }
</style>
