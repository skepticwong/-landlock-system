<script>
  import { goto } from '$app/navigation';
  import { browser } from '$app/environment';
  
  let phone = '';
  let password = '';
  let error = '';
  let isLoading = false;

  async function handleLogin() {
    error = '';
    
    if (!phone || !password) {
      error = 'Please enter both phone number and password';
      return;
    }

    isLoading = true;

    try {
      // TODO: Replace with your actual API endpoint
      const response = await fetch('http://localhost:5000/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone, password })
      });

      const data = await response.json();

      if (response.ok && data.token) {
        // Save token to localStorage
        if (browser) {
          localStorage.setItem('token', data.token);
          localStorage.setItem('user', JSON.stringify(data.user || { phone }));
        }
        
        // Redirect to dashboard
        goto('/dashboard');
      } else {
        error = data.error || 'Login failed. Please check your credentials.';
      }
    } catch (err) {
      error = 'Network error. Please try again.';
      console.error('Login error:', err);
    } finally {
      isLoading = false;
    }
  }

  // For demo purposes - remove in production
  function demoLogin() {
    if (browser) {
      localStorage.setItem('token', 'demo-token-12345');
      localStorage.setItem('user', JSON.stringify({ phone: '265888123456', name: 'Demo User' }));
    }
    goto('/dashboard');
  }
</script>

<div class="login-container">
  <div class="login-card">
    <div class="logo-section">
      <div class="logo-circle">🌍</div>
      <h1>LandLock</h1>
      <p>Secure Land Registry for Malawi</p>
    </div>

    <form on:submit|preventDefault={handleLogin}>
      <div class="form-group">
        <label for="phone">Phone Number</label>
        <input
          id="phone"
          type="tel"
          placeholder="265888123456"
          bind:value={phone}
          disabled={isLoading}
        />
      </div>

      <div class="form-group">
        <label for="password">Password</label>
        <input
          id="password"
          type="password"
          placeholder="Enter your password"
          bind:value={password}
          disabled={isLoading}
        />
      </div>

      {#if error}
        <div class="error-message">
          {error}
        </div>
      {/if}

      <button type="submit" class="btn-login" disabled={isLoading}>
        {#if isLoading}
          Logging in...
        {:else}
          Login
        {/if}
      </button>

      <!-- Demo button - remove in production -->
      <button type="button" class="btn-demo" on:click={demoLogin}>
        Demo Login (Skip Authentication)
      </button>
    </form>

    <div class="footer-links">
      <a href="/register" on:click|preventDefault={() => goto('/register')}>
        Don't have an account? <span class="register-link">Register</span>
      </a>
    </div>
  </div>
</div>

<style>
  .login-container {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(to bottom, #f0fdf4, #e6f7ee);
    padding: 1rem;
  }

  .login-card {
    background: white;
    border-radius: 16px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.1);
    padding: 2rem;
    width: 100%;
    max-width: 420px;
  }

  .logo-section {
    text-align: center;
    margin-bottom: 2rem;
  }

  .logo-circle {
    width: 4rem;
    height: 4rem;
    border-radius: 1rem;
    background: linear-gradient(135deg, #0d9488, #0b7a71);
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 2rem;
    box-shadow: 0 4px 12px rgba(13,148,136,0.25);
    margin-bottom: 1rem;
  }

  h1 {
    font-size: 2rem;
    font-weight: 700;
    background: linear-gradient(90deg, #0d9488, #0b7a71);
    background-clip: text;
    -webkit-background-clip: text;
    color: transparent;
    margin: 0.5rem 0;
  }

  .logo-section p {
    color: #64748b;
    font-weight: 600;
  }

  .form-group {
    margin-bottom: 1.25rem;
  }

  label {
    display: block;
    font-weight: 600;
    font-size: 0.875rem;
    margin-bottom: 0.5rem;
    color: #334155;
  }

  input {
    width: 100%;
    padding: 0.875rem 1rem;
    border: 2px solid #e2e8f0;
    border-radius: 12px;
    font-size: 1rem;
    background: #f8fafc;
    transition: border-color 0.2s;
  }

  input:focus {
    outline: none;
    border-color: #0d9488;
    box-shadow: 0 0 0 3px rgba(13,148,136,0.15);
  }

  input:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .error-message {
    background: #fee2e2;
    color: #991b1b;
    padding: 0.75rem;
    border-radius: 8px;
    font-size: 0.875rem;
    margin-bottom: 1rem;
    border: 1px solid #fecaca;
  }

  .btn-login {
    width: 100%;
    padding: 1rem;
    background: linear-gradient(135deg, #0d9488, #0b7a71);
    color: white;
    border: none;
    border-radius: 12px;
    font-weight: 600;
    font-size: 1rem;
    cursor: pointer;
    box-shadow: 0 4px 10px rgba(13,148,136,0.3);
    transition: all 0.2s;
  }

  .btn-login:hover:not(:disabled) {
    background: linear-gradient(135deg, #0b7a71, #09615b);
    transform: translateY(-2px);
    box-shadow: 0 6px 14px rgba(13,148,136,0.4);
  }

  .btn-login:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
  }

  .btn-demo {
    width: 100%;
    padding: 0.75rem;
    background: #f1f5f9;
    color: #475569;
    border: 2px solid #e2e8f0;
    border-radius: 12px;
    font-weight: 600;
    font-size: 0.9rem;
    cursor: pointer;
    margin-top: 0.75rem;
    transition: all 0.2s;
  }

  .btn-demo:hover {
    background: #e2e8f0;
  }

  .footer-links {
    text-align: center;
    margin-top: 1.5rem;
  }

  .footer-links a {
    color: #4b5563;
    text-decoration: none;
    font-weight: 500;
    font-size: 0.9rem;
    transition: color 0.2s ease;
  }

  .footer-links a:hover {
    color: #10b981;
  }

  .register-link {
    color: #10b981;
    font-weight: 600;
    margin-left: 0.25rem;
  }
  
  .footer-links a:hover .register-link {
    text-decoration: underline;
  }
</style>