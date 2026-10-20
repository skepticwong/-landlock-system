<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { browser } from '$app/environment';
  import { Home, FileText, Smartphone, MapPin, User, Ruler, Calendar, Lock, Building, Link, RefreshCw, Globe, Download, Share2, Check, Shield } from 'lucide-svelte';
  import Navbar from '$lib/components/Navbar.svelte';

  // Real data from backend
  let certificates = [];
  let isOnline = true;
  let selectedCertificate = null;
  let shareLink = '';
  let isGeneratingShare = false;
  let isDownloading = false;
  let currentUser = null;

  async function fetchCurrentUser() {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:5000/api/user/me', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        currentUser = await response.json();
      }
    } catch (error) {
      console.error('Failed to fetch user:', error);
    }
  }

  async function fetchCertificates() {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:5000/api/certificates', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        certificates = data;
      }
    } catch (error) {
      console.error('Failed to fetch certificates:', error);
    }
  }

  onMount(() => {
    if (!browser) return;
    
    isOnline = navigator.onLine;

    // Check authentication
    if (!localStorage.getItem('token')) {
      goto('/login');
      return;
    }

    // Listen for online/offline changes
    window.addEventListener('online', () => isOnline = true);
    window.addEventListener('offline', () => isOnline = false);

    // Fetch real data
    fetchCurrentUser();
    fetchCertificates();
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
      content: `Official Land Certificate\n\nParcel ID: ${certificate.parcelId}\nLocation: ${certificate.location}\nOwner: ${certificate.ownerName}\nSize: ${certificate.size} m²\nIssue Date: ${certificate.issueDate}\nType: ${certificate.type}\nVerification Code: ${certificate.verificationCode}\n\nIssued by Ministry of Lands, Malawi`
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

  function getTypeIcon(type: string): any {
    return type === 'ownership' ? Home : FileText;
  }

  function getTypeText(type: string): string {
    return type === 'ownership' ? 'Ownership' : 'Lease';
  }

  function handleLogout() {
    if (browser) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      goto('/login');
    }
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
  <Navbar userType="citizen" activeLink="/certificates" userName={currentUser?.full_name || 'User'} />

  <!-- Main Content -->
  <main class="main-content">
    <!-- Page Header -->
    <div class="page-header">
      <div class="header-left">
        <h1>Official Land Certificates</h1>
        <p class="subtitle">Verifiable digital deeds of title registered with the Ministry of Lands, Malawi</p>
      </div>
      <div class="header-right">
        <div class="trust-badge">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="var(--color-primary)">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
          </svg>
          <span>Government Verified</span>
        </div>
      </div>
    </div>

    <!-- Offline Indicator -->
    {#if !isOnline}
      <div class="offline-notice">
        <div class="offline-icon"><Smartphone class="w-6 h-6 text-amber-700" /></div>
        <div class="offline-content">
          <h4>Working Offline</h4>
          <p>Cached certificates are accessible. Standard PDF download is supported, but secure sharing and real-time online validation are paused.</p>
        </div>
      </div>
    {/if}

    <!-- Certificates List -->
    <div class="certificates-container">
      {#if certificates.length > 0}
        <div class="certificates-grid">
          {#each certificates as certificate (certificate.id)}
            <div class="certificate-card">
              <div class="certificate-frame">
                <!-- Certificate Emblem / Crest -->
                <div class="cert-crest">
                  <svg width="48" height="48" viewBox="0 0 40 40" fill="none">
                    <circle cx="20" cy="20" r="18" stroke="var(--color-primary)" stroke-width="2"/>
                    <circle cx="20" cy="20" r="15" stroke="#FFC107" stroke-width="1.5" stroke-dasharray="2,2"/>
                    <path d="M20 10L26 16H22V24H18V16H14L20 10Z" fill="var(--color-primary)"/>
                    <path d="M12 27H28" stroke="#FFC107" stroke-width="2"/>
                  </svg>
                </div>
                
                <div class="cert-gov-text">
                  <h2 class="cert-gov-title">REPUBLIC OF MALAWI</h2>
                  <h3 class="cert-gov-dept">MINISTRY OF LANDS</h3>
                </div>

                <div class="cert-title-container">
                  <h1 class="cert-main-title">Certificate of Customary Land Title</h1>
                  <p class="cert-sub-title">ISSUED UNDER THE LAND ACT AND REGISTERED DIGITAL DEEDS</p>
                </div>

                <div class="cert-divider"></div>

                <!-- Legal Certificate Body -->
                <div class="cert-statement">
                  This is to officially certify and record that <span class="highlight-text">{certificate.ownerName}</span> has been duly registered as the rightful and absolute proprietor of the parcel of land described hereunder:
                </div>

                <div class="cert-grid">
                  <div class="cert-field">
                    <span class="cert-field-label">Parcel ID (Ref)</span>
                    <span class="cert-field-value">{certificate.parcelId}</span>
                  </div>
                  <div class="cert-field">
                    <span class="cert-field-label">Geographical Location</span>
                    <span class="cert-field-value">{certificate.location}</span>
                  </div>
                  <div class="cert-field">
                    <span class="cert-field-label">Registered Size</span>
                    <span class="cert-field-value">{certificate.size || '20m x 20m'}</span>
                  </div>
                  <div class="cert-field">
                    <span class="cert-field-label">Date of Registration</span>
                    <span class="cert-field-value">{formatDate(certificate.issueDate)}</span>
                  </div>
                </div>

                <div class="cert-divider"></div>

                <!-- Footer & Validation -->
                <div class="cert-footer">
                  <div class="cert-security-info">
                    <div class="cert-field">
                      <span class="cert-field-label">Verification Code</span>
                      <span class="cert-field-value code-font">{certificate.verificationCode}</span>
                    </div>
                    <div class="cert-signatures">
                      <div class="signature-box">
                        <div class="signature-line"></div>
                        <span class="signature-label">Registrar of Lands</span>
                      </div>
                    </div>
                  </div>
                  
                  <div class="cert-qr-box">
                    <div class="qr-placeholder">
                      <svg width="60" height="60" viewBox="0 0 80 80" fill="var(--text-primary)">
                        <rect x="10" y="10" width="60" height="60" fill="none" stroke="currentColor" stroke-width="2"/>
                        <rect x="20" y="20" width="15" height="15" fill="currentColor"/>
                        <rect x="45" y="20" width="15" height="15" fill="currentColor"/>
                        <rect x="20" y="45" width="15" height="15" fill="currentColor"/>
                        <rect x="45" y="45" width="15" height="15" fill="currentColor"/>
                        <rect x="37" y="37" width="6" height="6" fill="currentColor"/>
                      </svg>
                    </div>
                    <span class="qr-caption">Scan to Verify</span>
                  </div>
                </div>

                <!-- Watermark Seal Background -->
                <div class="watermark-seal">
                  <svg width="180" height="180" viewBox="0 0 40 40" fill="none" opacity="0.03">
                    <circle cx="20" cy="20" r="18" stroke="var(--color-primary)" stroke-width="2"/>
                    <path d="M20 8L24 14H22V20H18V14H16L20 8Z" fill="var(--color-primary)"/>
                  </svg>
                </div>
              </div>

              <!-- Action Toolbar -->
              <div class="certificate-actions">
                <button 
                  class="action-btn download" 
                  on:click={() => downloadCertificate(certificate)}
                  disabled={isDownloading}
                >
                  <svg width="18" height="18" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clip-rule="evenodd"/>
                  </svg>
                  <span>{isDownloading ? 'Downloading...' : 'Download PDF'}</span>
                </button>

                <button 
                  class="action-btn share" 
                  on:click={() => shareCertificate(certificate)}
                  disabled={!isOnline || isGeneratingShare}
                >
                  <svg width="18" height="18" viewBox="0 0 20 20" fill="currentColor">
                    <path d="M15 8a3 3 0 10-2.977-2.63l-4.94 2.47a3 3 0 100 4.319l4.94 2.47a3 3 0 10.895-1.789l-4.94-2.47a3.027 3.027 0 000-.74l4.94-2.47C13.456 7.68 14.19 8 15 8z"/>
                  </svg>
                  <span>{isGeneratingShare ? 'Generating...' : 'Share Deed'}</span>
                </button>

                <button 
                  class="action-btn verify" 
                  on:click={() => verifyOnline(certificate)}
                  disabled={!isOnline}
                >
                  <svg width="18" height="18" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
                  </svg>
                  <span>Verify Registry</span>
                </button>
              </div>
            </div>
          {/each}
        </div>
      {:else}
        <div class="empty-state">
          <div class="empty-icon">
            <svg width="80" height="80" viewBox="0 0 80 80" fill="none" class="mx-auto">
              <circle cx="40" cy="40" r="40" fill="#f8fafc"/>
              <rect x="25" y="25" width="30" height="40" rx="2" fill="var(--color-primary)" opacity="0.2"/>
              <rect x="30" y="35" width="20" height="2" fill="var(--color-primary)" opacity="0.4"/>
              <rect x="30" y="40" width="15" height="2" fill="var(--color-primary)" opacity="0.4"/>
              <rect x="30" y="45" width="18" height="2" fill="var(--color-primary)" opacity="0.4"/>
              <circle cx="40" cy="55" r="3" fill="var(--color-primary)" opacity="0.4"/>
            </svg>
          </div>
          <h3>No Registered Certificates</h3>
          <p>Once your land claims have been officially reviewed and surveyed, your official digital certificates will be issued here.</p>
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
          <h3><Shield class="w-5 h-5 inline text-emerald-800" /> Digital Deed Security Infrastructure</h3>
        </div>
        <div class="trust-content">
          <div class="trust-grid">
            <div class="trust-item">
              <div class="trust-icon"><Building class="w-6 h-6 text-emerald-800" /></div>
              <div class="trust-text">
                <h4>Statutory Legitimacy</h4>
                <p>All certificates represent legally binding deeds approved and signed by the Ministry of Lands, Malawi.</p>
              </div>
            </div>
            <div class="trust-item">
              <div class="trust-icon"><Link class="w-6 h-6 text-emerald-800" /></div>
              <div class="trust-text">
                <h4>Immutable Ledger</h4>
                <p>Secured with cryptographic hashing, rendering every land parcel record tamper-proof and fully audit-trail complete.</p>
              </div>
            </div>
            <div class="trust-item">
              <div class="trust-icon"><RefreshCw class="w-6 h-6 text-emerald-800" /></div>
              <div class="trust-text">
                <h4>Real-Time Synchronization</h4>
                <p>Any updates to boundaries, transfers of ownership, or leases propagate instantly to revoke outdated certificate copies.</p>
              </div>
            </div>
            <div class="trust-item">
              <div class="trust-icon"><Globe class="w-6 h-6 text-emerald-800" /></div>
              <div class="trust-text">
                <h4>Instant Public Auditing</h4>
                <p>Third-party agencies or financial institutions can securely audit certificate status in real time via secure verification URLs.</p>
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
    background: var(--bg-primary);
    color: var(--text-primary);
    line-height: 1.5;
  }

  .certificates-page {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
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

  .dropdown-menu {
    position: absolute;
    top: 100%;
    right: 0;
    margin-top: 0.5rem;
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    min-width: 150px;
    z-index: 1000;
  }

  .dropdown-item {
    display: block;
    width: 100%;
    text-align: left;
    padding: 0.75rem 1rem;
    border: none;
    background: none;
    cursor: pointer;
    color: #ef4444;
    font-weight: 600;
  }

  .dropdown-item:hover {
    background: #fef2f2;
    border-radius: 8px;
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
    color: var(--text-primary);
    margin-bottom: 0.25rem;
  }

  .subtitle {
    color: var(--color-disabled);
    font-size: 0.9375rem;
  }

  .trust-badge {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    background: #e6f2ec;
    color: var(--color-primary);
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.875rem;
    border: 1px solid rgba(0, 122, 61, 0.15);
  }

  /* Offline Notice */
  .offline-notice {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem 1.5rem;
    background: #fffdf5;
    border: 1px solid var(--color-warning);
    border-radius: 8px;
    margin-bottom: 2rem;
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
    grid-template-columns: repeat(auto-fit, minmax(420px, 1fr));
    gap: 2.5rem;
  }

  /* Certificate Card */
  .certificate-card {
    background: white;
    border-radius: 12px;
    border: 1px solid var(--color-border);
    overflow: hidden;
    transition: all 0.3s ease;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
  }

  .certificate-card:hover {
    border-color: #cbd5e1;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.08);
    transform: translateY(-2px);
  }

  /* Elegant Certificate Frame */
  .certificate-frame {
    border: 3px double var(--color-primary);
    padding: 1.75rem;
    margin: 1rem;
    border-radius: 6px;
    background: #fdfcfb; /* Premium linen-white texture look */
    position: relative;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
    box-shadow: inset 0 0 0 1px rgba(255, 193, 7, 0.2);
  }

  .cert-crest {
    display: flex;
    justify-content: center;
    margin-bottom: 0.25rem;
    position: relative;
    z-index: 2;
  }

  .cert-gov-text {
    text-align: center;
    position: relative;
    z-index: 2;
  }

  .cert-gov-title {
    font-family: 'Georgia', serif;
    font-size: 0.95rem;
    letter-spacing: 2px;
    color: var(--color-primary);
    font-weight: 700;
    margin-bottom: 0.15rem;
  }

  .cert-gov-dept {
    font-family: 'Georgia', serif;
    font-size: 0.75rem;
    letter-spacing: 1px;
    color: var(--text-primary);
    font-weight: 600;
  }

  .cert-title-container {
    text-align: center;
    margin: 0.5rem 0;
    position: relative;
    z-index: 2;
  }

  .cert-main-title {
    font-family: 'Georgia', serif;
    font-size: 1.25rem;
    font-weight: 700;
    color: #111827;
    margin-bottom: 0.25rem;
  }

  .cert-sub-title {
    font-size: 0.625rem;
    letter-spacing: 1.5px;
    color: var(--color-disabled);
    font-weight: 700;
    text-transform: uppercase;
  }

  .cert-divider {
    height: 1px;
    background: linear-gradient(to right, transparent, var(--color-border), transparent);
    margin: 0.25rem 0;
    position: relative;
    z-index: 2;
  }

  .cert-statement {
    text-align: center;
    font-family: 'Georgia', serif;
    font-size: 0.85rem;
    line-height: 1.6;
    color: #374151;
    font-style: italic;
    margin-bottom: 0.5rem;
    position: relative;
    z-index: 2;
  }

  .highlight-text {
    font-weight: 700;
    color: var(--text-primary);
    font-style: normal;
    text-decoration: underline;
    text-underline-offset: 3px;
    text-decoration-color: #FFC107;
  }

  .cert-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
    background: rgba(248, 249, 250, 0.7);
    padding: 1rem;
    border-radius: 8px;
    border: 1px solid rgba(222, 226, 230, 0.5);
    position: relative;
    z-index: 2;
  }

  .cert-field {
    display: flex;
    flex-direction: column;
  }

  .cert-field-label {
    font-size: 0.65rem;
    text-transform: uppercase;
    color: var(--color-disabled);
    font-weight: 600;
    letter-spacing: 0.5px;
    margin-bottom: 0.15rem;
  }

  .cert-field-value {
    font-size: 0.875rem;
    color: var(--text-primary);
    font-weight: 700;
  }

  .code-font {
    font-family: 'Courier New', monospace;
    font-size: 0.8rem;
    background: #e9ecef;
    padding: 0.15rem 0.4rem;
    border-radius: 4px;
    width: fit-content;
    border: 1px solid #dee2e6;
  }

  .cert-footer {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    margin-top: 0.5rem;
    position: relative;
    z-index: 2;
  }

  .cert-security-info {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    flex: 1;
  }

  .cert-signatures {
    display: flex;
    margin-top: 0.5rem;
  }

  .signature-box {
    display: flex;
    flex-direction: column;
    width: 140px;
  }

  .signature-line {
    height: 1px;
    background: var(--text-primary);
    margin-bottom: 0.25rem;
    position: relative;
    width: 100%;
  }

  .signature-line::before {
    content: 'M. Banda';
    font-family: 'Georgia', serif;
    font-style: italic;
    font-size: 0.9rem;
    position: absolute;
    bottom: 2px;
    left: 15px;
    color: var(--color-primary-hover);
    font-weight: 600;
  }

  .signature-label {
    font-size: 0.6rem;
    text-transform: uppercase;
    color: var(--color-disabled);
    font-weight: 700;
    letter-spacing: 0.5px;
  }

  .cert-qr-box {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.25rem;
  }

  .qr-placeholder {
    padding: 0.25rem;
    background: white;
    border: 1px solid var(--color-border);
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .qr-caption {
    font-size: 0.575rem;
    text-transform: uppercase;
    color: var(--color-disabled);
    font-weight: 700;
    letter-spacing: 0.5px;
  }

  /* Watermark Government Seal Background */
  .watermark-seal {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    pointer-events: none;
    z-index: 1;
  }

  /* Action Buttons Toolbar */
  .certificate-actions {
    padding: 1.25rem;
    background: #f8fafc;
    border-top: 1px solid var(--color-border);
    display: flex;
    gap: 0.75rem;
  }

  .action-btn {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.4rem;
    padding: 0.625rem 0.75rem;
    border-radius: 6px;
    border: none;
    font-weight: 600;
    font-size: 0.8125rem;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .action-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .action-btn.download {
    background: var(--color-primary);
    color: white;
  }

  .action-btn.download:hover:not(:disabled) {
    background: var(--color-primary-hover);
    transform: translateY(-1px);
    box-shadow: 0 4px 10px rgba(0, 122, 61, 0.2);
  }

  .action-btn.share {
    background: var(--color-disabled);
    color: white;
  }

  .action-btn.share:hover:not(:disabled) {
    background: #5a6268;
    transform: translateY(-1px);
    box-shadow: 0 4px 10px rgba(0,0,0,0.1);
  }

  .action-btn.verify {
    background: white;
    color: var(--color-primary);
    border: 1px solid var(--color-border);
  }

  .action-btn.verify:hover:not(:disabled) {
    background: #f1f5f9;
    border-color: var(--color-primary);
  }

  /* Empty State */
  .empty-state {
    text-align: center;
    padding: 4rem 2rem;
    background: white;
    border-radius: 12px;
    border: 1px solid var(--color-border);
  }

  .empty-icon {
    margin-bottom: 1.5rem;
  }

  .empty-state h3 {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 0.75rem;
  }

  .empty-state p {
    color: var(--color-disabled);
    max-width: 500px;
    margin: 0 auto 1.5rem auto;
    font-size: 0.9375rem;
  }

  .empty-actions {
    display: flex;
    gap: 1rem;
    justify-content: center;
  }

  /* Trust & Security Section */
  .trust-section {
    margin-top: 3.5rem;
  }

  .trust-card {
    background: white;
    border-radius: 12px;
    border: 1px solid var(--color-border);
    overflow: hidden;
  }

  .trust-header {
    padding: 1.25rem 1.5rem;
    background: #f8fafc;
    border-bottom: 1px solid var(--color-border);
  }

  .trust-header h3 {
    font-size: 1.125rem;
    font-weight: 700;
    color: var(--text-primary);
    display: flex;
    align-items: center;
  }

  .trust-content {
    padding: 1.75rem;
  }

  .trust-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 2rem;
  }

  .trust-item {
    display: flex;
    gap: 1rem;
  }

  .trust-icon {
    width: 44px;
    height: 44px;
    border-radius: 8px;
    background: #f8fafc;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 1px solid var(--color-border);
    flex-shrink: 0;
  }

  .trust-text h4 {
    font-size: 0.95rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 0.25rem;
  }

  .trust-text p {
    font-size: 0.85rem;
    color: var(--color-disabled);
    line-height: 1.45;
  }

  /* Global buttons */
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

  .btn-secondary {
    background: white;
    color: var(--color-primary);
    border: 1px solid var(--color-border);
  }

  .btn-secondary:hover {
    background: #f8fafc;
    border-color: var(--color-primary);
  }

  /* Responsive styling overrides */
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

    .certificate-frame {
      padding: 1.25rem;
      margin: 0.5rem;
    }

    .cert-grid {
      grid-template-columns: 1fr;
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
