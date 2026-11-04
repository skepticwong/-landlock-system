<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { browser } from '$app/environment';
  import { Check, X, Shield, Smartphone, Users, Clock, AlertCircle, MapPin, DollarSign } from 'lucide-svelte';
  import Navbar from '$lib/components/Navbar.svelte';

  const API_BASE = 'http://localhost:5000';

  let pendingApprovals: any[] = [];
  let isLoading = true;
  let errorMsg = '';
  let actionMsg = '';
  let processingId = '';

  // For inline approval code entry (USSD/SMS flow) and rejection reasons
  let approvalCodes: Record<number, string> = {};
  let rejectReasons: Record<number, string> = {};
  let showRejectForm: Record<number, boolean> = {};

  onMount(() => {
    if (!browser) return;
    if (!localStorage.getItem('token')) { goto('/login'); return; }
    fetchPendingApprovals();
  });

  async function fetchPendingApprovals() {
    isLoading = true;
    errorMsg = '';
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_BASE}/api/transactions/pending-approvals`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        pendingApprovals = await res.json();
      } else {
        const data = await res.json();
        errorMsg = data.error || 'Failed to load pending approvals';
      }
    } catch (err: any) {
      errorMsg = err.message || 'Network error';
    } finally {
      isLoading = false;
    }
  }

  async function approve(txId: number) {
    processingId = `approve-${txId}`;
    actionMsg = '';
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_BASE}/api/transactions/${txId}/approve`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({})
      });
      const data = await res.json();
      if (res.ok) {
        actionMsg = data.message;
        pendingApprovals = pendingApprovals.filter(t => t.id !== txId);
      } else {
        actionMsg = data.error || 'Approval failed';
      }
    } catch (err: any) {
      actionMsg = err.message || 'Network error';
    } finally {
      processingId = '';
    }
  }

  async function reject(txId: number) {
    processingId = `reject-${txId}`;
    actionMsg = '';
    const reason = (rejectReasons[txId] || '').trim();
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_BASE}/api/transactions/${txId}/reject`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ reason: reason || 'Rejected via dashboard' })
      });
      const data = await res.json();
      if (res.ok) {
        actionMsg = data.message;
        pendingApprovals = pendingApprovals.filter(t => t.id !== txId);
      } else {
        actionMsg = data.error || 'Rejection failed';
      }
    } catch (err: any) {
      actionMsg = err.message || 'Network error';
    } finally {
      processingId = '';
      showRejectForm[txId] = false;
    }
  }

  async function buyerConfirm(txId: number) {
    processingId = `confirm-${txId}`;
    actionMsg = '';
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_BASE}/api/transactions/${txId}/buyer-confirm`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({})
      });
      const data = await res.json();
      if (res.ok) {
        actionMsg = data.message;
        pendingApprovals = pendingApprovals.filter(t => t.id !== txId);
      } else {
        actionMsg = data.error || 'Confirmation failed';
      }
    } catch (err: any) {
      actionMsg = err.message || 'Network error';
    } finally {
      processingId = '';
    }
  }

  function getRoleLabel(role: string): string {
    return { chief: 'Chief', witness: 'Witness', buyer: 'Buyer' }[role] || role;
  }

  function getRoleIcon(role: string) {
    return { chief: Shield, witness: Smartphone, buyer: Users }[role] || Shield;
  }

  function getRoleColor(role: string): string {
    return { chief: '#d97706', witness: '#007A3D', buyer: '#2563eb' }[role] || '#6b7280';
  }
</script>

<svelte:head>
  <title>Pending Approvals - LandLock</title>
</svelte:head>

