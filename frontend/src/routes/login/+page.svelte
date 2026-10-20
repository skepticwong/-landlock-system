<script>

  import { goto } from '$app/navigation';

  import { browser } from '$app/environment';

  import { Globe, Eye, EyeOff } from 'lucide-svelte';

  

  let phone = '';

  let password = '';

  let showPassword = false;

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

      // Corrected API endpoint with /api/ prefix

      const response = await fetch('/api/auth/login', {

        method: 'POST',

        headers: { 'Content-Type': 'application/json' },

        body: JSON.stringify({ phone, password }) // password here contains the PIN from the UI

      });



      const data = await response.json();



      if (response.ok && data.access_token) {

        // Save token to localStorage

        if (browser) {

          localStorage.setItem('token', data.access_token);

          localStorage.setItem('user', JSON.stringify(data.user || { phone }));

        }

        

        // Redirect based on role
        const userRole = data.user?.role || 'citizen';
        
        if (data.user && data.user.is_superuser) {
          goto('/dashboard/official');
        } else if (userRole === 'chief') {
          goto('/dashboard/chief');
        } else if (userRole === 'official') {
          goto('/dashboard/official');
        } else {
          goto('/dashboard');
        }

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





</script>



<div class="login-container">

  <div class="login-card">

    <div class="logo-section">
      <div class="logo-circle">
        <img src="/images/Coat_of_arms_of_Malawi.svg" alt="LandLock Logo" class="logo-image" />
      </div>
      <h1>LandLock</h1>

      <p>Secure Land Registry for Malawi</p>

    </div>



    <form on:submit|preventDefault={handleLogin}>

      <div class="form-group">

        <label for="phone">Phone Number</label>

        <input

          id="phone"

          type="tel"

          placeholder="0888123456"

          bind:value={phone}

          disabled={isLoading}

        />

      </div>



      <div class="form-group">

        <label for="password">Password</label>

        <div class="password-container">

          <input

            id="password"

            type={showPassword ? "text" : "password"}

            placeholder="Enter your password"

            bind:value={password}

            disabled={isLoading}

          />

          <button 

            type="button" 

            class="toggle-password" 

            on:click={() => showPassword = !showPassword}

            disabled={isLoading}

            aria-label={showPassword ? "Hide password" : "Show password"}

          >

            {#if showPassword}

              <EyeOff class="w-5 h-5" />

            {:else}

              <Eye class="w-5 h-5" />

            {/if}

          </button>

        </div>

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





    </form>



    <div class="footer-links">

      <a href="/register" on:click|preventDefault={() => goto('/register')}>

        Don't have an account? <span class="register-link">Sign Up</span>

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

    background: #F8F9FA;

    padding: 1rem;

  }



  .login-card {

    background: white;

    border-radius: 12px;

    box-shadow: 0 4px 16px rgba(0,0,0,0.08);

    border: 1px solid #DEE2E6;

    padding: 2.5rem 2rem;

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
    border-radius: 12px;
    background: #ffffff !important;
    color: white;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 2rem;
    box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    margin-bottom: 1rem;
    padding: 0.5rem;
  }

  .logo-image {
    width: 100%;
    height: 100%;
    object-fit: contain;
  }



  h1 {

    font-size: 1.75rem;

    font-weight: 700;

    color: #007A3D;

    margin: 0.5rem 0;

  }



  .logo-section p {

    color: #495057;

    font-weight: 600;

    font-size: 0.95rem;

  }



  .form-group {

    margin-bottom: 1.25rem;

  }



  label {

    display: block;

    font-weight: 600;

    font-size: 0.875rem;

    margin-bottom: 0.5rem;

    color: #212529;

  }



  input {

    width: 100%;

    padding: 0.75rem 1rem;

    border: 2px solid #DEE2E6;

    border-radius: 8px;

    font-size: 1rem;

    background: #F8F9FA;

    color: #212529;

    transition: all 0.2s;

  }



  input:focus {

    outline: none;

    border-color: #007A3D;

    box-shadow: 0 0 0 3px rgba(0,122,61,0.15);

  }



  input:disabled {

    opacity: 0.6;

    cursor: not-allowed;

  }



  .password-container {

    position: relative;

    display: flex;

    align-items: center;

  }



  .password-container input {

    padding-right: 3rem;

  }



  .toggle-password {

    position: absolute;

    right: 0.75rem;

    background: none;

    border: none;

    color: #6C757D;

    cursor: pointer;

    padding: 0.25rem;

    display: flex;

    align-items: center;

    justify-content: center;

    transition: color 0.2s;

  }



  .toggle-password:hover:not(:disabled) {

    color: #007A3D;

  }



  .toggle-password:disabled {

    opacity: 0.6;

    cursor: not-allowed;

  }



  .error-message {

    background: #FFF5F5;

    color: #CE1126;

    padding: 0.75rem;

    border-radius: 6px;

    font-size: 0.875rem;

    margin-bottom: 1rem;

    border: 1px solid #FED7D7;

  }



  .btn-login {

    width: 100%;

    padding: 0.875rem;

    background: #007A3D;

    color: white;

    border: none;

    border-radius: 8px;

    font-weight: 600;

    font-size: 1rem;

    cursor: pointer;

    box-shadow: 0 4px 10px rgba(0,122,61,0.2);

    transition: all 0.2s;

  }



  .btn-login:hover:not(:disabled) {

    background: #005C2E;

    transform: translateY(-1px);

    box-shadow: 0 6px 12px rgba(0,122,61,0.25);

  }



  .btn-login:disabled {

    opacity: 0.6;

    cursor: not-allowed;

    transform: none;

  }



  .footer-links {

    text-align: center;

    margin-top: 1.5rem;

  }



  .footer-links a {

    color: #495057;

    text-decoration: none;

    font-weight: 500;

    font-size: 0.9rem;

    transition: color 0.2s ease;

  }



  .footer-links a:hover {

    color: #007A3D;

  }



  .register-link {

    color: #007A3D;

    font-weight: 600;

    margin-left: 0.25rem;

  }

  

  .footer-links a:hover .register-link {

    text-decoration: underline;

  }

</style>