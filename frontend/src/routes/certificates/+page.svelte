<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { browser } from '$app/environment';

  // Mock data for user's certificates
  let certificates = [
    {
      id: 'CERT-001',
      parcelId: 'MLW-LIL-8821',
      location: 'Chilomoni, Lilongwe',
      ownerName: 'Grace M. Banda',
      size: 2.4,
      issueDate: '2024-01-15',
      type: 'ownership',
      status: 'verified',
      verificationCode: 'VC-2024-MLW-8821-001',
      qrCode: 'QR-CODE-DATA-8821'
    },
    {
      id: 'CERT-002',
      parcelId: 'MLW-LIL-8822',
      location: 'Area 25, Lilongwe',
      ownerName: 'Grace M. Banda',
      size: 1.8,
      issueDate: '2023-12-01',
      type: 'lease',
      status: 'verified',
      verificationCode: 'VC-2023-MLW-8822-001',
      qrCode: 'QR-CODE-DATA-8822'
    }
  ];

  let isOnline = navigator.onLine;
  let selectedCertificate = null;
  let shareLink = '';
  let isGeneratingShare = false;
  let isDownloading = false;

  onMount(() => {
    if (!browser) return;
    
    // Check authentication
    if (!localStorage.getItem('token')) {
      goto('/login');
      return;
    }

    // Listen for online/offline changes
    window.addEventListener('online', () => isOnline = true);
    window.addEventListener('offline', () => isOnline = false);
  });

  async function downloadCertificate(certificate) {
    if (!isOnline) {
      // Use cached version if offline
      console.log('Using cached certificate for offline download');
      return;
    }

    isDownloading = true;
    try {
      // Generate PDF
      await generatePDF(certificate);
    } catch (error) {
      console.error('Download failed:', error);
    } finally {
      isDownloading = false;
    }
  }

  async function generatePDF(certificate) {
    // Mock PDF generation
    console.log('Generating PDF for certificate:', certificate.id);
    
    // In a real app, this would:
    // 1. Call backend API to generate PDF
    // 2. Include government seal
    // 3. Add QR code
    // 4. Include verification code
    // 5. Download to device
    
    // Simulate download
    const pdfData = {
      fileName: `LandLock_Certificate_${certificate.parcelId}.pdf`,
      content: `Official Land Certificate\n\nParcel ID: ${certificate.parcelId}\nLocation: ${certificate.location}\nOwner: ${certificate.ownerName}\nSize: ${certificate.size} acres\nIssue Date: ${certificate.issueDate}\nType: ${certificate.type}\nVerification Code: ${certificate.verificationCode}\n\nIssued by Ministry of Lands, Malawi`
    };
    
    // Create download
    const blob = new Blob([pdfData.content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = pdfData.fileName;
    a.click();
    URL.revokeObjectURL(url);
  }

  async function shareCertificate(certificate) {
    if (!isOnline) {
      alert('Sharing requires an internet connection');
      return;
    }

    isGeneratingShare = true;
    try {
      // Generate secure, time-limited share link
      shareLink = `https://landlock.mw/verify/${certificate.verificationCode}?token=secure-${Date.now()}`;
      
      // On mobile, use system share dialog
      if (browser && navigator.share) {
        await navigator.share({
          title: 'LandLock Certificate Verification',
          text: `View my official land certificate for ${certificate.parcelId}`,
          url: shareLink
        });
      } else {
        // On desktop, copy to clipboard
        await navigator.clipboard.writeText(shareLink);
        alert('Share link copied to clipboard!');
      }
    } catch (error) {
      console.error('Share failed:', error);
    } finally {
      isGeneratingShare = false;
    }
  }

  function verifyOnline(certificate) {
    if (!isOnline) {
      alert('Online verification requires an internet connection');
      return;
    }
    
    // Open verification page in new tab
    const verificationUrl = `https://landlock.mw/verify/${certificate.verificationCode}`;
    window.open(verificationUrl, '_blank');
  }

  function getStatusColor(status: string): string {
    switch (status) {
      case 'verified': return '#16a34a';
      case 'pending': return '#f59e0b';
      case 'revoked': return '#dc2626';
      default: return '#6b7280';
    }
  }

  function getStatusText(status: string): string {
    switch (status) {
      case 'verified': return 'Verified';
      case 'pending': return 'Pending';
      case 'revoked': return 'Revoked';
      default: return status;
    }
  }

  function getTypeIcon(type: string): string {
    return type === 'ownership' ? '🏠' : '📄';
  }

  function getTypeText(type: string): string {
    return type === 'ownership' ? 'Ownership' : 'Lease';
  }

  function formatDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    });
  }