<div class="approvals-page">
  <Navbar activeLink="/transactions/approvals" />

  <main class="main-content">
    <div class="page-header">
      <h1>Pending Approvals</h1>
      <p>Transactions awaiting your action as chief, witness, or buyer.</p>
    </div>

    {#if actionMsg}
      <div class="action-banner" class:error={actionMsg.includes('failed') || actionMsg.includes('error') || actionMsg.includes('Please')}>
        {actionMsg}
      </div>
    {/if}

    {#if isLoading}
      <div class="loading-state">
        <div class="spinner"></div>
        <p>Loading pending approvals...</p>
      </div>
    {:else if pendingApprovals.length === 0}
      <div class="empty-state">
        <Check class="empty-icon" />
        <h3>All Clear!</h3>
        <p>No transactions awaiting your approval.</p>
      </div>
    {:else}
      <div class="approvals-list">
        {#each pendingApprovals as tx (tx.id)}
          <div class="approval-card">
            <div class="card-header">
              <div class="role-badge" style="background: {getRoleColor(tx.my_role)}20; color: {getRoleColor(tx.my_role)}; border-color: {getRoleColor(tx.my_role)}40;">
                <svelte:component this={getRoleIcon(tx.my_role)} class="w-4 h-4" />
                {getRoleLabel(tx.my_role)}
              </div>
              <div class="tx-id">TX #{tx.id}</div>
            </div>

            <div class="card-body">
              <div class="plot-info">
                <h3><MapPin class="w-4 h-4 inline" /> {tx.plot_name || `Plot #${tx.plot_id}`}</h3>
                <div class="plot-meta">
                  {#if tx.plot_district}<span>{tx.plot_district}</span>{/if}
                  {#if tx.plot_village}<span>{tx.plot_village}</span>{/if}
                </div>
              </div>

              <div class="parties-grid">
                <div class="party">
                  <span class="party-label">Seller</span>
                  <span class="party-name">{tx.seller_name || 'Unknown'}</span>
                </div>
                <div class="party">
                  <span class="party-label">Buyer</span>
                  <span class="party-name">{tx.buyer_name || 'Unknown'}</span>
                </div>
                <div class="party">
                  <span class="party-label">Witness</span>
                  <span class="party-name">{tx.witness_name || 'Unknown'}</span>
                </div>
                <div class="party">
                  <span class="party-label">Chief</span>
                  <span class="party-name">{tx.chief_name || 'Unknown'}</span>
                </div>
              </div>

              {#if tx.amount}
                <div class="amount">
                  <DollarSign class="w-4 h-4 inline" /> MK {tx.amount.toLocaleString()}
                </div>
              {/if}

              <div class="approval-status-grid">
                <div class="status-item" class:approved={tx.buyer_approval_status === 'approved'}>
                  <span>Buyer</span>
                  <span class="status-pill">{tx.buyer_approval_status === 'approved' ? 'Confirmed' : 'Pending'}</span>
                </div>
                <div class="status-item" class:approved={tx.chief_approval_status === 'approved'}>
                  <span>Chief</span>
                  <span class="status-pill">{tx.chief_approval_status === 'approved' ? 'Approved' : 'Pending'}</span>
                </div>
                <div class="status-item" class:approved={tx.witness_approval_status === 'approved'}>
                  <span>Witness</span>
                  <span class="status-pill">{tx.witness_approval_status === 'approved' ? 'Approved' : 'Pending'}</span>
                </div>
              </div>

              <!-- Action section -->
              {#if tx.my_role === 'buyer'}
                <div class="action-section buyer-action">
                  <p class="action-hint">As the buyer, confirm that you agree to this purchase.</p>
                  <button
                    class="btn btn-confirm"
                    on:click={() => buyerConfirm(tx.id)}
                    disabled={processingId === `confirm-${tx.id}`}
                  >
                    {#if processingId === `confirm-${tx.id}`}
                      <span class="spinner-sm"></span>
                    {:else}
                      <Check class="w-4 h-4 inline" />
                    {/if}
                    Confirm Purchase
                  </button>
                </div>
              {:else}
                <div class="action-section">
                  <p class="action-hint">
                    You are logged in as the <strong>{tx.my_role === 'chief' ? 'chief' : 'witness'}</strong> for this transaction.
                    Your identity is verified — approve or reject directly.
                  </p>

                  {#if showRejectForm[tx.id]}
                    <div class="reject-form">
                      <label class="reject-label">Reason for rejection (optional):</label>
                      <textarea
                        class="reason-input"
                        placeholder="Enter reason..."
                        bind:value={rejectReasons[tx.id]}
                        rows="2"
                      ></textarea>
                      <div class="reject-form-buttons">
                        <button
                          class="btn btn-reject"
                          on:click={() => reject(tx.id)}
                          disabled={processingId === `reject-${tx.id}`}
                        >
                          {#if processingId === `reject-${tx.id}`}
                            <span class="spinner-sm"></span>
                          {:else}
                            <X class="w-4 h-4 inline" />
                          {/if}
                          Confirm Rejection
                        </button>
                        <button
                          class="btn btn-cancel"
                          on:click={() => showRejectForm[tx.id] = false}
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  {:else}
                    <div class="action-buttons">
                      <button
                        class="btn btn-approve"
                        on:click={() => approve(tx.id)}
                        disabled={processingId === `approve-${tx.id}`}
                      >
                        {#if processingId === `approve-${tx.id}`}
                          <span class="spinner-sm"></span>
                        {:else}
                          <Check class="w-4 h-4 inline" />
                        {/if}
                        Approve
                      </button>
                      <button
                        class="btn btn-reject"
                        on:click={() => showRejectForm[tx.id] = true}
                        disabled={processingId === `approve-${tx.id}`}
                      >
                        <X class="w-4 h-4 inline" />
                        Reject
                      </button>
                    </div>
                  {/if}
                </div>
              {/if}

              <div class="card-footer">
                <Clock class="w-3 h-3" />
                <span>Created: {new Date(tx.created_at).toLocaleDateString()}</span>
              </div>
            </div>
          </div>
        {/each}
      </div>
    {/if}
  </main>
</div>

<style>
  .approvals-page {
    min-height: 100vh;
    background: #f8f9fa;
  }

  .main-content {
    max-width: 800px;
    margin: 0 auto;
    padding: 2rem 1.5rem;
  }

  .page-header {
    margin-bottom: 2rem;
  }

  .page-header h1 {
    font-size: 1.5rem;
    font-weight: 700;
    color: #1a1a1a;
    margin-bottom: 0.25rem;
  }

  .page-header p {
    color: #6b7280;
    font-size: 0.9375rem;
  }

  .action-banner {
    padding: 0.75rem 1rem;
    background: #ecfdf5;
    border: 1px solid #a7f3d0;
    border-radius: 8px;
    color: #065f46;
    font-size: 0.875rem;
    margin-bottom: 1.5rem;
  }

  .action-banner.error {
    background: #fef2f2;
    border-color: #fecaca;
    color: #dc2626;
  }

  .loading-state {
    text-align: center;
    padding: 3rem;
    color: #6b7280;
  }

  .empty-state {
    text-align: center;
    padding: 3rem 2rem;
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
  }

  .empty-icon {
    width: 48px;
    height: 48px;
    color: #007A3D;
    margin-bottom: 1rem;
  }

  .empty-state h3 {
    font-size: 1.25rem;
    font-weight: 700;
    color: #1a1a1a;
    margin-bottom: 0.5rem;
  }

  .empty-state p { color: #6b7280; }

  .approvals-list {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .approval-card {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    overflow: hidden;
  }

  .card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem 1.5rem;
    background: #f8f9fa;
    border-bottom: 1px solid #e2e8f0;
  }

  .role-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.375rem;
    padding: 0.25rem 0.75rem;
    border-radius: 6px;
    font-size: 0.8125rem;
    font-weight: 600;
    border: 1px solid;
  }

  .tx-id {
    font-size: 0.8125rem;
    color: #6b7280;
    font-weight: 500;
  }

  .card-body {
    padding: 1.5rem;
  }

  .plot-info {
    margin-bottom: 1rem;
  }

  .plot-info h3 {
    font-size: 1rem;
    font-weight: 700;
    color: #1a1a1a;
    display: flex;
    align-items: center;
    gap: 0.375rem;
    margin-bottom: 0.25rem;
  }

  .plot-meta {
    display: flex;
    gap: 0.75rem;
    font-size: 0.8125rem;
    color: #6b7280;
  }

  .parties-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0.75rem;
    margin-bottom: 1rem;
  }

  .party {
    display: flex;
    flex-direction: column;
    gap: 0.125rem;
  }

  .party-label {
    font-size: 0.6875rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #9ca3af;
    font-weight: 600;
  }

  .party-name {
    font-size: 0.875rem;
    font-weight: 600;
    color: #374151;
  }

  .amount {
    font-size: 1.125rem;
    font-weight: 700;
    color: #007A3D;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 0.25rem;
  }

  .approval-status-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 0.5rem;
    margin-bottom: 1.25rem;
  }

  .status-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.25rem;
    padding: 0.5rem;
    background: #f9fafb;
    border-radius: 8px;
    border: 1px solid #e5e7eb;
  }

  .status-item span:first-child {
    font-size: 0.75rem;
    color: #6b7280;
    font-weight: 500;
  }

  .status-pill {
    font-size: 0.75rem;
    font-weight: 600;
    padding: 0.125rem 0.5rem;
    border-radius: 4px;
    background: #fef3c7;
    color: #92400e;
  }

  .status-item.approved .status-pill {
    background: #dcfce7;
    color: #166534;
  }

  .action-section {
    margin-top: 1rem;
    padding-top: 1rem;
    border-top: 1px solid #e5e7eb;
  }

  .action-hint {
    font-size: 0.8125rem;
    color: #6b7280;
    margin-bottom: 0.75rem;
  }

  .action-buttons {
    display: flex;
    gap: 0.75rem;
  }

  .buyer-action {
    text-align: center;
  }

  .btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.375rem;
    padding: 0.625rem 1.25rem;
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.875rem;
    border: none;
    cursor: pointer;
    transition: all 0.2s;
  }

  .btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .btn-approve {
    background: #007A3D;
    color: white;
    flex: 1;
  }

  .btn-approve:hover:not(:disabled) {
    background: #005c2e;
  }

  .btn-reject {
    background: #fef2f2;
    color: #dc2626;
    border: 1px solid #fecaca;
    flex: 1;
  }

  .btn-reject:hover:not(:disabled) {
    background: #fee2e2;
  }

  .btn-cancel {
    background: #f3f4f6;
    color: #374151;
    border: 1px solid #e5e7eb;
  }

  .btn-cancel:hover:not(:disabled) {
    background: #e5e7eb;
  }

  .reject-form {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .reject-label {
    font-size: 0.8125rem;
    font-weight: 600;
    color: #374151;
  }

  .reason-input {
    width: 100%;
    padding: 0.625rem 1rem;
    border: 2px solid #e5e7eb;
    border-radius: 8px;
    font-size: 0.875rem;
    font-family: inherit;
    resize: vertical;
  }

  .reason-input:focus {
    outline: none;
    border-color: #dc2626;
    box-shadow: 0 0 0 3px rgba(220,38,38,0.1);
  }

  .reject-form-buttons {
    display: flex;
    gap: 0.75rem;
  }

  .btn-confirm {
    background: #2563eb;
    color: white;
    padding: 0.75rem 2rem;
  }

  .btn-confirm:hover:not(:disabled) {
    background: #1d4ed8;
  }

  .card-footer {
    display: flex;
    align-items: center;
    gap: 0.375rem;
    margin-top: 1rem;
    padding-top: 0.75rem;
    border-top: 1px solid #f3f4f6;
    font-size: 0.75rem;
    color: #9ca3af;
  }

  .spinner {
    width: 32px;
    height: 32px;
    border: 3px solid #e5e7eb;
    border-top: 3px solid #007A3D;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto 1rem;
  }

  .spinner-sm {
    display: inline-block;
    width: 14px;
    height: 14px;
    border: 2px solid rgba(255,255,255,0.3);
    border-top: 2px solid white;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  @media (max-width: 640px) {
    .parties-grid { grid-template-columns: repeat(2, 1fr); }
    .approval-status-grid { grid-template-columns: 1fr; }
    .navbar-menu { display: none; }
  }
</style>
