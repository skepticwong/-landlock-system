<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import {
    Activity,
    ArrowUpRight,
    BadgeCheck,
    ClipboardCheck,
    MapPinned,
    ShieldCheck,
    Users
  } from 'lucide-svelte';
  import Navbar from '$lib/components/Navbar.svelte';

  const API = 'http://localhost:5000';
  type AdminUser = { full_name?: string; is_superuser: boolean };
  type DashboardStats = {
    total_users: number;
    active_users: number;
    total_admins: number;
    total_plots: number;
    total_transactions: number;
    pending_transactions: number;
  };

  let currentUser: AdminUser | null = null;
  let stats: DashboardStats = {
    total_users: 0,
    active_users: 0,
    total_admins: 0,
    total_plots: 0,
    total_transactions: 0,
    pending_transactions: 0
  };
  let isLoading = true;
  let error = '';

  function authHeaders(): Record<string, string> {
    return { Authorization: `Bearer ${localStorage.getItem('token')}` };
  }

  async function initialize() {
    isLoading = true;
    error = '';
    try {
      const userResponse = await fetch(`${API}/api/user/me`, { headers: authHeaders() });
      if (!userResponse.ok) {
        goto('/login');
        return;
      }
      const userData: AdminUser = await userResponse.json();
      currentUser = userData;
      if (!userData.is_superuser) {
        goto('/dashboard');
        return;
      }

      const response = await fetch(`${API}/api/admin/dashboard`, { headers: authHeaders() });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || data.message || 'Could not load admin dashboard.');
      stats = data;
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not load admin dashboard.';
    } finally {
      isLoading = false;
    }
  }

  onMount(initialize);
</script>

<svelte:head>
  <title>Admin Dashboard - LandLock</title>
</svelte:head>