</script>

<svelte:head>
  <title>Certificates - LandLock</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</svelte:head>

<div class="certificates-page">
  <!-- Navigation -->
  <nav class="navbar">
    <div class="navbar-content">
      <div class="navbar-brand">
        <div class="logo">
          <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
            <rect width="32" height="32" rx="8" fill="url(#gradient)"/>
            <path d="M16 8L22 14H18V20H14V14H10L16 8Z" fill="white"/>
            <defs>
              <linearGradient id="gradient" x1="0" y1="0" x2="32" y2="32">
                <stop stop-color="#667eea"/>
                <stop offset="1" stop-color="#764ba2"/>
              </linearGradient>
            </defs>
          </svg>
        </div>
        <span class="brand-name">LandLock</span>
      </div>
      
      <div class="navbar-menu">
        <a href="/dashboard" class="nav-link">
          <span>Dashboard</span>
        </a>
        <a href="/register-land" class="nav-link">
          <span>Register Land</span>
        </a>
        <a href="/sell-or-lease" class="nav-link">
          <span>Sell or Lease</span>
        </a>
        <a href="/certificates" class="nav-link active">
          <span>Certificates</span>
        </a>
      </div>

      <div class="navbar-actions">
        <button class="icon-btn">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
            <path d="M10 2a6 6 0 00-6 6v3.586l-.707.707A1 1 0 004 14h12a1 1 0 00.707-1.707L16 11.586V8a6 6 0 00-6-6z"/>
            <path d="M10 18a3 3 0 01-3-3h6a3 3 0 01-3 3z"/>
          </svg>
        </button>
        <div class="user-menu">
          <div class="avatar">
            <span>G</span>
          </div>
        </div>
      </div>
    </div>
  </nav>

  <!-- Main Content -->
  <main class="main-content">
    <!-- Page Header -->
    <div class="page-header">
      <div class="header-left">
        <h1>My Certificates</h1>
        <p class="subtitle">Official digital land certificates issued by the Government of Malawi</p>
      </div>
      <div class="header-right">
        <div class="trust-badge">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="#16a34a">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
          </svg>
          <span>Government Verified</span>
        </div>
      </div>
    </div>

    <!-- Offline Indicator -->
    {#if !isOnline}
      <div class="offline-notice">
        <div class="offline-icon">📱</div>
        <div class="offline-content">
          <h4>You're offline</h4>
          <p>Previously viewed certificates are available. Download works, but sharing and online verification require internet.</p>
        </div>
      </div>
    {/if}

    <!-- Certificates List -->
    <div class="certificates-container">
      {#if certificates.length > 0}
        <div class="certificates-grid">
          {#each certificates as certificate (certificate.id)}
            <div class="certificate-card">
              <!-- Certificate Header -->
              <div class="certificate-header">
                <div class="certificate-id">
                  <div class="id-badge">
                    {getTypeIcon(certificate.type)}
                    <span>{certificate.parcelId}</span>
                  </div>
                  <div class="status-badge" style="background: {getStatusColor(certificate.status)}20; color: {getStatusColor(certificate.status)};">
                    {getStatusText(certificate.status)}
                  </div>
                </div>
                <div class="certificate-type">
                  <span class="type-label">{getTypeText(certificate.type)}</span>
                </div>
              </div>

              <!-- Certificate Details -->
              <div class="certificate-details">
                <div class="detail-row">
                  <div class="detail-icon">📍</div>
                  <div class="detail-content">
                    <div class="detail-label">Location</div>
                    <div class="detail-value">{certificate.location}</div>
                  </div>
                </div>

                <div class="detail-row">
                  <div class="detail-icon">👤</div>
                  <div class="detail-content">
                    <div class="detail-label">Owner</div>
                    <div class="detail-value">{certificate.ownerName}</div>
                  </div>
                </div>

                <div class="detail-row">
                  <div class="detail-icon">📏</div>
                  <div class="detail-content">
                    <div class="detail-label">Size</div>
                    <div class="detail-value">{certificate.size} acres</div>
                  </div>
                </div>

                <div class="detail-row">
                  <div class="detail-icon">📅</div>
                  <div class="detail-content">
                    <div class="detail-label">Issue Date</div>
                    <div class="detail-value">{formatDate(certificate.issueDate)}</div>
                  </div>
                </div>

                <div class="detail-row">
                  <div class="detail-icon">🔐</div>
                  <div class="detail-content">
                    <div class="detail-label">Verification Code</div>
                    <div class="detail-value verification-code">{certificate.verificationCode}</div>
                  </div>
                </div>
              </div>

              <!-- QR Code Section -->
              <div class="qr-section">
                <div class="qr-code">
                  <div class="qr-placeholder">
                    <svg width="80" height="80" viewBox="0 0 80 80" fill="#1e293b">
                      <rect x="10" y="10" width="60" height="60" fill="none" stroke="currentColor" stroke-width="2"/>
                      <rect x="20" y="20" width="15" height="15" fill="currentColor"/>
                      <rect x="45" y="20" width="15" height="15" fill="currentColor"/>
                      <rect x="20" y="45" width="15" height="15" fill="currentColor"/>
                      <rect x="45" y="45" width="15" height="15" fill="currentColor"/>
                      <rect x="37" y="37" width="6" height="6" fill="currentColor"/>
                    </svg>
                  </div>
                  <div class="qr-text">Scan to verify</div>
                </div>
              </div>

              <!-- Certificate Actions -->
              <div class="certificate-actions">
                <button 
                  class="action-btn download" 
                  on:click={() => downloadCertificate(certificate)}
                  disabled={isDownloading}
                >
                  <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clip-rule="evenodd"/>
                  </svg>
                  <span>{isDownloading ? 'Downloading...' : 'Download PDF'}</span>
                </button>

                <button 
                  class="action-btn share" 
                  on:click={() => shareCertificate(certificate)}
                  disabled={!isOnline || isGeneratingShare}
                >
                  <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                    <path d="M15 8a3 3 0 10-2.977-2.63l-4.94 2.47a3 3 0 100 4.319l4.94 2.47a3 3 0 10.895-1.789l-4.94-2.47a3.027 3.027 0 000-.74l4.94-2.47C13.456 7.68 14.19 8 15 8z"/>
                  </svg>
                  <span>{isGeneratingShare ? 'Generating...' : 'Share'}</span>
                </button>

                <button 
                  class="action-btn verify" 
                  on:click={() => verifyOnline(certificate)}
                  disabled={!isOnline}
                >
                  <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
                  </svg>
                  <span>Verify Online</span>
                </button>
              </div>

              <!-- Government Seal -->
              <div class="government-seal">
                <div class="seal-content">
                  <svg width="40" height="40" viewBox="0 0 40 40" fill="#16a34a">
                    <circle cx="20" cy="20" r="18" fill="none" stroke="currentColor" stroke-width="2"/>
                    <path d="M20 8L24 14H22V20H18V14H16L20 8Z" fill="currentColor"/>
                  </svg>
                  <div class="seal-text">
                    <div class="seal-title">Issued by</div>
                    <div class="seal-subtitle">Ministry of Lands, Malawi</div>
                  </div>
                </div>
              </div>
            </div>
          {/each}
        </div>
      {:else}
        <div class="empty-state">
          <div class="empty-icon">
            <svg width="80" height="80" viewBox="0 0 80 80" fill="none">
              <circle cx="40" cy="40" r="40" fill="#f0f4ff"/>
              <rect x="25" y="25" width="30" height="40" rx="2" fill="#667eea" opacity="0.3"/>
              <rect x="30" y="35" width="20" height="2" fill="#667eea" opacity="0.5"/>
              <rect x="30" y="40" width="15" height="2" fill="#667eea" opacity="0.5"/>
              <rect x="30" y="45" width="18" height="2" fill="#667eea" opacity="0.5"/>
              <circle cx="40" cy="55" r="3" fill="#667eea" opacity="0.5"/>
            </svg>
          </div>
          <h3>No Verified Certificates Yet</h3>
          <p>You don't have any verified certificates yet.</p>
          <p class="empty-subtitle">Once your land is approved, your official digital certificates will appear here.</p>
          <div class="empty-actions">
            <button class="btn btn-primary" on:click={() => goto('/register-land')}>
              Register Land
            </button>
            <button class="btn btn-secondary" on:click={() => goto('/dashboard')}>
              View Dashboard
            </button>
          </div>
        </div>
      {/if}
    </div>

    <!-- Trust & Security Section -->
    <div class="trust-section">
      <div class="trust-card">
        <div class="trust-header">
          <h3>🔐 Why Your Certificates Are Trusted</h3>
        </div>
        <div class="trust-content">
          <div class="trust-grid">
            <div class="trust-item">
              <div class="trust-icon">🏛️</div>
              <div class="trust-text">
                <h4>Government Issued</h4>
                <p>Every certificate is digitally signed by the Ministry of Lands, Malawi</p>
              </div>
            </div>
            <div class="trust-item">
              <div class="trust-icon">🔗</div>
              <div class="trust-text">
                <h4>Tamper-Proof</h4>
                <p>QR codes and verification links connect to immutable public records</p>
              </div>
            </div>
            <div class="trust-item">
              <div class="trust-icon">🔄</div>
              <div class="trust-text">
                <h4>Always Current</h4>
                <p>Certificates automatically update if land is sold, transferred, or revoked</p>
              </div>
            </div>
            <div class="trust-item">
              <div class="trust-icon">🌍</div>
              <div class="trust-text">
                <h4>Public Verification</h4>
                <p>Anyone can verify certificate authenticity online or by scanning QR codes</p>
              </div>
            </div>
          </div>
        </div>
      </div>
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
    background: #f8fafc;
    color: #1e293b;
    line-height: 1.5;
  }

  .certificates-page {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  /* Navbar - Same as dashboard */
  .navbar {
    background: white;
    border-bottom: 1px solid #e2e8f0;
    position: sticky;
    top: 0;
    z-index: 100;
    box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
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
    color: #0f172a;
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
    color: #64748b;
    font-weight: 500;
    font-size: 0.9375rem;
    transition: all 0.2s;
    white-space: nowrap;
  }

  .nav-link:hover {
    background: #f1f5f9;
    color: #334155;
  }

  .nav-link.active {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
    background: #f8fafc;
    color: #64748b;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
  }

  .icon-btn:hover {
    background: #f1f5f9;
    color: #334155;
  }

  .avatar {
    width: 40px;
    height: 40px;
    border-radius: 10px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
    width: 100%;
    flex: 1;
  }

  /* Page Header */
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
    flex-wrap: wrap;
    gap: 1rem;
  }

  .header-left h1 {
    font-size: 1.875rem;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 0.25rem;
  }

  .subtitle {
    color: #64748b;
    font-size: 0.9375rem;
  }

  .trust-badge {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    background: #dcfce7;
    color: #16a34a;
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.875rem;
  }

  /* Offline Notice */
  .offline-notice {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem 1.5rem;
    background: #fef3c7;
    border: 1px solid #fbbf24;
    border-radius: 8px;
    margin-bottom: 2rem;
  }

  .offline-icon {
    font-size: 1.5rem;
  }

  .offline-content h4 {
    font-weight: 600;
    color: #92400e;
    margin-bottom: 0.25rem;
  }

  .offline-content p {
    color: #78350f;
    font-size: 0.875rem;
  }

  /* Certificates Container */
  .certificates-container {
    margin-bottom: 3rem;
  }

  .certificates-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
    gap: 2rem;
  }

  /* Certificate Card */
  .certificate-card {
    background: white;
    border-radius: 16px;
    border: 1px solid #e2e8f0;
    overflow: hidden;
    transition: all 0.3s;
    position: relative;
  }

  .certificate-card:hover {
    border-color: #cbd5e1;
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
    transform: translateY(-2px);
  }

  /* Certificate Header */
  .certificate-header {
    padding: 1.5rem;
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    border-bottom: 1px solid #e2e8f0;
  }

  .certificate-id {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.75rem;
  }

  .id-badge {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 1.125rem;
    font-weight: 700;
    color: #0f172a;
  }

  .status-badge {
    padding: 0.25rem 0.75rem;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
  }

  .certificate-type {
    text-align: right;
  }

  .type-label {
    font-size: 0.875rem;
    color: #64748b;
    font-weight: 500;
  }

  /* Certificate Details */
  .certificate-details {
    padding: 1.5rem;
  }

  .detail-row {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1rem;
  }

  .detail-row:last-child {
    margin-bottom: 0;
  }

  .detail-icon {
    width: 32px;
    height: 32px;
    border-radius: 6px;
    background: #f8fafc;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1rem;
    flex-shrink: 0;
  }

  .detail-content {
    flex: 1;
  }

  .detail-label {
    font-size: 0.75rem;
    color: #64748b;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.3px;
    margin-bottom: 0.25rem;
  }

  .detail-value {
    font-size: 0.9375rem;
    color: #0f172a;
    font-weight: 500;
  }

  .verification-code {
    font-family: 'Courier New', monospace;
    font-size: 0.875rem;
    background: #f1f5f9;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
  }

  /* QR Code Section */
  .qr-section {
    padding: 1.5rem;
    background: #f8fafc;
    border-top: 1px solid #e2e8f0;
    display: flex;
    justify-content: center;
  }

  .qr-code {
    text-align: center;
  }

  .qr-placeholder {
    margin-bottom: 0.5rem;
  }

  .qr-text {
    font-size: 0.75rem;
    color: #64748b;
    font-weight: 500;
  }

  /* Certificate Actions */
  .certificate-actions {
    padding: 1.5rem;
    display: flex;
    gap: 1rem;
    border-top: 1px solid #e2e8f0;
  }

  .action-btn {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
    border-radius: 8px;
    border: none;
    font-weight: 600;
    font-size: 0.875rem;
    cursor: pointer;
    transition: all 0.2s;
  }

  .action-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .action-btn.download {
    background: linear-gradient(135deg, #1a472a 0%, #2d5a3d 100%);
    color: white;
  }

  .action-btn.download:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(45, 90, 61, 0.4);
  }

  .action-btn.share {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
  }

  .action-btn.share:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  }

  .action-btn.verify {
    background: white;
    color: #667eea;
    border: 1px solid #e2e8f0;
  }

  .action-btn.verify:hover:not(:disabled) {
    background: #f8fafc;
  }

  /* Government Seal */
  .government-seal {
    position: absolute;
    top: 1rem;
    right: 1rem;
    opacity: 0.1;
  }

  .seal-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.25rem;
  }

  .seal-title {
    font-size: 0.625rem;
    font-weight: 600;
    color: #16a34a;
  }

  .seal-subtitle {
    font-size: 0.5rem;
    color: #16a34a;
  }

  /* Empty State */
  .empty-state {
    text-align: center;
    padding: 4rem 2rem;
    background: white;
    border-radius: 16px;
    border: 1px solid #e2e8f0;
  }

  .empty-icon {
    margin-bottom: 2rem;
  }

  .empty-state h3 {
    font-size: 1.5rem;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 1rem;
  }

  .empty-state p {
    color: #64748b;
    margin-bottom: 0.5rem;
  }

  .empty-subtitle {
    color: #94a3b8;
    font-size: 0.875rem;
    margin-bottom: 2rem;
  }

  .empty-actions {
    display: flex;
    gap: 1rem;
    justify-content: center;
  }

  /* Trust Section */
  .trust-section {
    margin-top: 3rem;
  }

  .trust-card {
    background: white;
    border-radius: 16px;
    border: 1px solid #e2e8f0;
    overflow: hidden;
  }

  .trust-header {
    padding: 1.5rem;
    background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
    border-bottom: 1px solid #e2e8f0;
  }

  .trust-header h3 {
    font-size: 1.25rem;
    font-weight: 700;
    color: #0f172a;
  }

  .trust-content {
    padding: 1.5rem;
  }

  .trust-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1.5rem;
  }

  .trust-item {
    display: flex;
    gap: 1rem;
  }

  .trust-icon {
    width: 48px;
    height: 48px;
    border-radius: 8px;
    background: #f8fafc;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5rem;
    flex-shrink: 0;
  }

  .trust-text h4 {
    font-size: 1rem;
    font-weight: 600;
    color: #0f172a;
    margin-bottom: 0.25rem;
  }

  .trust-text p {
    font-size: 0.875rem;
    color: #64748b;
    line-height: 1.5;
  }

  /* Buttons */
  .btn {
    padding: 0.625rem 1.25rem;
    border-radius: 8px;
    border: none;
    font-weight: 600;
    font-size: 0.9375rem;
    cursor: pointer;
    transition: all 0.2s;
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
  }

  .btn-primary {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
  }

  .btn-primary:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  }

  .btn-secondary {
    background: white;
    color: #667eea;
    border: 1px solid #e2e8f0;
  }

  .btn-secondary:hover {
    background: #f8fafc;
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

    .certificates-grid {
      grid-template-columns: 1fr;
      gap: 1.5rem;
    }

    .certificate-actions {
      flex-direction: column;
    }

    .trust-grid {
      grid-template-columns: 1fr;
    }

    .empty-actions {
      flex-direction: column;
    }

    .empty-actions .btn {
      width: 100%;
      justify-content: center;
    }
  }
</style>
