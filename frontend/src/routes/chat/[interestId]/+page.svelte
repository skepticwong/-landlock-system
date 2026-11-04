<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import { ArrowLeft, Send, Phone, Mail, DollarSign, Check, X, AlertCircle } from 'lucide-svelte';
  import { fetchMessages, sendMessage, fetchMyInterests } from '$lib/api.js';
  import Navbar from '$lib/components/Navbar.svelte';
  import PaymentModal from '$lib/components/PaymentModal.svelte';

  let interestId: number;
  let messages: any[] = [];
  let newMessage = '';
  let isLoading = true;
  let error: string | null = null;
  let currentUser: any = null;
  let interest: any = null;
  let otherParty: any = null;
  let isSeller = false;
  let pollingInterval: any = null;
  
  // Payment state
  let showPaymentModal = false;
  let paymentType = 'land_transfer';
  let transferFee = 10000;
  let paymentDescription = 'Land Purchase Payment';
  
  // Calculate total payment (sale price + transfer fee)
  $: salePrice = interest?.listing_price ? parseFloat(interest.listing_price) : 0;
  $: totalPayment = salePrice + transferFee;

  onMount(async () => {
    interestId = parseInt($page.params.interestId);
    await loadCurrentUser();
    await loadInterest();

    // Only start polling if interest is approved and no error
    if (interest && interest.status === 'contact_shared' && !error) {
      await loadMessages();
      // Poll for new messages every 3 seconds
      pollingInterval = setInterval(loadMessages, 3000);
    } else {
      isLoading = false;
    }
  });

  onDestroy(() => {
    if (pollingInterval) clearInterval(pollingInterval);
  });

  async function loadCurrentUser() {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        goto('/login');
        return;
      }
      const res = await fetch('http://localhost:5000/api/user/me', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        currentUser = await res.json();
      } else {
        goto('/login');
      }
    } catch (e) {
      goto('/login');
    }
  }

  async function loadInterest() {
    try {
      // First try to find in buyer's interests
      let interests = await fetchMyInterests();
      interest = interests.find((i: any) => i.id === interestId);

      // If not found as buyer, try to find in seller's interests
      if (!interest) {
        const { fetchBuyerInterests } = await import('$lib/api.js');
        const sellerInterests = await fetchBuyerInterests();
        interest = sellerInterests.find((i: any) => i.id === interestId);
        isSeller = true;
      } else {
        isSeller = false;
      }

      if (!interest) {
        error = 'Interest not found or you do not have permission to access this chat';
        isLoading = false;
        return;
      }

      if (interest.status !== 'contact_shared') {
        error = 'This interest has not been approved yet. Please wait for the seller to approve your request.';
        isLoading = false;
        return;
      }

      // Set other party info based on whether user is buyer or seller
      if (!isSeller) {
        // User is buyer, other party is seller
        otherParty = {
          name: interest.sellerName,
          phone: interest.sellerPhone,
          email: interest.sellerEmail,
          id: interest.seller_id
        };
      } else {
        // User is seller, other party is buyer
        otherParty = {
          name: interest.buyerName,
          phone: interest.buyerPhone,
          email: '', // Seller doesn't see buyer email until approved
          id: interest.buyer_id
        };
      }
    } catch (e: any) {
      error = e.message;
      isLoading = false;
    }
  }

  async function loadMessages() {
    if (!interest || interest.status !== 'contact_shared') {
      isLoading = false;
      return;
    }

    try {
      messages = await fetchMessages(interestId);
      scrollToBottom();
    } catch (e: any) {
      console.error('Failed to load messages:', e);
      error = e.message || 'Failed to load messages';
    } finally {
      isLoading = false;
    }
  }

  async function handleSendMessage() {
    if (!newMessage.trim()) return;

    try {
      await sendMessage(interestId, newMessage);
      newMessage = '';
      await loadMessages();
    } catch (e: any) {
      alert(e.message || 'Failed to send message');
    }
  }

  function scrollToBottom() {
    const chatContainer = document.querySelector('.messages-container');
    if (chatContainer) {
      chatContainer.scrollTop = chatContainer.scrollHeight;
    }
  }

  function formatTime(timestamp: string) {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  }

  function formatDate(timestamp: string) {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    const today = new Date();
    if (date.toDateString() === today.toDateString()) {
      return 'Today';
    }
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  }

  function initiatePayment() {
    showPaymentModal = true;
  }

  function handlePaymentCompleted(event: any) {
    const payment = event.detail.payment;
    // Payment completed successfully
    // You can add additional logic here like updating the interest status
    console.log('Payment completed:', payment);
  }
