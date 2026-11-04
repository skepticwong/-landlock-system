<script lang="ts">
  import Navbar from '$lib/components/Navbar.svelte';
  import { BarChart3, Clock, CheckCircle, Home } from 'lucide-svelte';
  import { onMount } from 'svelte';
  import { browser } from '$app/environment';

  const API = 'http://localhost:5000';
  let stats = { pending_claims: 0, verified_this_month: 0, total_households: 0, registration_rate: 0 };
  let error = '';

  async function loadReports() {
    try {
      const response = await fetch(`${API}/api/chief/dashboard-stats`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      if (!response.ok) throw new Error('Could not load reports');
      stats = await response.json();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not load reports';
    }
  }

  onMount(() => { if (browser) loadReports(); });
</script>

<Navbar userType="chief" activeLink="/dashboard/chief/reports" showNotification={false} />

<main class="page-content">
  <header><h1><BarChart3 /> Reports</h1><p>Village land registration summary</p></header>
  {#if error}<p class="error">{error}</p>{/if}
  <div class="stats">
    <article><Clock /><strong>{stats.pending_claims}</strong><span>Pending claims</span></article>
    <article><CheckCircle /><strong>{stats.verified_this_month}</strong><span>Verified this month</span></article>
    <article><Home /><strong>{stats.total_households}</strong><span>Total households</span></article>
    <article><BarChart3 /><strong>{stats.registration_rate}%</strong><span>Registration rate</span></article>
  </div>
</main>

<style>
  :global(body) { background: #f8fafc; }
  .page-content { margin-left: 260px; padding: 2rem; }
  header { margin-bottom: 2rem; }
  h1 { display:flex; align-items:center; gap:.5rem; }
  .stats { display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:1rem; }
  article { background:white; border:1px solid #e2e8f0; border-radius:12px; padding:1.5rem; display:grid; gap:.5rem; }
  strong { font-size:2rem; }
  span { color:#64748b; }
  .error { color:#dc2626; }
  @media (max-width: 768px) { .page-content { margin-left:0; padding-top:5rem; } }
</style>