<div class="page-wrapper">
  <Navbar userType="admin" activeLink="/dashboard/admin" userName={currentUser?.full_name || 'Administrator'} />
  <main class="main-content">
    <header class="welcome-banner">
      <div>
        <p class="eyebrow">LANDLOCK · ADMINISTRATION</p>
        <h1>Admin dashboard</h1>
        <p>Manage people, permissions, and verification from one place.</p>
      </div>
      <a class="banner-action" href="/dashboard/admin/users">
        <Users size={18} />
        Manage users
        <ArrowUpRight size={17} />
      </a>
    </header>

    {#if error}<p class="notice error" role="alert">{error}</p>{/if}
    {#if isLoading}
      <section class="stats-grid" aria-label="Loading system totals">
        {#each [1, 2, 3, 4] as item}
          <div class="stat-card skeleton" aria-hidden="true"></div>
        {/each}
      </section>
    {:else}
      <section class="stats-grid" aria-label="System overview">
        <article class="stat-card">
          <span class="stat-icon green"><Users size={19} /></span>
          <div><span class="stat-label">Registered users</span><strong>{stats.total_users}</strong></div>
          <small>{stats.active_users} active</small>
        </article>
        <article class="stat-card">
          <span class="stat-icon blue"><ShieldCheck size={19} /></span>
          <div><span class="stat-label">Administrators</span><strong>{stats.total_admins}</strong></div>
          <small>Privileged accounts</small>
        </article>
        <article class="stat-card">
          <span class="stat-icon earth"><MapPinned size={19} /></span>
          <div><span class="stat-label">Land plots</span><strong>{stats.total_plots}</strong></div>
          <small>In the registry</small>
        </article>
        <article class="stat-card">
          <span class="stat-icon amber"><Activity size={19} /></span>
          <div><span class="stat-label">Transactions</span><strong>{stats.total_transactions}</strong></div>
          <small>{stats.pending_transactions} pending</small>
        </article>
      </section>

      <section class="section-block">
        <div class="section-heading">
          <div><p class="section-kicker">CONTROL CENTRE</p><h2>Administration</h2></div>
          <span>Choose an area to manage</span>
        </div>
        <div class="tool-grid">
          <a class="tool-card" href="/dashboard/admin/users">
            <span class="tool-icon green"><Users size={21} /></span>
            <span class="tool-copy"><strong>User management</strong><small>Create accounts, change roles, reset PINs, and control access.</small></span>
            <span class="tool-arrow"><ArrowUpRight size={18} /></span>
          </a>
          <a class="tool-card" href="/dashboard/admin/citizen-registrations">
            <span class="tool-icon amber"><ClipboardCheck size={21} /></span>
            <span class="tool-copy"><strong>Citizen registrations</strong><small>Review officer-submitted details before account activation.</small></span>
            <span class="tool-arrow"><ArrowUpRight size={18} /></span>
          </a>
          <a class="tool-card" href="/dashboard/admin/identity-verifications">
            <span class="tool-icon blue"><BadgeCheck size={21} /></span>
            <span class="tool-copy"><strong>National ID verification</strong><small>Review identity information and submitted documents.</small></span>
            <span class="tool-arrow"><ArrowUpRight size={18} /></span>
          </a>
          <a class="tool-card" href="/dashboard/admin/chief-areas">
            <span class="tool-icon earth"><MapPinned size={21} /></span>
            <span class="tool-copy"><strong>Chief jurisdictions</strong><small>Assign chiefs to districts, traditional authorities, and villages.</small></span>
            <span class="tool-arrow"><ArrowUpRight size={18} /></span>
          </a>
        </div>
      </section>

      <section class="security-note">
        <span><ShieldCheck size={20} /></span>
        <div><strong>Administrative access</strong><p>Role changes and account deactivation take effect immediately. Accounts are deactivated—not deleted—to preserve registry history.</p></div>
      </section>
    {/if}
  </main>
</div>

<style>
  .page-wrapper { min-height: 100vh; background: #f4f7f5; }
  .main-content { width: min(100% - 48px, 1240px); margin: 0 auto; padding: 2rem 0 3rem; }
  .welcome-banner { display: flex; align-items: center; justify-content: space-between; gap: 1.5rem; padding: clamp(1.5rem, 3vw, 2.5rem); border-radius: 18px; color: white; background: linear-gradient(115deg, #073d2a 0%, #0b6540 62%, #138052 100%); box-shadow: 0 16px 34px rgb(4 60 39 / 16%); }
  .welcome-banner .eyebrow { margin: 0 0 .7rem; color: #b7e5cd; font-size: .72rem; font-weight: 750; letter-spacing: .13em; }
  .welcome-banner h1 { margin: 0; font-size: clamp(1.8rem, 3vw, 2.5rem); font-weight: 700; letter-spacing: -.035em; }
  .welcome-banner p:not(.eyebrow) { margin: .55rem 0 0; color: #d3e9dc; }
  .banner-action { display: inline-flex; align-items: center; gap: .65rem; flex-shrink: 0; padding: .8rem 1rem; border: 1px solid rgb(255 255 255 / 28%); border-radius: 9px; color: white; background: rgb(255 255 255 / 9%); font-size: .92rem; font-weight: 650; text-decoration: none; transition: background .18s ease, transform .18s ease; }
  .banner-action:hover { transform: translateY(-1px); background: rgb(255 255 255 / 17%); }
  .stats-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 1rem; margin: 1.35rem 0 2.4rem; }
  .stat-card { display: grid; grid-template-columns: auto 1fr; align-items: center; gap: .2rem .85rem; min-height: 115px; padding: 1.1rem 1.2rem; border: 1px solid #e4eae6; border-radius: 12px; background: white; box-shadow: 0 3px 12px rgb(15 35 25 / 3%); }
  .stat-icon, .tool-icon { display: grid; place-items: center; flex: 0 0 auto; border-radius: 10px; }
  .stat-icon { width: 42px; height: 42px; grid-row: span 2; }
  .green { color: #167447; background: #e8f5ed; }
  .blue { color: #306a9c; background: #eaf2fa; }
  .earth { color: #8b6742; background: #f5eee5; }
  .amber { color: #9a6a13; background: #fbf3df; }
  .stat-card > div { display: grid; gap: .18rem; }
  .stat-label { color: #697970; font-size: .82rem; }
  .stat-card strong { color: #193329; font-size: 1.55rem; line-height: 1.1; }
  .stat-card > small { grid-column: 2; color: #839087; font-size: .76rem; }
  .skeleton { min-height: 115px; background: linear-gradient(90deg, #fff 20%, #edf1ee 50%, #fff 80%); background-size: 200% 100%; animation: shimmer 1.3s infinite; }
  @keyframes shimmer { to { background-position: -200% 0; } }
  .section-block { margin-top: 2rem; }
  .section-heading { display: flex; align-items: end; justify-content: space-between; gap: 1rem; margin-bottom: 1rem; }
  .section-kicker { margin: 0 0 .35rem; color: #6b8376; font-size: .7rem; font-weight: 750; letter-spacing: .12em; }
  .section-heading h2 { margin: 0; color: #1a3428; font-size: 1.35rem; letter-spacing: -.02em; }
  .section-heading > span { color: #78867d; font-size: .86rem; }
  .tool-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .85rem; }
  .tool-card { display: grid; grid-template-columns: auto 1fr auto; align-items: center; gap: 1rem; min-height: 112px; padding: 1.15rem; border: 1px solid #e2e9e4; border-radius: 12px; color: inherit; background: white; text-decoration: none; transition: border-color .18s ease, box-shadow .18s ease, transform .18s ease; }
  .tool-card:hover { transform: translateY(-2px); border-color: #a7c7b3; box-shadow: 0 10px 24px rgb(22 66 44 / 8%); }
  .tool-icon { width: 46px; height: 46px; }
  .tool-copy { display: grid; gap: .32rem; }
  .tool-copy strong { color: #1c392b; font-size: .97rem; }
  .tool-copy small { max-width: 440px; color: #748178; font-size: .83rem; line-height: 1.45; }
  .tool-arrow { color: #8b9b90; transition: transform .18s ease; }
  .tool-card:hover .tool-arrow { transform: translate(2px, -2px); color: #167447; }
  .security-note { display: flex; align-items: flex-start; gap: .85rem; margin-top: 1.4rem; padding: 1rem 1.1rem; border: 1px solid #dce8df; border-radius: 11px; background: #edf5ef; }
  .security-note > span { color: #347b54; }
  .security-note strong { color: #2b4938; font-size: .9rem; }
  .security-note p { margin: .25rem 0 0; color: #63796a; font-size: .82rem; line-height: 1.45; }
  .notice { padding: .8rem 1rem; border-radius: 8px; }
  .notice.error { color: #991b1b; background: #fee2e2; }
  @media (max-width: 900px) { .stats-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
  @media (max-width: 650px) {
    .main-content { width: min(100% - 28px, 1240px); padding: 1rem 0 2rem; }
    .welcome-banner { align-items: flex-start; flex-direction: column; border-radius: 14px; }
    .banner-action { align-self: stretch; justify-content: center; }
    .stats-grid { gap: .65rem; margin: .8rem 0 1.8rem; }
    .stat-card { min-height: 100px; gap: .2rem .6rem; padding: .85rem; }
    .stat-icon { width: 36px; height: 36px; }
    .stat-label { font-size: .75rem; }
    .stat-card strong { font-size: 1.3rem; }
    .stat-card > small { font-size: .7rem; }
    .tool-grid { grid-template-columns: 1fr; }
    .section-heading { align-items: flex-start; flex-direction: column; gap: .35rem; }
  }
</style>
