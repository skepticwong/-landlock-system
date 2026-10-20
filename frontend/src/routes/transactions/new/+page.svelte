<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { browser } from '$app/environment';
  import { Check, MapPin, Ruler, DollarSign, Lock, Smartphone, Users, AlertCircle, Shield, Wallet } from 'lucide-svelte';
  import Navbar from '$lib/components/Navbar.svelte';
  import PaymentModal from '$lib/components/PaymentModal.svelte';

  const API_BASE = 'http://localhost:5000';

  // Step management
  let currentStep = 1;
  const totalSteps = 4;

  // User's verified parcels (real data from backend)
  let verifiedParcels: any[] = [];

  // Form data
  let formData = {
    selectedParcel: '',
    price: '',
    buyerPhone: '',
    witnessPhone: '',
    notes: ''
  };

  // UI state
  let isSubmitting = false;
  let errorMsg = '';
  let successMsg = '';
  let submittedTx: any = null;
  
  // Payment state
  let showPaymentModal = false;
  let paymentType = 'land_transfer';
  let transferFee = 10000;
  let paymentDescription = 'Land Purchase Payment';
  let pendingTxData: any = null;
  
  // Calculate total payment (sale price + transfer fee)
  $: salePrice = parseFloat(formData.price) || 0;
  $: totalPayment = salePrice + transferFee;

  async function fetchVerifiedParcels() {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/api/parcels`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        verifiedParcels = data.filter((p: any) => p.status === 'verified' || p.status === 'approved');
      }
    } catch (error) {
      console.error('Failed to fetch verified parcels:', error);
    }
  }

  onMount(() => {
    if (!browser) return;
    if (!localStorage.getItem('token')) { goto('/login'); return; }
    fetchVerifiedParcels();
  });

  function nextStep() { if (currentStep < totalSteps) currentStep++; }
  function prevStep() { if (currentStep > 1) currentStep--; }

  function selectParcel(parcelId: string) { formData.selectedParcel = parcelId; }

  function getSelectedParcel() {
    return verifiedParcels.find(p => p.id === formData.selectedParcel);
  }

  function isStepValid(step: number): boolean {
    switch (step) {
      case 1: return formData.selectedParcel !== '';
      case 2: return formData.price !== '' && formData.buyerPhone !== '' && formData.witnessPhone !== '';
      case 3: return true;
      case 4: return true;
      default: return false;
    }
  }

  function getStepTitle(step: number): string {
    return { 
      1: 'Select Parcel', 
      2: 'Sale Details', 
      3: 'Review & Submit',
      4: 'Payment'
    }[step] || '';
  }

  function getStepSubtitle(step: number): string {
    return {
      1: 'Choose which verified parcel you want to sell.',
      2: 'Enter the buyer and witness phone numbers. The chief is auto-assigned.',
      3: 'Review the sale details and submit for multi-party approval.',
      4: 'Complete the land transfer fee payment.'
    }[step] || '';
  }

  async function submitSale() {
    isSubmitting = true;
    errorMsg = '';
    successMsg = '';

    try {
      const token = localStorage.getItem('token');
      // Extract numeric plot ID from parcel ID (e.g. "MLW-3" -> 3)
      const plotId = parseInt(formData.selectedParcel.replace('MLW-', ''));

      // Store transaction data for after payment
      pendingTxData = {
        plot_id: plotId,
        buyer_phone: formData.buyerPhone,
        witness_phone: formData.witnessPhone,
        amount: parseFloat(formData.price) || 0,
        notes: formData.notes
      };
      
      // Move to payment step
      currentStep = 4;
    } catch (err: any) {
      errorMsg = err.message || 'Network error';
    } finally {
      isSubmitting = false;
    }
  }

  async function handlePaymentCompleted(event: any) {
    const payment = event.detail.payment;
    
    // Now submit the transaction with payment info
    isSubmitting = true;
    errorMsg = '';
    successMsg = '';

    try {
      const token = localStorage.getItem('token');

      const response = await fetch(`${API_BASE}/api/transactions/sale`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          ...pendingTxData,
          payment_id: payment.id
        })
      });

      const data = await response.json();

      if (!response.ok) {
        errorMsg = data.error || 'Failed to initiate sale';
        return;
      }

      submittedTx = data.transaction;
      successMsg = data.message;
      pendingTxData = null;
    } catch (err: any) {
      errorMsg = err.message || 'Network error';
    } finally {
      isSubmitting = false;
    }
  }

  function backToDashboard() { goto('/dashboard'); }
</script>

<PaymentModal
  bind:isOpen={showPaymentModal}
  paymentType={paymentType}
  amount={totalPayment}
  description={paymentDescription}
  transactionId={pendingTxData?.plot_id}
  on:paymentCompleted={handlePaymentCompleted}
/>

<svelte:head>
  <title>Initiate Land Sale - LandLock</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</svelte:head>

<div class="sell-lease-land">
  <!-- Navigation -->
  <Navbar activeLink="/transactions/new" />

  <!-- Main Content -->
  <main class="main-content">
    <!-- Progress Bar -->
    <div class="progress-container">
      <div class="progress-bar">
        {#each Array(totalSteps) as _, i}
          <div 
            class="progress-step" 
            class:active={currentStep === i + 1}
            class:completed={currentStep > i + 1}
          >
            <div class="step-number">{i + 1}</div>
            <div class="step-label">Step {i + 1}</div>
          </div>
        {/each}
      </div>
    </div>

    <!-- Step Content -->
    <div class="step-container">
      <div class="step-header">
        <h1>{getStepTitle(currentStep)}</h1>
        <p class="step-subtitle">{getStepSubtitle(currentStep)}</p>
      </div>

      <!-- Step 1: Select Parcel -->
      {#if currentStep === 1}
        <div class="step-content">
          <div class="parcels-grid">
            {#each verifiedParcels as parcel (parcel.id)}
              <div
                class="parcel-card"
                class:selected={formData.selectedParcel === parcel.id}
                on:click={() => selectParcel(parcel.id)}
              >
                <div class="parcel-header">
                  <div class="parcel-id">{parcel.id}</div>
                  <div class="parcel-badge"><Check class="w-4 h-4 inline" /> Verified</div>
                </div>
                <div class="parcel-details">
                  <div class="parcel-location"><MapPin class="w-4 h-4 inline" /> {parcel.location}</div>
                  <div class="parcel-size"><Ruler class="w-4 h-4 inline" /> {parcel.size || '20m x 20m'}</div>
                </div>
                <div class="parcel-status">
                  <div class="status-tag verified">Verified by Government</div>
                </div>
              </div>
            {/each}
          </div>

          {#if verifiedParcels.length === 0}
            <div class="empty-state">
              <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
                <circle cx="32" cy="32" r="32" fill="rgba(0, 122, 61, 0.1)"/>
                <path d="M32 20L42 30H36V40H28V30H22L32 20Z" fill="var(--color-primary)" opacity="0.5"/>
              </svg>
              <h3>No Verified Parcels</h3>
              <p>You need approved or verified parcels to initiate a sale.</p>
              <button class="btn btn-primary" on:click={() => goto('/register-land')}>
                Register Land First
              </button>
            </div>
          {/if}

          <div class="step-actions">
            <button class="btn btn-secondary" on:click={backToDashboard}>Cancel</button>
            <button class="btn btn-primary" on:click={nextStep} disabled={!isStepValid(1)}>
              Continue
              <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd"/>
              </svg>
            </button>
          </div>
        </div>
      {/if}

      <!-- Step 2: Sale Details (buyer + witness) -->
      {#if currentStep === 2}
        <div class="step-content">
          <div class="selected-parcel-info">
            <div class="parcel-summary">
              <div class="parcel-id">{getSelectedParcel()?.id}</div>
              <div class="parcel-details">
                <span><MapPin class="w-4 h-4 inline" /> {getSelectedParcel()?.location}</span>
                <span><Ruler class="w-4 h-4 inline" /> {getSelectedParcel()?.size || '20m x 20m'}</span>
              </div>
            </div>
          </div>

          <div class="sale-form-section">
            <div class="form-group">
              <label class="form-label"><DollarSign class="w-4 h-4 inline" /> Sale Price (MK)</label>
              <input
                type="number"
                class="form-input"
                bind:value={formData.price}
                placeholder="e.g., 500000"
                min="0"
              />
              <div class="field-hint">The agreed sale price in Malawian Kwacha</div>
            </div>

            <div class="form-group">
              <label class="form-label"><Users class="w-4 h-4 inline" /> Buyer Phone Number</label>
              <input
                type="tel"
                class="form-input"
                bind:value={formData.buyerPhone}
                placeholder="0888123456"
              />
              <div class="field-hint">Must be a registered LandLock user. They will receive an SMS to confirm.</div>
            </div>

            <div class="form-group">
              <label class="form-label"><Shield class="w-4 h-4 inline" /> Witness Phone Number</label>
              <input
                type="tel"
                class="form-input"
                bind:value={formData.witnessPhone}
                placeholder="0999888777"
              />
              <div class="field-hint">Any registered user can witness. Cannot be the seller or buyer. Their national ID ensures accountability.</div>
            </div>

            <div class="form-group">
              <label class="form-label">Notes (optional)</label>
              <textarea
                class="form-textarea"
                bind:value={formData.notes}
                placeholder="Any additional details about this sale..."
                rows="3"
              ></textarea>
            </div>

            <div class="info-card">
              <h4><Lock class="w-4 h-4 inline" /> Chief Auto-Assignment</h4>
              <p>The system will automatically assign the chief responsible for this plot's area based on its district, traditional authority, and village. The chief cannot be chosen by the seller.</p>
            </div>
          </div>

          <div class="step-actions">
            <button class="btn btn-secondary" on:click={prevStep}>
              <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clip-rule="evenodd"/>
              </svg>
              Back
            </button>
            <button class="btn btn-primary" on:click={nextStep} disabled={!isStepValid(2)}>
              Review Sale
              <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd"/>
              </svg>
            </button>
          </div>
        </div>
      {/if}

      <!-- Step 3: Review & Submit -->
      {#if currentStep === 3 && !successMsg}
        <div class="step-content">
          <div class="review-section">
            <div class="review-card">
              <h3>Sale Summary</h3>
              <div class="review-row">
                <span class="review-label">Parcel</span>
                <span class="review-value">{getSelectedParcel()?.id} — {getSelectedParcel()?.location}</span>
              </div>
              <div class="review-row">
                <span class="review-label">Sale Price</span>
                <span class="review-value">MK {formData.price}</span>
              </div>
              <div class="review-row">
                <span class="review-label">Buyer Phone</span>
                <span class="review-value">{formData.buyerPhone}</span>
              </div>
              <div class="review-row">
                <span class="review-label">Witness Phone</span>
                <span class="review-value">{formData.witnessPhone}</span>
              </div>
              {#if formData.notes}
                <div class="review-row">
                  <span class="review-label">Notes</span>
                  <span class="review-value">{formData.notes}</span>
                </div>
              {/if}
            </div>

            <div class="approval-flow-card">
              <h3><Shield class="w-5 h-5 inline" /> Multi-Party Approval Flow</h3>
              <p class="flow-description">After submission, the following approvals are required:</p>
              <div class="approval-steps">
                <div class="approval-step">
                  <div class="step-icon buyer"><Users class="w-5 h-5" /></div>
                  <div class="step-info">
                    <strong>1. Buyer Confirms</strong>
                    <span>Buyer receives SMS and confirms the purchase</span>
                  </div>
                </div>
                <div class="approval-step">
                  <div class="step-icon chief"><Shield class="w-5 h-5" /></div>
                  <div class="step-info">
                    <strong>2. Chief Approves</strong>
                    <span>Auto-assigned chief receives approval code via SMS</span>
                  </div>
                </div>
                <div class="approval-step">
                  <div class="step-icon witness"><Smartphone class="w-5 h-5" /></div>
                  <div class="step-info">
                    <strong>3. Witness Approves</strong>
                    <span>Witness receives approval code via SMS</span>
                  </div>
                </div>
              </div>
              <div class="flow-note">
                <AlertCircle class="w-4 h-4 inline" /> All approvals are logged in an immutable audit trail. Any party can reject the sale.
              </div>
            </div>

            {#if errorMsg}
              <div class="error-message">
                <AlertCircle class="w-4 h-4 inline" /> {errorMsg}
              </div>
            {/if}
          </div>

          <div class="step-actions">
            <button class="btn btn-secondary" on:click={prevStep}>Back</button>
            <button class="btn btn-primary btn-lg" on:click={submitSale} disabled={isSubmitting}>
              {#if isSubmitting}
                <span class="spinner"></span> Submitting...
              {:else}
                <Check class="w-4 h-4 inline" /> Continue to Payment
              {/if}
            </button>
          </div>
        </div>
      {/if}

      <!-- Step 4: Payment -->
      {#if currentStep === 4}
        <div class="step-content">
          <div class="payment-summary-card">
            <div class="payment-header">
              <h3><DollarSign class="w-5 h-5 inline" /> Payment Summary</h3>
              <div class="fee-amount">MK {totalPayment.toLocaleString()}</div>
            </div>
            <div class="payment-details">
              <div class="detail-row">
                <span>Plot Sale Price</span>
                <strong>MK {salePrice.toLocaleString()}</strong>
              </div>
              <div class="detail-row">
                <span>Land Transfer Fee</span>
                <strong>MK {transferFee.toLocaleString()}</strong>
              </div>
              <div class="detail-row total">
                <span>Total Payment</span>
                <strong>MK {totalPayment.toLocaleString()}</strong>
              </div>
              <div class="detail-row">
                <span>Plot</span>
                <strong>{getSelectedParcel()?.id}</strong>
              </div>
              <div class="detail-row">
                <span>Location</span>
                <strong>{getSelectedParcel()?.location}</strong>
              </div>
            </div>
          </div>

          <div class="payment-methods-section">
            <h4>Select Payment Method</h4>
            <div class="payment-methods-grid">
              <button class="payment-method-card" on:click={() => showPaymentModal = true}>
                <Smartphone class="w-8 h-8" />
                <span>Airtel Money</span>
              </button>
              <button class="payment-method-card" on:click={() => showPaymentModal = true}>
                <Smartphone class="w-8 h-8" />
                <span>TNM Mpamba</span>
              </button>
              <button class="payment-method-card" on:click={() => showPaymentModal = true}>
                <DollarSign class="w-8 h-8" />
                <span>Bank Card</span>
              </button>
              <button class="payment-method-card" on:click={() => showPaymentModal = true}>
                <Wallet class="w-8 h-8" />
                <span>Cash</span>
              </button>
            </div>
          </div>

          <div class="step-actions">
            <button class="btn btn-secondary" on:click={prevStep}>Back</button>
          </div>
        </div>
      {/if}

      <!-- Success Screen -->
      {#if successMsg}
        <div class="confirmation-screen">
          <div class="confirmation-card">
            <div class="success-icon">
              <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
                <circle cx="32" cy="32" r="32" fill="#dcfce7"/>
                <path d="M20 32L28 40L44 24" stroke="#16a34a" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <h2>Sale Initiated Successfully!</h2>
            <p class="success-detail">{successMsg}</p>

            {#if submittedTx}
              <div class="tx-summary">
                <div class="summary-row">
                  <span>Plot</span>
                  <strong>{submittedTx.plot_name}</strong>
                </div>
                <div class="summary-row">
                  <span>Buyer</span>
                  <strong>{submittedTx.buyer_name}</strong>
                </div>
                <div class="summary-row">
                  <span>Witness</span>
                  <strong>{submittedTx.witness_name}</strong>
                </div>
                <div class="summary-row">
                  <span>Chief</span>
                  <strong>{submittedTx.chief_name}</strong>
                  <small>({submittedTx.chief_area})</small>
                </div>
              </div>

              <div class="sms-notice">
                <Smartphone class="w-5 h-5" />
                <div>
                  <strong>SMS notifications sent</strong>
                  <p>The buyer, witness, and chief have each received an approval code via SMS.</p>
                </div>
              </div>
            {/if}

            <div class="next-steps">
              <h4>What happens next?</h4>
              <ul>
                <li><Users class="w-4 h-4 inline" /> Buyer confirms the purchase via SMS or web</li>
                <li><Shield class="w-4 h-4 inline" /> Chief approves using their unique code</li>
                <li><Smartphone class="w-4 h-4 inline" /> Witness approves using their unique code</li>
                <li><Check class="w-4 h-4 inline" /> Once all approve, ownership transfers automatically</li>
                <li><Lock class="w-4 h-4 inline" /> Every step is recorded in an immutable audit trail</li>
              </ul>
            </div>

            <div class="step-actions">
              <button class="btn btn-secondary" on:click={() => goto('/dashboard')}>
                Back to Dashboard
              </button>
              <button class="btn btn-primary" on:click={() => goto('/transactions')}>
                View Transactions
              </button>
            </div>
          </div>
        </div>
      {/if}
    </div>
  </main>
</div>

<style>
  :global(*) {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }

  :global(body) {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', sans-serif;
    background: var(--bg-primary);
    color: var(--text-primary);
    line-height: 1.5;
  }

  .sell-lease-land {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  /* Navbar */
  .navbar {
    background: white;
    border-bottom: 1px solid var(--color-border);
    position: sticky;
    top: 0;
    z-index: 100;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
  }

  .navbar-content {
    max-width: 1400px;
    margin: 0 auto;
    padding: 0 2rem;
    height: 64px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 2rem;
  }

  .navbar-brand {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .brand-name {
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--text-primary);
    letter-spacing: -0.5px;
  }

  .navbar-menu {
    display: flex;
    gap: 0.5rem;
    flex: 1;
  }

  .nav-link {
    padding: 0.5rem 1rem;
    border-radius: 8px;
    text-decoration: none;
    color: var(--color-disabled);
    font-weight: 500;
    font-size: 0.9375rem;
    transition: all 0.2s;
    white-space: nowrap;
  }

  .nav-link:hover {
    background: #f1f5f9;
    color: var(--text-primary);
  }

  .nav-link.active {
    background: var(--color-primary);
    color: white;
  }

  .navbar-actions {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .icon-btn {
    width: 40px;
    height: 40px;
    border-radius: 8px;
    border: none;
    background: var(--bg-primary);
    color: var(--color-disabled);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
  }

  .icon-btn:hover {
    background: #f1f5f9;
    color: var(--text-primary);
  }

  .avatar {
    width: 40px;
    height: 40px;
    border-radius: 10px;
    background: var(--color-primary);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
    font-size: 0.875rem;
    cursor: pointer;
  }

  /* Main Content */
  .main-content {
    max-width: 900px;
    margin: 0 auto;
    padding: 2rem;
    width: 100%;
    flex: 1;
  }

  /* Progress Bar */
  .progress-container {
    margin-bottom: 3rem;
  }

  .progress-bar {
    display: flex;
    justify-content: space-between;
    position: relative;
    max-width: 600px;
    margin: 0 auto;
  }

  .progress-bar::before {
    content: '';
    position: absolute;
    top: 20px;
    left: 0;
    right: 0;
    height: 2px;
    background: var(--color-border);
    z-index: 0;
  }

  .progress-step {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
    position: relative;
    z-index: 1;
  }

  .step-number {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: var(--color-border);
    color: var(--color-disabled);
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
    font-size: 0.875rem;
    transition: all 0.3s;
  }

  .progress-step.active .step-number {
    background: var(--color-primary);
    color: white;
    box-shadow: 0 4px 12px rgba(0, 122, 61, 0.3);
  }

  .progress-step.completed .step-number {
    background: #dcfce7;
    color: var(--color-primary);
    border: 1px solid rgba(0, 122, 61, 0.2);
  }

  .step-label {
    font-size: 0.75rem;
    color: var(--color-disabled);
    font-weight: 500;
  }

  .progress-step.active .step-label {
    color: var(--text-primary);
  }

  /* Step Container */
  .step-container {
    background: white;
    border-radius: 16px;
    border: 1px solid var(--color-border);
    padding: 2.5rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
  }

  .step-header {
    text-align: center;
    margin-bottom: 2rem;
  }

  .step-header h1 {
    font-size: 2rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 0.5rem;
  }

  .step-subtitle {
    color: var(--color-disabled);
    font-size: 1rem;
  }

  .step-content {
    min-height: 400px;
  }

  /* Parcels Grid */
  .parcels-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1.5rem;
    margin-bottom: 3rem;
  }

  .parcel-card {
    background: var(--bg-primary);
    border: 2px solid var(--color-border);
    border-radius: 12px;
    padding: 1.5rem;
    cursor: pointer;
    transition: all 0.3s;
    position: relative;
  }

  .parcel-card:hover {
    border-color: var(--color-primary);
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0, 122, 61, 0.1);
  }

  .parcel-card.selected {
    border-color: var(--color-primary);
    background: #f0fdf4;
    box-shadow: 0 0 0 3px rgba(0, 122, 61, 0.1);
  }

  .parcel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }

  .parcel-id {
    font-size: 1.125rem;
    font-weight: 700;
    color: var(--text-primary);
  }

  .parcel-badge {
    font-size: 0.75rem;
    color: var(--color-primary);
    font-weight: 600;
  }

  .parcel-details {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    margin-bottom: 1rem;
  }

  .parcel-location,
  .parcel-size {
    color: var(--color-disabled);
    font-size: 0.9375rem;
  }

  .parcel-status {
    display: flex;
    justify-content: flex-end;
  }

  .status-tag {
    padding: 0.25rem 0.75rem;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
  }

  .status-tag.verified {
    background: #e6f2ec;
    color: var(--color-primary);
    border: 1px solid rgba(0, 122, 61, 0.15);
  }

  /* Selected Parcel Info */
  .selected-parcel-info {
    background: var(--bg-primary);
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 2rem;
    border: 1px solid var(--color-border);
  }

  .parcel-summary {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .parcel-summary .parcel-id {
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--text-primary);
  }

  .parcel-summary .parcel-details {
    display: flex;
    gap: 1rem;
    color: var(--color-disabled);
  }

  /* Transaction Types */
  .transaction-types {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
    gap: 2rem;
    margin-bottom: 3rem;
  }

  .transaction-type {
    background: var(--bg-primary);
    border: 2px solid var(--color-border);
    border-radius: 12px;
    padding: 1.5rem;
    cursor: pointer;
    transition: all 0.3s;
  }

  .transaction-type:hover {
    border-color: var(--color-primary);
  }

  .transaction-type.selected {
    border-color: var(--color-primary);
    background: #f0fdf4;
    box-shadow: 0 0 0 3px rgba(0, 122, 61, 0.1);
  }

  .transaction-header {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1.5rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid var(--color-border);
  }

  .transaction-icon {
    font-size: 2rem;
  }

  .transaction-title {
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--text-primary);
  }

  .transaction-fields {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  /* Form Styles */
  .form-group {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .form-label {
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--text-primary);
    text-transform: uppercase;
    letter-spacing: 0.3px;
  }

  .form-input,
  .form-select,
  .form-textarea {
    padding: 0.75rem 1rem;
    border: 1.5px solid var(--color-border);
    background: white;
    border-radius: 8px;
    font-size: 0.9375rem;
    color: var(--text-primary);
    transition: all 0.2s;
  }

  .form-input:focus,
  .form-select:focus,
  .form-textarea:focus {
    outline: none;
    border-color: var(--color-primary);
    box-shadow: 0 0 0 3px rgba(0, 122, 61, 0.1);
    background: white;
  }

  .form-input:disabled,
  .form-select:disabled,
  .form-textarea:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    background: var(--bg-primary);
  }

  .form-textarea {
    resize: vertical;
    min-height: 80px;
  }

  /* Publish Section */
  .publish-section {
    max-width: 700px;
    margin: 0 auto;
  }

  .listing-preview {
    margin-bottom: 2rem;
  }

  .listing-preview h3 {
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 1rem;
  }

  .preview-card {
    background: var(--bg-primary);
    border: 1px solid var(--color-border);
    border-radius: 12px;
    padding: 1.5rem;
  }

  .preview-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }

  .preview-id {
    font-size: 1.125rem;
    font-weight: 700;
    color: var(--text-primary);
  }

  .preview-badge.verified {
    background: #e6f2ec;
    color: var(--color-primary);
    padding: 0.25rem 0.75rem;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
    border: 1px solid rgba(0, 122, 61, 0.15);
  }

  .preview-details {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    margin-bottom: 1rem;
  }

  .preview-location,
  .preview-size,
  .preview-price {
    color: var(--color-disabled);
  }

  .preview-price {
    font-size: 1.125rem;
    font-weight: 700;
    color: var(--text-primary);
  }

  .preview-terms {
    padding: 1rem;
    background: white;
    border-radius: 8px;
    border: 1px solid var(--color-border);
    font-size: 0.9375rem;
    color: var(--color-disabled);
  }

  .publish-info {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
  }

  .info-card {
    background: var(--bg-primary);
    border: 1px solid var(--color-border);
    border-radius: 12px;
    padding: 1.5rem;
  }

  .info-card h4 {
    font-size: 1rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 1rem;
  }

  .info-card ul {
    list-style: none;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .info-card li {
    color: var(--color-disabled);
    font-size: 0.9375rem;
  }

  .url-display {
    background: white;
    border: 1px solid var(--color-border);
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 0.5rem;
  }

  .url-display code {
    color: var(--color-primary);
    font-family: 'Courier New', monospace;
    font-size: 0.875rem;
  }

  .url-description {
    color: var(--color-disabled);
    font-size: 0.875rem;
  }

  .publish-actions {
    text-align: center;
    margin-top: 2rem;
  }

  /* Confirmation Screen */
  .confirmation-screen {
    text-align: center;
  }

  .confirmation-card {
    max-width: 600px;
    margin: 0 auto;
    padding: 3rem 2rem;
  }

  .confirmation-icon {
    margin-bottom: 2rem;
  }

  .confirmation-card h2 {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 1.5rem;
  }

  .status-section {
    margin-bottom: 2rem;
  }

  .status-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.5rem;
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.9375rem;
  }

  .status-badge.success {
    background: #e6f2ec;
    color: var(--color-primary);
    border: 1px solid rgba(0, 122, 61, 0.15);
  }

  .status-badge.warning {
    background: #fef3c7;
    color: #d97706;
    border: 1px solid rgba(217, 119, 6, 0.15);
  }

  .listing-url-section {
    margin-bottom: 2rem;
  }

  .url-label {
    font-size: 0.875rem;
    color: var(--color-disabled);
    margin-bottom: 0.5rem;
  }

  .url-value {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    padding: 1rem;
    background: var(--bg-primary);
    border: 1px solid var(--color-border);
    border-radius: 8px;
  }

  .url-value code {
    color: var(--color-primary);
    font-family: 'Courier New', monospace;
    font-size: 0.875rem;
  }

  .message-section {
    margin-bottom: 2rem;
  }

  .message-card {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1.5rem;
    background: var(--bg-primary);
    border: 1px solid var(--color-border);
    border-radius: 12px;
    text-align: left;
  }

  .message-icon {
    font-size: 2rem;
  }

  .message-content h4 {
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 0.5rem;
  }

  .message-content p {
    color: var(--color-disabled);
    font-size: 0.9375rem;
  }

  .next-steps {
    text-align: left;
    background: var(--bg-primary);
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 2rem;
    border: 1px solid var(--color-border);
  }

  .next-steps h4 {
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 1rem;
  }

  .next-steps ul {
    list-style: none;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .next-steps li {
    color: var(--color-disabled);
  }

  /* Empty State */
  .empty-state {
    text-align: center;
    padding: 3rem 2rem;
    background: white;
    border: 1px solid var(--color-border);
    border-radius: 12px;
  }

  .empty-state h3 {
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 1rem;
  }

  .empty-state p {
    color: var(--color-disabled);
    margin-bottom: 2rem;
  }

  /* Buttons */
  .btn {
    padding: 0.625rem 1.25rem;
    border-radius: 8px;
    border: none;
    font-weight: 600;
    font-size: 0.9375rem;
    cursor: pointer;
    transition: all 0.2s ease;
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    white-space: nowrap;
  }

  .btn-primary {
    background: var(--color-primary);
    color: white;
  }

  .btn-primary:hover:not(:disabled) {
    background: var(--color-primary-hover);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0, 122, 61, 0.2);
  }

  .btn-primary:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
  }

  .btn-secondary {
    background: white;
    color: var(--color-primary);
    border: 1px solid var(--color-border);
  }

  .btn-secondary:hover {
    background: #f8fafc;
    border-color: var(--color-primary);
  }

  .btn-lg {
    padding: 0.875rem 2rem;
    font-size: 1rem;
  }

  .btn-sm {
    padding: 0.5rem 1rem;
    font-size: 0.875rem;
  }

  .step-actions {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 3rem;
    gap: 1rem;
  }

  .step-actions .btn {
    min-width: 120px;
  }

  /* Animations */
  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }

  .animate-spin {
    animation: spin 1s linear infinite;
  }

  /* Sale Form Section */
  .sale-form-section {
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
    margin-bottom: 2rem;
  }

  .sale-form-section .form-group {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .sale-form-section .form-label {
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--text-primary);
    display: flex;
    align-items: center;
    gap: 0.25rem;
  }

  .sale-form-section .form-input,
  .sale-form-section .form-textarea {
    padding: 0.75rem 1rem;
    border: 2px solid var(--color-border);
    border-radius: 8px;
    font-size: 1rem;
    background: white;
    transition: border-color 0.2s;
  }

  .sale-form-section .form-input:focus,
  .sale-form-section .form-textarea:focus {
    outline: none;
    border-color: var(--color-primary);
    box-shadow: 0 0 0 3px rgba(0,122,61,0.15);
  }

  .field-hint {
    font-size: 0.75rem;
    color: var(--color-disabled);
  }

  .sale-form-section .info-card {
    background: var(--bg-primary);
    border: 1px solid var(--color-border);
    border-radius: 12px;
    padding: 1.5rem;
  }

  .sale-form-section .info-card h4 {
    font-size: 1rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .sale-form-section .info-card p {
    color: var(--color-disabled);
    font-size: 0.9375rem;
    line-height: 1.5;
  }

  /* Review Section */
  .review-section {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
    margin-bottom: 2rem;
  }

  .review-card {
    background: white;
    border: 1px solid var(--color-border);
    border-radius: 12px;
    padding: 1.5rem;
  }

  .review-card h3 {
    font-size: 1.125rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 1rem;
  }

  .review-row {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    padding: 0.75rem 0;
    border-bottom: 1px solid var(--color-border);
  }

  .review-row:last-child {
    border-bottom: none;
  }

  .review-label {
    font-size: 0.875rem;
    color: var(--color-disabled);
    font-weight: 500;
  }

  .review-value {
    font-size: 0.9375rem;
    font-weight: 600;
    color: var(--text-primary);
    text-align: right;
  }

  /* Payment Summary Card */
  .payment-summary-card {
    background: white;
    border: 1px solid var(--color-border);
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 2rem;
  }

  .payment-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid var(--color-border);
  }

  .payment-header h3 {
    font-size: 1.125rem;
    font-weight: 700;
    color: var(--text-primary);
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .fee-amount {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--color-primary);
  }

  .payment-details {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .detail-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem 0;
  }

  .detail-row.total {
    padding-top: 1rem;
    border-top: 2px solid var(--color-border);
    font-size: 1.125rem;
  }

  .detail-row.total strong {
    color: var(--color-primary);
    font-size: 1.25rem;
  }

  .detail-row span {
    color: var(--color-disabled);
    font-size: 0.9375rem;
  }

  .detail-row strong {
    color: var(--text-primary);
    font-weight: 600;
  }

  /* Payment Methods Section */
  .payment-methods-section {
    margin-bottom: 2rem;
  }

  .payment-methods-section h4 {
    font-size: 1rem;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 1rem;
  }

  .payment-methods-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 1rem;
  }

  .payment-method-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
    padding: 1.5rem;
    background: white;
    border: 2px solid var(--color-border);
    border-radius: 12px;
    cursor: pointer;
    transition: all 0.2s;
  }

  .payment-method-card:hover {
    border-color: var(--color-primary);
    background: var(--bg-primary);
  }

  .payment-method-card span {
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--text-primary);
  }

  /* Approval Flow Card */
  .approval-flow-card {
    background: var(--bg-primary);
    border: 1px solid var(--color-border);
    border-radius: 12px;
    padding: 1.5rem;
  }

  .approval-flow-card h3 {
    font-size: 1.125rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .flow-description {
    color: var(--color-disabled);
    font-size: 0.9375rem;
    margin-bottom: 1rem;
  }

  .approval-steps {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    margin-bottom: 1rem;
  }

  .approval-step {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .step-icon {
    width: 40px;
    height: 40px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .step-icon.buyer {
    background: #dbeafe;
    color: #2563eb;
  }

  .step-icon.chief {
    background: #fef3c7;
    color: #d97706;
  }

  .step-icon.witness {
    background: #e6f2ec;
    color: var(--color-primary);
  }

  .step-info {
    display: flex;
    flex-direction: column;
    gap: 0.125rem;
  }

  .step-info strong {
    font-size: 0.9375rem;
    color: var(--text-primary);
  }

  .step-info span {
    font-size: 0.8125rem;
    color: var(--color-disabled);
  }

  .flow-note {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
    background: #fff7ed;
    border: 1px solid #fed7aa;
    border-radius: 8px;
    font-size: 0.8125rem;
    color: #9a3412;
  }

  /* Error Message */
  .error-message {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
    background: #fef2f2;
    border: 1px solid #fecaca;
    border-radius: 8px;
    color: #dc2626;
    font-size: 0.875rem;
  }

  /* Success Screen */
  .success-icon {
    margin-bottom: 1.5rem;
  }

  .success-detail {
    color: var(--color-disabled);
    font-size: 1rem;
    margin-bottom: 1.5rem;
  }

  .tx-summary {
    background: var(--bg-primary);
    border: 1px solid var(--color-border);
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    text-align: left;
  }

  .summary-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem 0;
    border-bottom: 1px solid var(--color-border);
  }

  .summary-row:last-child {
    border-bottom: none;
  }

  .summary-row span {
    font-size: 0.875rem;
    color: var(--color-disabled);
  }

  .summary-row strong {
    font-size: 0.9375rem;
    color: var(--text-primary);
  }

  .summary-row small {
    color: var(--color-disabled);
    margin-left: 0.25rem;
    font-size: 0.75rem;
  }

  .sms-notice {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    padding: 1rem 1.25rem;
    background: #ecfdf5;
    border: 1px solid #a7f3d0;
    border-radius: 10px;
    margin-bottom: 1.5rem;
    text-align: left;
  }

  .sms-notice strong {
    display: block;
    color: #065f46;
    font-size: 0.9375rem;
    margin-bottom: 0.25rem;
  }

  .sms-notice p {
    color: #047857;
    font-size: 0.8125rem;
    margin: 0;
  }

  /* Spinner */
  .spinner {
    display: inline-block;
    width: 16px;
    height: 16px;
    border: 2px solid rgba(255,255,255,0.3);
    border-top: 2px solid white;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  /* Responsive */
  @media (max-width: 768px) {
    .navbar-content {
      padding: 0 1rem;
    }

    .navbar-menu {
      display: none;
    }

    .main-content {
      padding: 1rem;
    }

    .step-container {
      padding: 1.5rem;
    }

    .step-header h1 {
      font-size: 1.5rem;
    }

    .parcels-grid {
      grid-template-columns: 1fr;
    }

    .transaction-types {
      grid-template-columns: 1fr;
    }

    .publish-info {
      grid-template-columns: 1fr;
    }

    .step-actions {
      flex-direction: column;
    }

    .step-actions .btn {
      width: 100%;
      justify-content: center;
    }
  }
</style>
