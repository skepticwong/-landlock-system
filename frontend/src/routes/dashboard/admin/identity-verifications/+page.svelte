<script lang="ts">
  import { onDestroy, onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import Navbar from '$lib/components/Navbar.svelte';

  const API = 'http://localhost:5000';
  type Verification = {
    id: number;
    national_id: string;
    submitted_at: string;
    user: {
      id: number;
      full_name: string;
      username: string;
      phone: string;
      email: string;
      role: string;
    };
    frontUrl?: string;
    backUrl?: string;
  };
  type AdminUser = { full_name?: string; is_superuser: boolean };

  let currentUser: AdminUser | null = null;
  let submissions: Verification[] = [];
  let rejectionReasons: Record<number, string> = {};
  let isLoading = true;
  let reviewingId: number | null = null;
  let error = '';
  let message = '';
  const documentUrls: string[] = [];

  function authHeaders(): Record<string, string> {
    return { Authorization: `Bearer ${localStorage.getItem('token')}` };
  }

  function clearDocumentUrls() {
    documentUrls.forEach((url) => URL.revokeObjectURL(url));
    documentUrls.length = 0;
  }

  async function loadSubmissions() {
    clearDocumentUrls();
    const response = await fetch(`${API}/api/admin/identity-verifications`, {
      headers: authHeaders()
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Could not load ID submissions.');

    submissions = await Promise.all(data.map(async (submission: Verification) => {
      const [frontResponse, backResponse] = await Promise.all([
        fetch(`${API}/api/admin/identity-verifications/${submission.id}/documents/front`, {
          headers: authHeaders()
        }),
        fetch(`${API}/api/admin/identity-verifications/${submission.id}/documents/back`, {
          headers: authHeaders()
        })
      ]);
      if (!frontResponse.ok || !backResponse.ok) {
        throw new Error(`Could not load ID images for ${submission.user.full_name}.`);
      }
      const frontUrl = URL.createObjectURL(await frontResponse.blob());
      const backUrl = URL.createObjectURL(await backResponse.blob());
      documentUrls.push(frontUrl, backUrl);
      return { ...submission, frontUrl, backUrl };
    }));
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
      await loadSubmissions();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not load ID submissions.';
    } finally {
      isLoading = false;
    }
  }

  async function review(submission: Verification, decision: 'verified' | 'rejected') {
    const reason = rejectionReasons[submission.id]?.trim() || '';
    if (decision === 'rejected' && !reason) {
      error = 'Enter a reason before rejecting an ID submission.';
      return;
    }
    reviewingId = submission.id;
    error = '';
    message = '';
    try {
      const response = await fetch(`${API}/api/admin/identity-verifications/${submission.id}/review`, {
        method: 'POST',
        headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ decision, reason })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Could not review this ID.');
      message = `${submission.user.full_name}: ${decision === 'verified' ? 'verified' : 'rejected'}.`;
      await loadSubmissions();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not review this ID.';
    } finally {
      reviewingId = null;
    }
  }

  function formatDate(value: string) {
    return value ? new Date(value).toLocaleString() : 'Unknown';
  }

  onMount(initialize);
  onDestroy(clearDocumentUrls);
</script>

<svelte:head>
  <title>National ID Review - LandLock Admin</title>
</svelte:head>

<div class="page-wrapper">
  <Navbar userType="admin" activeLink="/dashboard/admin/identity-verifications" userName={currentUser?.full_name || 'Administrator'} />
  <main class="main-content">
    <header class="page-header">
      <div>
        <h1>National ID review</h1>
        <p>Review submitted National IDs. Approving verifies identity only; it does not confirm land ownership.</p>
      </div>
      <span class="queue-count">{submissions.length} awaiting review</span>
    </header>

    {#if error}<p class="notice error" role="alert">{error}</p>{/if}
    {#if message}<p class="notice success" role="status">{message}</p>{/if}

    {#if isLoading}
      <p class="empty-state">Loading ID submissions...</p>
    {:else if submissions.length === 0}
      <section class="empty-state">
        <h2>No pending ID submissions</h2>
        <p>New submissions will appear here for administrator review.</p>
      </section>
    {:else}
      <div class="submission-list">
        {#each submissions as submission (submission.id)}
          <article class="submission-card">
            <header class="submission-header">
              <div>
                <h2>{submission.user.full_name || 'Name not provided'}</h2>
                <p>{submission.user.role || 'citizen'} · {submission.user.phone || 'No phone'}</p>
              </div>
              <div class="submission-meta">
                <span>National ID: <strong>{submission.national_id}</strong></span>
                <small>Submitted {formatDate(submission.submitted_at)}</small>
              </div>
            </header>

            <div class="document-grid">
              <figure>
                <img src={submission.frontUrl} alt={`Front of ${submission.user.full_name}'s National ID`} />
                <figcaption>Front of ID</figcaption>
              </figure>
              <figure>
                <img src={submission.backUrl} alt={`Back of ${submission.user.full_name}'s National ID`} />
                <figcaption>Back of ID</figcaption>
              </figure>
            </div>

            <label class="reason-field">
              Review note <span>(required when rejecting)</span>
              <textarea bind:value={rejectionReasons[submission.id]} rows="2" disabled={reviewingId === submission.id}></textarea>
            </label>
            <div class="review-actions">
              <button class="button approve" on:click={() => review(submission, 'verified')} disabled={reviewingId === submission.id}>
                {reviewingId === submission.id ? 'Saving...' : 'Approve ID'}
              </button>
              <button class="button reject" on:click={() => review(submission, 'rejected')} disabled={reviewingId === submission.id}>
                Reject ID
              </button>
            </div>
          </article>
        {/each}
      </div>
    {/if}
  </main>
</div>

<style>
  .page-wrapper { min-height: 100vh; background: #f8fafc; }
  .main-content { max-width: 1200px; margin: auto; padding: 2rem; }
  .page-header, .submission-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; }
  .page-header h1 { margin: 0; color: #1e293b; }
  .page-header p, .submission-header p { margin: .4rem 0 0; color: #64748b; }
  .queue-count { padding: .4rem .7rem; border-radius: 999px; background: #eff6ff; color: #1d4ed8; white-space: nowrap; }
  .submission-list { display: grid; gap: 1rem; margin-top: 1.5rem; }
  .submission-card, .empty-state { padding: 1.5rem; border: 1px solid #e2e8f0; border-radius: 12px; background: white; }
  .submission-header h2, .empty-state h2 { margin: 0; color: #1e293b; }
  .submission-meta { display: grid; gap: .35rem; text-align: right; color: #334155; }
  .submission-meta small { color: #64748b; }
  .document-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem; margin: 1.25rem 0; }
  figure { margin: 0; padding: .5rem; border: 1px solid #e2e8f0; border-radius: 8px; }
  figure img { display: block; width: 100%; height: 260px; object-fit: contain; background: #f8fafc; }
  figcaption { padding: .5rem 0 .1rem; color: #475569; font-size: .9rem; }
  .reason-field { display: grid; gap: .4rem; color: #334155; font-weight: 600; }
  .reason-field span { color: #64748b; font-size: .85rem; font-weight: 400; }
  textarea { width: 100%; resize: vertical; padding: .65rem; border: 1px solid #cbd5e1; border-radius: 7px; font: inherit; }
  .review-actions { display: flex; justify-content: flex-end; gap: .75rem; margin-top: 1rem; }
  .button { padding: .65rem 1rem; border: 0; border-radius: 7px; color: white; font: inherit; font-weight: 600; cursor: pointer; }
  .button:disabled { opacity: .6; cursor: not-allowed; }
  .approve { background: #15803d; }
  .reject { background: #b91c1c; }
  .notice { margin: 1rem 0; padding: .75rem 1rem; border-radius: 7px; }
  .notice.error { background: #fee2e2; color: #991b1b; }
  .notice.success { background: #dcfce7; color: #166534; }
  .empty-state { margin-top: 1.5rem; text-align: center; color: #64748b; }
  .empty-state h2 { margin-bottom: .5rem; }
  @media (max-width: 650px) {
    .main-content { padding: 1rem; }
    .page-header, .submission-header { flex-direction: column; }
    .submission-meta { text-align: left; }
    .document-grid { grid-template-columns: 1fr; }
    figure img { height: 220px; }
    .review-actions { flex-direction: column; }
  }
</style>
