<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { Check, ClipboardCheck, Clock3, MapPin, UserRound, X } from 'lucide-svelte';
  import Navbar from '$lib/components/Navbar.svelte';

  const API = 'http://localhost:5000';
  type Registration = {
    id: number;
    district: string;
    traditional_authority: string;
    village: string;
    relationship_to_land?: string;
    additional_notes?: string;
    submitted_at: string;
    registrar_name?: string;
    citizen: {
      id: number;
      full_name: string;
      phone: string;
      email?: string;
    };
  };
  type AdminUser = { full_name?: string; is_superuser: boolean };

  let currentUser: AdminUser | null = null;
  let registrations: Registration[] = [];
  let rejectionReasons: Record<number, string> = {};
  let isLoading = true;
  let reviewingId: number | null = null;
  let error = '';
  let message = '';

  function authHeaders(): Record<string, string> {
    return { Authorization: `Bearer ${localStorage.getItem('token')}` };
  }

  async function loadRegistrations() {
    const response = await fetch(`${API}/api/admin/citizen-registrations`, {
      headers: authHeaders()
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Could not load citizen registrations.');
    registrations = data;
  }

  async function initialize() {
    isLoading = true;
    error = '';
    try {
      const response = await fetch(`${API}/api/user/me`, { headers: authHeaders() });
      if (!response.ok) {
        goto('/login');
        return;
      }
      const userData: AdminUser = await response.json();
      currentUser = userData;
      if (!userData.is_superuser) {
        goto('/dashboard');
        return;
      }
      await loadRegistrations();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not load citizen registrations.';
    } finally {
      isLoading = false;
    }
  }

  async function review(registration: Registration, decision: 'approved' | 'rejected') {
    const reason = rejectionReasons[registration.id]?.trim() || '';
    if (decision === 'rejected' && !reason) {
      error = 'Enter a reason before rejecting a registration.';
      return;
    }

    reviewingId = registration.id;
    error = '';
    message = '';
    try {
      const response = await fetch(
        `${API}/api/admin/citizen-registrations/${registration.id}/review`,
        {
          method: 'POST',
          headers: { ...authHeaders(), 'Content-Type': 'application/json' },
          body: JSON.stringify({ decision, reason })
        }
      );
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Could not review this registration.');
      message = `${registration.citizen.full_name}: registration ${decision}.`;
      await loadRegistrations();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not review this registration.';
    } finally {
      reviewingId = null;
    }
  }

  function formatDate(value: string) {
    return value ? new Date(value).toLocaleString() : 'Unknown';
  }

  onMount(initialize);
</script>

<svelte:head>
  <title>Citizen Registration Review - LandLock Admin</title>
</svelte:head>

<div class="page-wrapper">
  <Navbar
    userType="admin"
    activeLink="/dashboard/admin/citizen-registrations"
    userName={currentUser?.full_name || 'Administrator'}
  />
  <main class="main-content">
    <header class="page-heading">
      <div>
        <p class="eyebrow">ACCOUNT APPROVALS</p>
        <h1>Citizen registrations</h1>
        <p>Check officer-submitted details before activating a citizen account.</p>
      </div>
      <div class="queue-count">
        <ClipboardCheck size={18} />
        <strong>{registrations.length}</strong>
        <span>awaiting review</span>
      </div>
    </header>

    {#if error}<p class="notice error" role="alert">{error}</p>{/if}
    {#if message}<p class="notice success" role="status">{message}</p>{/if}

    {#if isLoading}
      <section class="empty-state loading-state"><span class="spinner"></span><p>Loading registration queue...</p></section>
    {:else if registrations.length === 0}
      <section class="empty-state">
        <span class="empty-icon"><Check size={25} /></span>
        <h2>All caught up</h2>
        <p>There are no citizen registrations waiting for review.</p>
      </section>
    {:else}
      <div class="registration-list">
        {#each registrations as registration (registration.id)}
          <article class="registration-card">
            <header class="registration-header">
              <div class="citizen-summary">
                <span class="avatar">{(registration.citizen.full_name || '?').trim().charAt(0).toUpperCase()}</span>
                <div>
                  <h2>{registration.citizen.full_name || 'Name not provided'}</h2>
                  <p>{registration.citizen.phone || 'No phone'}{registration.citizen.email ? ` · ${registration.citizen.email}` : ''}</p>
                </div>
              </div>
              <div class="review-meta">
                <span class="pending-pill"><Clock3 size={14} /> Pending review</span>
                <span>Submitted {formatDate(registration.submitted_at)}</span>
              </div>
            </header>

            <div class="location-heading"><MapPin size={16} /><span>Registered location</span></div>
            <dl class="details-grid">
              <div><dt>District</dt><dd>{registration.district || '—'}</dd></div>
              <div><dt>Traditional authority</dt><dd>{registration.traditional_authority || '—'}</dd></div>
              <div><dt>Village</dt><dd>{registration.village || '—'}</dd></div>
              <div><dt>Relationship to land</dt><dd>{registration.relationship_to_land || 'Not provided'}</dd></div>
            </dl>

            <section class="context-panel">
              <div class="registrar"><UserRound size={16} /><span>Registered by</span><strong>{registration.registrar_name || 'Unknown official'}</strong></div>
              <div class="additional-notes"><span>Officer notes</span><p>{registration.additional_notes || 'No additional notes provided.'}</p></div>
            </section>

            <label class="reason-field">
              <span>Decision note <small>Required if rejecting</small></span>
              <textarea bind:value={rejectionReasons[registration.id]} rows="2" placeholder="Add a reason for rejection, or a note for the record..." disabled={reviewingId === registration.id}></textarea>
            </label>
            <div class="review-actions">
              <button
                class="button approve"
                on:click={() => review(registration, 'approved')}
                disabled={reviewingId === registration.id}
              >
                <Check size={17} />
                {reviewingId === registration.id ? 'Saving...' : 'Approve account'}
              </button>
              <button
                class="button reject"
                on:click={() => review(registration, 'rejected')}
                disabled={reviewingId === registration.id}
              >
                <X size={17} />
                Reject
              </button>
            </div>
          </article>
        {/each}
      </div>
    {/if}
  </main>
</div>

<style>
  .page-wrapper { min-height: 100vh; background: #f4f7f5; }
  .main-content { width: min(100% - 48px, 1120px); margin: 0 auto; padding: 2rem 0 3rem; }
  .page-heading { display: flex; justify-content: space-between; align-items: center; gap: 1.5rem; margin-bottom: 1.4rem; }
  .eyebrow { margin: 0 0 .45rem; color: #638171; font-size: .7rem; font-weight: 750; letter-spacing: .13em; }
  .page-heading h1 { margin: 0; color: #193329; font-size: clamp(1.7rem, 3vw, 2.2rem); letter-spacing: -.035em; }
  .page-heading p:not(.eyebrow) { margin: .45rem 0 0; color: #738178; }
  .queue-count { display: flex; align-items: center; gap: .55rem; padding: .75rem .9rem; border: 1px solid #dfebe2; border-radius: 10px; color: #47745b; background: #edf5ef; white-space: nowrap; }
  .queue-count strong { color: #1c5635; font-size: 1.1rem; }
  .queue-count span { color: #668271; font-size: .85rem; }
  .registration-list { display: grid; gap: 1rem; }
  .registration-card { padding: clamp(1.1rem, 2vw, 1.5rem); border: 1px solid #e2e9e4; border-radius: 14px; background: #fff; box-shadow: 0 4px 16px rgb(25 51 41 / 4%); }
  .registration-header { display: flex; justify-content: space-between; align-items: center; gap: 1rem; padding-bottom: 1rem; border-bottom: 1px solid #edf1ee; }
  .citizen-summary { display: flex; align-items: center; gap: .8rem; min-width: 0; }
  .avatar { display: grid; place-items: center; width: 46px; height: 46px; flex: 0 0 auto; border-radius: 50%; color: #236742; background: #e8f3eb; font-size: 1.1rem; font-weight: 700; }
  .citizen-summary h2 { overflow: hidden; margin: 0; color: #193329; font-size: 1.05rem; text-overflow: ellipsis; }
  .citizen-summary p { margin: .25rem 0 0; color: #718078; font-size: .86rem; }
  .review-meta { display: grid; justify-items: end; gap: .35rem; flex: 0 0 auto; color: #78877e; font-size: .78rem; }
  .pending-pill { display: inline-flex; align-items: center; gap: .35rem; padding: .3rem .55rem; border-radius: 999px; color: #93691c; background: #fbf3df; font-size: .76rem; font-weight: 650; }
  .location-heading { display: flex; align-items: center; gap: .45rem; margin: 1.15rem 0 .65rem; color: #557462; font-size: .82rem; font-weight: 700; }
  .details-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: .7rem; margin: 0; }
  .details-grid div { min-width: 0; padding: .75rem .8rem; border: 1px solid #edf1ee; border-radius: 8px; background: #fafcfb; }
  dt { color: #839087; font-size: .72rem; }
  dd { overflow-wrap: anywhere; margin: .25rem 0 0; color: #293d32; font-size: .87rem; font-weight: 600; }
  .context-panel { display: grid; grid-template-columns: minmax(170px, .7fr) 1.3fr; gap: 1rem; margin-top: .8rem; padding: .85rem 1rem; border-radius: 9px; background: #f6f8f6; }
  .registrar { display: flex; align-items: center; gap: .45rem; color: #728078; font-size: .8rem; }
  .registrar strong { color: #40574a; font-weight: 600; }
  .additional-notes > span { color: #728078; font-size: .75rem; }
  .additional-notes p { margin: .2rem 0 0; color: #405147; font-size: .84rem; line-height: 1.45; }
  .reason-field { display: grid; gap: .45rem; margin-top: 1rem; color: #405147; font-size: .83rem; font-weight: 650; }
  .reason-field > span { display: flex; justify-content: space-between; }
  .reason-field small { color: #89948d; font-size: .76rem; font-weight: 400; }
  textarea { width: 100%; resize: vertical; min-height: 68px; padding: .65rem .75rem; border: 1px solid #dfe7e1; border-radius: 8px; background: #fcfdfc; color: #263d30; font: inherit; font-size: .85rem; }
  textarea:focus { outline: 2px solid #a7ccb2; outline-offset: 1px; border-color: #6ea780; }
  .review-actions { display: flex; justify-content: flex-end; gap: .6rem; margin-top: .9rem; }
  .button { display: inline-flex; align-items: center; justify-content: center; gap: .45rem; min-height: 40px; padding: .6rem .9rem; border: 1px solid transparent; border-radius: 8px; font: inherit; font-size: .85rem; font-weight: 650; cursor: pointer; transition: background .15s ease, transform .15s ease; }
  .button:hover:not(:disabled) { transform: translateY(-1px); }
  .button:disabled { opacity: .6; cursor: not-allowed; }
  .approve { color: white; background: #167447; }
  .approve:hover:not(:disabled) { background: #105d38; }
  .reject { border-color: #f0d7d4; color: #a34137; background: white; }
  .reject:hover:not(:disabled) { background: #fff5f4; }
  .notice { margin: 1rem 0; padding: .8rem 1rem; border-radius: 8px; font-size: .9rem; }
  .notice.error { color: #991b1b; background: #fee2e2; }
  .notice.success { color: #166534; background: #dcfce7; }
  .empty-state { display: grid; justify-items: center; gap: .55rem; margin-top: 1.2rem; padding: 3rem 1.5rem; border: 1px solid #e2e9e4; border-radius: 14px; color: #78877e; background: white; text-align: center; }
  .empty-state h2 { margin: .2rem 0 0; color: #193329; font-size: 1.15rem; }
  .empty-state p { margin: 0; font-size: .9rem; }
  .empty-icon { display: grid; place-items: center; width: 50px; height: 50px; border-radius: 50%; color: #167447; background: #e8f5ed; }
  .loading-state { display: flex; justify-content: center; }
  .spinner { width: 18px; height: 18px; border: 2px solid #d9e8dd; border-top-color: #167447; border-radius: 50%; animation: spin .8s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }
  @media (max-width: 650px) {
    .main-content { width: min(100% - 28px, 1120px); padding: 1rem 0 2rem; }
    .page-heading { align-items: flex-start; flex-direction: column; gap: .9rem; }
    .queue-count { align-self: stretch; justify-content: center; }
    .registration-header { align-items: flex-start; flex-direction: column; }
    .review-meta { justify-items: start; }
    .details-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .context-panel { grid-template-columns: 1fr; gap: .7rem; }
    .review-actions { flex-direction: column-reverse; }
    .button { width: 100%; }
  }
</style>
