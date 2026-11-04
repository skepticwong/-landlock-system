<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { browser } from '$app/environment';
  import { Smartphone, Home, Calendar, FileText, Check, X, Eye, AlertTriangle, Clipboard } from 'lucide-svelte';
  import Navbar from '$lib/components/Navbar.svelte';
  const API = 'http://localhost:5000';

  interface Claim {
    id: string;
    parcelId: string;
    claimant: string;
    village: string;
    status: 'pending' | 'verified' | 'disputed';
    submittedDate: string;
    priority: 'high' | 'medium' | 'low';
    description: string;
  }

  let isOnline = true;
  let claims: Claim[] = [];
  let loadingClaims = true;
  let loadError = '';

  async function loadJurisdictionClaims() {
    try {
      const response = await fetch(`${API}/api/chief/pending-claims`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Could not load claims');
      claims = data.map((plot: any) => ({
        id: String(plot.id),
        parcelId: `MLW-${String(plot.id).padStart(4, '0')}`,
        claimant: plot.owner_name || plot.plot_name || 'Unknown claimant',
        village: plot.village || plot.traditional_authority || plot.district || 'Unknown',
        status: 'pending',
        submittedDate: plot.created_at || new Date().toISOString(),
        priority: plot.priority || 'medium',
        description: plot.description || plot.landmark_description || 'No description provided'
      }));
    } catch (err) {
      loadError = err instanceof Error ? err.message : 'Could not load claims';
    } finally {
      loadingClaims = false;
    }
  }

  let selectedClaim: Claim | null = null;
  let showVerifyModal = false;
  let showRejectModal = false;
  let rejectionReason = '';

  function handleOnline() {
    isOnline = true;
  }

  function handleOffline() {
    isOnline = false;
  }

  function getPriorityColor(priority: string) {
    switch (priority) {
      case 'high': return '#ef4444';
      case 'medium': return '#f59e0b';
      case 'low': return '#10b981';
      default: return '#6b7280';
    }
  }

  function formatDate(dateString: string) {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  }

  function openVerifyModal(claim: Claim) {
    selectedClaim = claim;
    showVerifyModal = true;
  }

  function openRejectModal(claim: Claim) {
    selectedClaim = claim;
    showRejectModal = true;
    rejectionReason = '';
  }

  function verifyClaim() {
    if (!selectedClaim) return;
    
    // Update claim status to verified
    const claimIndex = claims.findIndex(c => c.id === selectedClaim.id);
    if (claimIndex !== -1) {
      claims[claimIndex].status = 'verified';
    }
    
    showVerifyModal = false;
    selectedClaim = null;
    
    // TODO: Send verification to backend
    console.log('Claim verified');
  }

  function rejectClaim() {
    if (!selectedClaim || !rejectionReason.trim()) return;
    
    // Update claim status to disputed
    const claimIndex = claims.findIndex(c => c.id === selectedClaim.id);
    if (claimIndex !== -1) {
      claims[claimIndex].status = 'disputed';
    }
    
    showRejectModal = false;
    selectedClaim = null;
    rejectionReason = '';
    
    // TODO: Send rejection to backend
    console.log('Claim rejected:', rejectionReason);
  }

  function closeModal() {
    showVerifyModal = false;
    showRejectModal = false;
    selectedClaim = null;
    rejectionReason = '';
  }

  onMount(() => {
    if (!browser) return;
    isOnline = navigator.onLine;
    loadJurisdictionClaims();

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  });

  function viewClaimDetails(claim: Claim) {
    const numericId = String(claim.id).match(/\d+/)?.[0];
    if (numericId) goto(`/dashboard/chief/pending/${numericId}`);
  }
</script>

<div class="pending-container">
  <Navbar userType="chief" activeLink="/dashboard/chief/pending" showNotification={false} />
  <div class="page-header">
    <div class="header-content">
      <div class="back-link" on:click={() => goto('/dashboard/chief')}>
        ← Back to Chief Dashboard
      </div>
      <h1>Pending Claims</h1>
      <p>Review and verify land claims submitted by villagers</p>
    </div>
    
    {#if !isOnline}
      <div class="offline-indicator">
        <Smartphone class="w-5 h-5 inline" /> Offline Mode - Actions will sync when connected
      </div>
    {/if}
  </div>

  {#if loadingClaims}
    <div class="empty-state"><p>Loading claims in your jurisdiction...</p></div>
  {:else if loadError}
    <div class="empty-state"><p>{loadError}</p></div>
  {:else}
  <div class="claims-grid">
    {#each claims as claim (claim.id)}
      <div class="claim-card" class:offline={!isOnline}>
        <div class="claim-header">
          <div class="parcel-id">{claim.parcelId}</div>
          <div class="priority-badge" style="background-color: {getPriorityColor(claim.priority)}">
            {claim.priority.toUpperCase()} PRIORITY
          </div>
        </div>
        
        <div class="claim-content">
          <h3 class="claimant-name">{claim.claimant}</h3>
          <div class="claim-details">
            <div class="detail-item">
              <span class="detail-label"><Home class="w-4 h-4 inline" /> Village:</span>
              <span class="detail-value">{claim.village}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label"><Calendar class="w-4 h-4 inline" /> Submitted:</span>
              <span class="detail-value">{formatDate(claim.submittedDate)}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label"><FileText class="w-4 h-4 inline" /> Description:</span>
              <span class="detail-value">{claim.description}</span>
            </div>
          </div>
          
          <div class="claim-actions">
            <button 
              class="action-btn verify-btn"
              on:click={() => openVerifyModal(claim)}
              disabled={!isOnline}
            >
              <Check class="w-4 h-4 inline" /> Verify Claim
            </button>
            <button 
              class="action-btn reject-btn"
              on:click={() => openRejectModal(claim)}
              disabled={!isOnline}
            >
              <X class="w-4 h-4 inline" /> Reject
            </button>
            <button 
              class="action-btn details-btn"
              on:click={() => viewClaimDetails(claim)}
            >
              <Eye class="w-4 h-4 inline" /> View Details
            </button>
          </div>
        </div>
      </div>
    {/each}
  </div>

  {#if claims.length === 0}
    <div class="empty-state">
      <div class="empty-icon"><Clipboard class="w-12 h-12" /></div>
      <h3>No Pending Claims</h3>
      <p>All claims have been reviewed. Check back later for new submissions.</p>
    </div>
  {/if}
  {/if}
</div>

<!-- Verify Modal -->
{#if showVerifyModal && selectedClaim}
  <div class="modal-overlay" on:click={closeModal}>
    <div class="modal" on:click|stopPropagation>
      <div class="modal-header">
        <h2>Verify Land Claim</h2>
        <button class="close-btn" on:click={closeModal}>×</button>
      </div>
      
      <div class="modal-content">
        <div class="claim-summary">
          <h3>Claim Details</h3>
          <div class="summary-item">
            <strong>Parcel ID:</strong> {selectedClaim.parcelId}
          </div>
          <div class="summary-item">
            <strong>Claimant:</strong> {selectedClaim.claimant}
          </div>
          <div class="summary-item">
            <strong>Village:</strong> {selectedClaim.village}
          </div>
          <div class="summary-item">
            <strong>Description:</strong> {selectedClaim.description}
          </div>
        </div>
        
        <div class="verification-warning">
          <AlertTriangle class="w-5 h-5 inline" /> By verifying this claim, you confirm that:
          <ul>
            <li>You have personally verified the claimant's identity</li>
            <li>The land description is accurate</li>
            <li>There are no known disputes with this claim</li>
            <li>The claimant has legitimate rights to this land</li>
          </ul>
        </div>
      </div>
      
      <div class="modal-actions">
        <button class="btn-cancel" on:click={closeModal}>
          Cancel
        </button>
        <button class="btn-verify" on:click={verifyClaim}>
          <Check class="w-4 h-4 inline" /> Verify Claim
        </button>
      </div>
    </div>
  </div>
{/if}

<!-- Reject Modal -->
{#if showRejectModal && selectedClaim}
  <div class="modal-overlay" on:click={closeModal}>
    <div class="modal" on:click|stopPropagation>
      <div class="modal-header">
        <h2>Reject Land Claim</h2>
        <button class="close-btn" on:click={closeModal}>×</button>
      </div>
      
      <div class="modal-content">
        <div class="claim-summary">
          <h3>Claim to Reject</h3>
          <div class="summary-item">
            <strong>Parcel ID:</strong> {selectedClaim.parcelId}
          </div>
          <div class="summary-item">
            <strong>Claimant:</strong> {selectedClaim.claimant}
          </div>
          <div class="summary-item">
            <strong>Village:</strong> {selectedClaim.village}
          </div>
        </div>
        
        <div class="rejection-form">
          <label for="rejection-reason">Reason for Rejection</label>
          <textarea
            id="rejection-reason"
            bind:value={rejectionReason}
            placeholder="Please explain why this claim is being rejected..."
            rows="4"
            required
          ></textarea>
        </div>
      </div>
      
      <div class="modal-actions">
        <button class="btn-cancel" on:click={closeModal}>
          Cancel
        </button>
        <button 
          class="btn-reject" 
          on:click={rejectClaim}
          disabled={!rejectionReason.trim()}
        >
          <X class="w-4 h-4 inline" /> Reject Claim
        </button>
      </div>
    </div>
  </div>
{/if}

<style>
  .pending-container {
    padding: 2rem;
    max-width: 1200px;
    margin: 0 auto;
  }

  .page-header {
    margin-bottom: 2rem;
  }

  .header-content {
    margin-bottom: 1rem;
  }

  .back-link {
    color: var(--color-primary);
    cursor: pointer;
    font-weight: 600;
    margin-bottom: 1rem;
    transition: color 0.2s;
  }

  .back-link:hover {
    color: var(--color-primary-hover);
  }

  .page-header h1 {
    font-size: 2.5rem;
    font-weight: 700;
    color: #1e293b;
    margin-bottom: 0.5rem;
  }

  .page-header p {
    font-size: 1.125rem;
    color: #64748b;
  }

  .offline-indicator {
    background: #fef3c7;
    color: #92400e;
    padding: 0.75rem 1rem;
    border-radius: 8px;
    border: 1px solid #fcd34d;
    font-weight: 500;
    display: inline-block;
  }

  .claims-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(450px, 1fr));
    gap: 1.5rem;
  }

  .claim-card {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    border: 2px solid #e2e8f0;
    transition: all 0.3s ease;
  }

  .claim-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 15px rgba(0, 0, 0, 0.15);
    border-color: var(--color-primary);
  }

  .claim-card.offline {
    opacity: 0.7;
    border-color: #f59e0b;
  }

  .claim-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }

  .parcel-id {
    font-family: monospace;
    font-weight: 600;
    color: #1e293b;
    font-size: 1.125rem;
  }

  .priority-badge {
    color: white;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
  }

  .claimant-name {
    font-size: 1.25rem;
    font-weight: 600;
    color: #1e293b;
    margin-bottom: 1rem;
  }

  .claim-details {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    margin-bottom: 1.5rem;
  }

  .detail-item {
    display: flex;
    align-items: flex-start;
    gap: 0.5rem;
  }

  .detail-label {
    color: #64748b;
    font-size: 0.875rem;
    min-width: 100px;
  }

  .detail-value {
    color: #1e293b;
    font-weight: 500;
    flex: 1;
  }

  .claim-actions {
    display: flex;
    gap: 0.75rem;
    flex-wrap: wrap;
  }

  .action-btn {
    padding: 0.75rem 1rem;
    border: none;
    border-radius: 8px;
    font-size: 0.875rem;
    cursor: pointer;
    transition: all 0.2s;
    font-weight: 600;
    flex: 1;
    min-width: 120px;
  }

  .action-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .verify-btn {
    background: #10b981;
    color: white;
  }

  .verify-btn:hover:not(:disabled) {
    background: #059669;
  }

  .reject-btn {
    background: #ef4444;
    color: white;
  }

  .reject-btn:hover:not(:disabled) {
    background: #dc2626;
  }

  .details-btn {
    background: #f1f5f9;
    color: #475569;
  }

  .details-btn:hover:not(:disabled) {
    background: #e2e8f0;
  }

  .empty-state {
    text-align: center;
    padding: 4rem 2rem;
    color: #64748b;
  }

  .empty-icon {
    font-size: 4rem;
    margin-bottom: 1rem;
  }

  .empty-state h3 {
    font-size: 1.5rem;
    margin-bottom: 0.5rem;
  }

  /* Modal Styles */
  .modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }

  .modal {
    background: white;
    border-radius: 16px;
    padding: 0;
    max-width: 600px;
    width: 90%;
    max-height: 90vh;
    overflow-y: auto;
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.5rem;
    border-bottom: 1px solid #e2e8f0;
  }

  .modal-header h2 {
    font-size: 1.5rem;
    font-weight: 700;
    color: #1e293b;
    margin: 0;
  }

  .close-btn {
    background: none;
    border: none;
    font-size: 1.5rem;
    cursor: pointer;
    color: #64748b;
    padding: 0.5rem;
  }

  .close-btn:hover {
    color: #1e293b;
  }

  .modal-content {
    padding: 1.5rem;
  }

  .claim-summary {
    margin-bottom: 1.5rem;
  }

  .claim-summary h3 {
    font-size: 1.125rem;
    font-weight: 600;
    color: #1e293b;
    margin-bottom: 1rem;
  }

  .summary-item {
    padding: 0.5rem 0;
    border-bottom: 1px solid #f1f5f9;
  }

  .summary-item:last-child {
    border-bottom: none;
  }

  .verification-warning {
    background: #fef3c7;
    border: 1px solid #fcd34d;
    border-radius: 8px;
    padding: 1rem;
  }

  .verification-warning p {
    margin: 0 0 0.5rem 0;
    font-weight: 600;
    color: #92400e;
  }

  .verification-warning ul {
    margin: 0;
    padding-left: 1.25rem;
    color: #92400e;
  }

  .verification-warning li {
    margin-bottom: 0.25rem;
  }

  .rejection-form {
    margin-bottom: 1.5rem;
  }

  .rejection-form label {
    display: block;
    font-weight: 600;
    color: #1e293b;
    margin-bottom: 0.5rem;
  }

  .rejection-form textarea {
    width: 100%;
    padding: 0.75rem;
    border: 2px solid #e2e8f0;
    border-radius: 8px;
    font-size: 1rem;
    resize: vertical;
    transition: border-color 0.2s;
  }

  .rejection-form textarea:focus {
    outline: none;
    border-color: #ef4444;
    box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.15);
  }

  .modal-actions {
    display: flex;
    gap: 1rem;
    padding: 1.5rem;
    border-top: 1px solid #e2e8f0;
  }

  .btn-cancel, .btn-verify, .btn-reject {
    padding: 0.75rem 1.5rem;
    border: none;
    border-radius: 8px;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    flex: 1;
  }

  .btn-cancel {
    background: #f1f5f9;
    color: #475569;
  }

  .btn-cancel:hover {
    background: #e2e8f0;
  }

  .btn-verify {
    background: #10b981;
    color: white;
  }

  .btn-verify:hover {
    background: #059669;
  }

  .btn-reject {
    background: #ef4444;
    color: white;
  }

  .btn-reject:hover {
    background: #dc2626;
  }

  .btn-reject:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  @media (max-width: 768px) {
    .pending-container {
      padding: 1rem;
    }

    .claims-grid {
      grid-template-columns: 1fr;
      gap: 1rem;
    }

    .claim-card {
      padding: 1rem;
    }

    .claim-actions {
      flex-direction: column;
    }

    .action-btn {
      min-width: auto;
    }

    .modal {
      width: 95%;
      margin: 1rem;
    }

    .modal-actions {
      flex-direction: column;
    }
  }
</style>