</script>

<svelte:head>
  <title>Chat — LandLock</title>
</svelte:head>

<Navbar userType={currentUser ? "citizen" : "citizen"} activeLink="/transactions" userName={currentUser?.full_name || ''} showNotification={!!currentUser} />

<div class="chat-page">
  <div class="chat-header">
    <button class="back-btn" on:click={() => goto('/transactions')}>
      <ArrowLeft size={20} />
      Back to Transactions
    </button>
    
    {#if interest}
      <div class="chat-info">
        <div class="listing-info">
          <h2>{interest.listing_title}</h2>
          <p class="listing-price">
            {interest.listing_price ? `MK ${Number(interest.listing_price).toLocaleString()}` : 'Price on request'}
          </p>
          {#if interest.listing_location}
            <p class="listing-location">{interest.listing_location}</p>
          {/if}
        </div>
        
        <div class="other-party-info">
          <div class="party-avatar">
            {otherParty?.name?.charAt(0).toUpperCase() || '?'}
          </div>
          <div class="party-details">
            <div class="party-name">{otherParty?.name || 'Unknown'}</div>
            <div class="party-role">{isSeller ? 'Buyer' : 'Seller'}</div>
          </div>
        </div>
      </div>
    {/if}
  </div>

  <div class="chat-content">
    {#if isLoading}
      <div class="loading-state">
        <div class="spinner"></div>
        <p>Loading messages...</p>
      </div>
    {:else if error}
      <div class="error-state">
        <AlertCircle size={48} />
        <p>{error}</p>
        <button class="btn btn-primary" on:click={() => goto('/transactions')}>Go Back</button>
      </div>
    {:else}
      <div class="messages-container">
        {#if messages.length === 0}
          <div class="empty-chat">
            <div class="empty-icon">
              <Send size={48} />
            </div>
            <h3>No messages yet</h3>
            <p>Start the conversation with {otherParty?.name || 'the other party'}</p>
          </div>
        {:else}
          {#each messages as message (message.id)}
            <div class="message {message.isMine ? 'mine' : 'theirs'}">
              <div class="message-header">
                <span class="sender-name">{message.senderName}</span>
                <span class="message-time">{formatTime(message.created_at)}</span>
              </div>
              <div class="message-content">
                {message.message}
              </div>
              {#if message.isMine && message.is_read}
                <div class="read-receipt">
                  <Check size={12} />
                  <span>Read</span>
                </div>
              {/if}
            </div>
          {/each}
        {/if}
      </div>

      <div class="chat-actions">
        {#if interest?.status === 'contact_shared' && otherParty?.phone}
          <div class="contact-info">
            <div class="contact-item">
              <Phone size={16} />
              <span>{otherParty.phone}</span>
            </div>
            {#if otherParty.email}
              <div class="contact-item">
                <Mail size={16} />
                <span>{otherParty.email}</span>
              </div>
            {/if}
          </div>
        {/if}

        <div class="payment-section">
          <button class="btn btn-payment" on:click={initiatePayment}>
            <DollarSign size={18} />
            Pay MK {totalPayment.toLocaleString()}
          </button>
        </div>

        <div class="message-input">
          <textarea
            class="input-field"
            bind:value={newMessage}
            placeholder="Type your message..."
            rows="1"
            on:keydown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSendMessage();
              }
            }}
          ></textarea>
          <button 
            class="send-btn" 
            on:click={handleSendMessage}
            disabled={!newMessage.trim()}
          >
            <Send size={20} />
          </button>
        </div>
      </div>
    {/if}
  </div>
</div>

<style>
  :global(*) {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }

  :global(body) {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', sans-serif;
    background: #f8fafc;
    color: #0f172a;
  }

  .chat-page {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  .chat-header {
    background: white;
    border-bottom: 1px solid #e2e8f0;
    padding: 1rem 2rem;
    display: flex;
    align-items: center;
    gap: 2rem;
    position: sticky;
    top: 0;
    z-index: 10;
  }

  .back-btn {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background: none;
    border: none;
    color: #64748b;
    font-weight: 600;
    cursor: pointer;
    padding: 0.5rem 1rem;
    border-radius: 8px;
    transition: all 0.2s;
  }

  .back-btn:hover {
    background: #f1f5f9;
    color: #0f172a;
  }

  .chat-info {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .listing-info h2 {
    font-size: 1.25rem;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 0.25rem;
  }

  .listing-price {
    font-size: 1.125rem;
    font-weight: 700;
    color: #007A3D;
    margin-bottom: 0.25rem;
  }

  .listing-location {
    font-size: 0.875rem;
    color: #64748b;
  }

  .other-party-info {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 0.75rem 1rem;
    background: #f8fafc;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
  }

  .party-avatar {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    background: #007A3D;
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.25rem;
    font-weight: 700;
  }

  .party-name {
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 0.125rem;
  }

  .party-role {
    font-size: 0.875rem;
    color: #64748b;
  }

  .chat-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .messages-container {
    flex: 1;
    overflow-y: auto;
    padding: 2rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .empty-chat {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 4rem 2rem;
    text-align: center;
    color: #64748b;
  }

  .empty-icon {
    margin-bottom: 1rem;
    color: #cbd5e1;
  }

  .empty-chat h3 {
    font-size: 1.25rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
    color: #0f172a;
  }

  .message {
    max-width: 70%;
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .message.mine {
    align-self: flex-end;
  }

  .message.theirs {
    align-self: flex-start;
  }

  .message-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.75rem;
    color: #64748b;
  }

  .message.mine .message-header {
    flex-direction: row-reverse;
  }

  .message-content {
    padding: 0.875rem 1.25rem;
    border-radius: 16px;
    line-height: 1.5;
    word-wrap: break-word;
  }

  .message.mine .message-content {
    background: #007A3D;
    color: white;
    border-bottom-right-radius: 4px;
  }

  .message.theirs .message-content {
    background: white;
    color: #0f172a;
    border: 1px solid #e2e8f0;
    border-bottom-left-radius: 4px;
  }

  .read-receipt {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    font-size: 0.75rem;
    color: #64748b;
    align-self: flex-end;
  }

  .chat-actions {
    background: white;
    border-top: 1px solid #e2e8f0;
    padding: 1rem 2rem;
  }

  .contact-info {
    display: flex;
    gap: 1rem;
    margin-bottom: 1rem;
    padding: 0.75rem 1rem;
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    border-radius: 8px;
  }

  .contact-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.875rem;
    color: #166534;
    font-weight: 500;
  }

  .payment-section {
    margin-bottom: 1rem;
  }

  .btn-payment {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    padding: 0.875rem;
    background: #007A3D;
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 700;
    font-size: 1rem;
    cursor: pointer;
    transition: background 0.2s;
  }

  .btn-payment:hover {
    background: #005c2e;
  }

  .message-input {
    display: flex;
    gap: 0.75rem;
    align-items: flex-end;
  }

  .input-field {
    flex: 1;
    padding: 0.875rem 1rem;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    font-family: inherit;
    font-size: 0.9375rem;
    resize: none;
    outline: none;
    transition: border-color 0.2s;
    min-height: 48px;
    max-height: 120px;
  }

  .input-field:focus {
    border-color: #007A3D;
    box-shadow: 0 0 0 3px rgba(0, 122, 61, 0.1);
  }

  .send-btn {
    width: 48px;
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #007A3D;
    color: white;
    border: none;
    border-radius: 12px;
    cursor: pointer;
    transition: all 0.2s;
  }

  .send-btn:hover:not(:disabled) {
    background: #005c2e;
    transform: scale(1.05);
  }

  .send-btn:disabled {
    background: #cbd5e1;
    cursor: not-allowed;
  }

  .loading-state,
  .error-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 4rem 2rem;
    gap: 1rem;
    text-align: center;
    color: #64748b;
  }

  .spinner {
    width: 40px;
    height: 40px;
    border: 3px solid #e2e8f0;
    border-top-color: #007A3D;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .btn {
    padding: 0.5rem 1rem;
    border-radius: 8px;
    font-weight: 600;
    cursor: pointer;
    border: none;
  }

  .btn-primary {
    background: #007A3D;
    color: white;
  }

  @media (max-width: 768px) {
    .chat-header {
      flex-direction: column;
      align-items: flex-start;
      gap: 1rem;
      padding: 1rem;
    }

    .chat-info {
      flex-direction: column;
      align-items: flex-start;
      gap: 1rem;
      width: 100%;
    }

    .other-party-info {
      width: 100%;
    }

    .messages-container {
      padding: 1rem;
    }

    .message {
      max-width: 85%;
    }

    .chat-actions {
      padding: 1rem;
    }

    .contact-info {
      flex-direction: column;
    }
  }
</style>

<PaymentModal
  bind:isOpen={showPaymentModal}
  paymentType={paymentType}
  amount={totalPayment}
  description={paymentDescription}
  on:paymentCompleted={handlePaymentCompleted}
/>
