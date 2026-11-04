<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { CreditCard, Smartphone, Wallet, CheckCircle, X, Loader2 } from 'lucide-svelte';

  const dispatch = createEventDispatcher();

  export let isOpen = false;
  export let paymentType = '';
  export let amount = 0;
  export let description = '';
  export let plotId: number | null = null;
  export let transactionId: number | null = null;

  const API = 'http://localhost:5000';

  let paymentMethod = 'airtel_money';
  let phoneNumber = '';
  let cardNumber = '';
  let cardExpiry = '';
  let cardCvv = '';
  let isProcessing = false;
  let paymentId: number | null = null;
  let paymentStatus = '';
  let errorMessage = '';

  const paymentMethods = [
    { id: 'airtel_money', name: 'Airtel Money', icon: Smartphone },
    { id: 'tnm_mpamba', name: 'TNM Mpamba', icon: Smartphone },
    { id: 'bank_card', name: 'Bank Card', icon: CreditCard },
    { id: 'cash', name: 'Cash Payment', icon: Wallet }
  ];

  function authHeaders() {
    return { 'Authorization': `Bearer ${localStorage.getItem('token')}` };
  }

  async function initiatePayment() {
    isProcessing = true;
    errorMessage = '';
    paymentStatus = '';

    try {
      const body: any = {
        payment_type: paymentType,
        payment_method: paymentMethod
      };

      if (paymentMethod === 'airtel_money' || paymentMethod === 'tnm_mpamba') {
        if (!phoneNumber) {
          errorMessage = 'Phone number is required';
          isProcessing = false;
          return;
        }
        body.phone_number = phoneNumber;
      } else if (paymentMethod === 'bank_card') {
        if (!cardNumber || !cardExpiry || !cardCvv) {
          errorMessage = 'Card details are required';
          isProcessing = false;
          return;
        }
        body.card_number = cardNumber;
        body.card_expiry = cardExpiry;
        body.card_cvv = cardCvv;
      }

      if (plotId) body.plot_id = plotId;
      if (transactionId) body.transaction_id = transactionId;

      const response = await fetch(`${API}/api/payments/initiate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...authHeaders()
        },
        body: JSON.stringify(body)
      });

      if (response.ok) {
        const result = await response.json();
        paymentId = result.payment_id;
        
        // Auto-confirm mock payment
        await confirmPayment();
      } else {
        const error = await response.json();
        errorMessage = error.error || 'Payment initiation failed';
        isProcessing = false;
      }
    } catch (error) {
      console.error('Payment error:', error);
      errorMessage = 'Network error. Please try again.';
      isProcessing = false;
    }
  }

  async function confirmPayment() {
    if (!paymentId) return;

    try {
      const response = await fetch(`${API}/api/payments/${paymentId}/confirm`, {
        method: 'POST',
        headers: authHeaders()
      });

      if (response.ok) {
        const result = await response.json();
        paymentStatus = 'completed';
        dispatch('paymentCompleted', { payment: result.payment });
        
        // Close modal after success
        setTimeout(() => {
          closeModal();
        }, 2000);
      } else {
        const error = await response.json();
        errorMessage = error.error || 'Payment confirmation failed';
        paymentStatus = 'failed';
        isProcessing = false;
      }
    } catch (error) {
      console.error('Confirmation error:', error);
      errorMessage = 'Failed to confirm payment';
      paymentStatus = 'failed';
      isProcessing = false;
    }
  }

  function closeModal() {
    isOpen = false;
    // Reset form
    paymentMethod = 'airtel_money';
    phoneNumber = '';
    cardNumber = '';
    cardExpiry = '';
    cardCvv = '';
    isProcessing = false;
    paymentId = null;
    paymentStatus = '';
    errorMessage = '';
  }

  function formatCardNumber(value: string) {
    return value.replace(/\s/g, '').replace(/(.{4})/g, '$1 ').trim();
  }

  function formatExpiry(value: string) {
    if (value.length === 2 && !value.includes('/')) {
      return value + '/';
    }
    return value;
  }
</script>

{#if isOpen}
  <div class="modal-overlay" on:click={closeModal}>
    <div class="modal-content" on:click|stopPropagation>
      <div class="modal-header">
        <h2>Complete Payment</h2>
        <button class="close-button" on:click={closeModal}>
          <X size={24} />
        </button>
      </div>

      <div class="modal-body">
        <div class="payment-summary">
          <div class="summary-item">
            <span class="label">Service:</span>
            <span class="value">{description}</span>
          </div>
          <div class="summary-item">
            <span class="label">Amount:</span>
            <span class="value amount">MWK {amount.toLocaleString()}</span>
          </div>
        </div>

        {#if paymentStatus === 'completed'}
          <div class="success-message">
            <CheckCircle size={48} />
            <h3>Payment Successful!</h3>
            <p>Your payment has been processed successfully.</p>
          </div>
        {:else if paymentStatus === 'failed'}
          <div class="error-message">
            <h3>Payment Failed</h3>
            <p>{errorMessage}</p>
            <button class="btn btn-primary" on:click={() => { paymentStatus = ''; errorMessage = ''; }}>
              Try Again
            </button>
          </div>
        {:else}
          <div class="payment-methods">
            <h3>Select Payment Method</h3>
            <div class="methods-grid">
              {#each paymentMethods as method}
                <button 
                  class="method-card {paymentMethod === method.id ? 'selected' : ''}"
                  on:click={() => paymentMethod = method.id}
                  disabled={isProcessing}
                >
                  <svelte:component this={method.icon} size={24} />
                  <span>{method.name}</span>
                </button>
              {/each}
            </div>
          </div>

          {#if paymentMethod === 'airtel_money' || paymentMethod === 'tnm_mpamba'}
            <div class="form-section">
              <label>Phone Number</label>
              <input 
                type="tel" 
                placeholder="09XX XXX XXX" 
                bind:value={phoneNumber}
                disabled={isProcessing}
              />
            </div>
          {:else if paymentMethod === 'bank_card'}
            <div class="form-section">
              <label>Card Number</label>
              <input 
                type="text" 
                placeholder="1234 5678 9012 3456" 
                bind:value={cardNumber}
                on:input={(e) => cardNumber = formatCardNumber(e.target.value)}
                maxlength="19"
                disabled={isProcessing}
              />
            </div>
            <div class="form-row">
              <div class="form-section">
                <label>Expiry Date</label>
                <input 
                  type="text" 
                  placeholder="MM/YY" 
                  bind:value={cardExpiry}
                  on:input={(e) => cardExpiry = formatExpiry(e.target.value)}
                  maxlength="5"
                  disabled={isProcessing}
                />
              </div>
              <div class="form-section">
                <label>CVV</label>
                <input 
                  type="text" 
                  placeholder="123" 
                  bind:value={cardCvv}
                  maxlength="3"
                  disabled={isProcessing}
                />
              </div>
            </div>
          {:else if paymentMethod === 'cash'}
            <div class="cash-info">
              <p>Please visit your nearest LandLock office to complete the cash payment.</p>
              <p>Bring your reference number: <strong>{paymentType.toUpperCase()}-{Date.now()}</strong></p>
            </div>
          {/if}

          {#if errorMessage}
            <div class="error-alert">
              {errorMessage}
            </div>
          {/if}

          <div class="modal-actions">
            <button class="btn btn-secondary" on:click={closeModal} disabled={isProcessing}>
              Cancel
            </button>
            <button 
              class="btn btn-primary" 
              on:click={initiatePayment} 
              disabled={isProcessing || paymentMethod === 'cash'}
            >
              {#if isProcessing}
                <Loader2 class="spinner" size={20} />
                Processing...
              {:else}
                Pay MWK {amount.toLocaleString()}
              {/if}
            </button>
          </div>
        {/if}
      </div>
    </div>
  </div>
{/if}

<style>
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
    padding: 1rem;
  }

  .modal-content {
    background: white;
    border-radius: 16px;
    max-width: 500px;
    width: 100%;
    max-height: 90vh;
    overflow-y: auto;
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.5rem;
    border-bottom: 1px solid #e5e7eb;
  }

  .modal-header h2 {
    font-size: 1.25rem;
    font-weight: 600;
    color: #1f2937;
    margin: 0;
  }

  .close-button {
    background: none;
    border: none;
    color: #6b7280;
    cursor: pointer;
    padding: 0.25rem;
    border-radius: 4px;
    transition: background 0.2s;
  }

  .close-button:hover {
    background: #f3f4f6;
  }

  .modal-body {
    padding: 1.5rem;
  }

  .payment-summary {
    background: #f9fafb;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1.5rem;
  }

  .summary-item {
    display: flex;
    justify-content: space-between;
    margin-bottom: 0.5rem;
  }

  .summary-item:last-child {
    margin-bottom: 0;
  }

  .label {
    color: #6b7280;
    font-size: 0.875rem;
  }

  .value {
    color: #1f2937;
    font-weight: 500;
  }

  .amount {
    color: #007A3D;
    font-weight: 700;
    font-size: 1.125rem;
  }

  .success-message {
    text-align: center;
    padding: 2rem;
    color: #007A3D;
  }

  .success-message h3 {
    margin: 1rem 0 0.5rem;
    font-size: 1.25rem;
  }

  .error-message {
    text-align: center;
    padding: 2rem;
    color: #dc2626;
  }

  .error-message h3 {
    margin: 0 0 0.5rem;
  }

  .payment-methods h3 {
    font-size: 1rem;
    font-weight: 600;
    color: #1f2937;
    margin-bottom: 1rem;
  }

  .methods-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 0.75rem;
    margin-bottom: 1.5rem;
  }

  .method-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
    padding: 1rem;
    border: 2px solid #e5e7eb;
    border-radius: 8px;
    background: white;
    cursor: pointer;
    transition: all 0.2s;
  }

  .method-card:hover:not(:disabled) {
    border-color: #007A3D;
    background: #f0fdf4;
  }

  .method-card.selected {
    border-color: #007A3D;
    background: #f0fdf4;
  }

  .method-card:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .method-card span {
    font-size: 0.875rem;
    font-weight: 500;
    color: #1f2937;
  }

  .form-section {
    margin-bottom: 1rem;
  }

  .form-section label {
    display: block;
    font-size: 0.875rem;
    font-weight: 500;
    color: #374151;
    margin-bottom: 0.5rem;
  }

  .form-section input {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    font-size: 0.9375rem;
    transition: border-color 0.2s;
  }

  .form-section input:focus {
    outline: none;
    border-color: #007A3D;
  }

  .form-section input:disabled {
    background: #f3f4f6;
    cursor: not-allowed;
  }

  .form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
  }

  .cash-info {
    background: #fef3c7;
    border: 1px solid #fcd34d;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1.5rem;
  }

  .cash-info p {
    margin: 0.5rem 0;
    color: #92400e;
    font-size: 0.875rem;
  }

  .error-alert {
    background: #fef2f2;
    border: 1px solid #fecaca;
    color: #dc2626;
    padding: 0.75rem;
    border-radius: 6px;
    margin-bottom: 1rem;
    font-size: 0.875rem;
  }

  .modal-actions {
    display: flex;
    gap: 0.75rem;
    justify-content: flex-end;
    margin-top: 1.5rem;
  }

  .btn {
    padding: 0.75rem 1.5rem;
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.9375rem;
    cursor: pointer;
    border: none;
    transition: all 0.2s;
  }

  .btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .btn-primary {
    background: #007A3D;
    color: white;
  }

  .btn-primary:hover:not(:disabled) {
    background: #006633;
  }

  .btn-secondary {
    background: white;
    color: #1f2937;
    border: 1px solid #d1d5db;
  }

  .btn-secondary:hover:not(:disabled) {
    background: #f3f4f6;
  }

  .spinner {
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }

  @media (max-width: 640px) {
    .methods-grid {
      grid-template-columns: 1fr;
    }

    .form-row {
      grid-template-columns: 1fr;
    }
  }
</style>
