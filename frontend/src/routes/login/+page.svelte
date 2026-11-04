<script>
  import { goto } from "$app/navigation";
  import { browser } from "$app/environment";
  import { Eye, EyeOff } from "lucide-svelte";

  let phone = "";
  let password = "";
  let showPassword = false;
  let error = "";
  let isLoading = false;

  async function handleLogin() {
    error = "";

    if (!phone || !password) {
      error = "Please enter both phone number and password";
      return;
    }

    isLoading = true;

    try {
      // Corrected API endpoint with /api/ prefix
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phone, password }),
      });

      const data = await response.json();

      if (response.ok && data.access_token) {
        // Save token to localStorage
        if (browser) {
          localStorage.setItem("token", data.access_token);
          localStorage.setItem("user", JSON.stringify(data.user || { phone }));
        }

        // Redirect based on role
        const userRole = data.user?.role || "citizen";
        if (data.user && data.user.is_superuser) {
          goto("/dashboard/official");
        } else if (userRole === "chief") {
          goto("/dashboard/chief");
        } else if (userRole === "official") {
          goto("/dashboard/official");
        } else {
          goto("/dashboard");
        }
      } else {
        error = data.error || "Login failed. Please check your credentials.";
      }
    } catch (err) {
      error = "Network error. Please try again.";
      console.error("Login error:", err);
    } finally {
      isLoading = false;
    }
  }
</script>

<svelte:head>
  <title>Login - LandLock</title>
</svelte:head>

<div class="login-container">
  <div class="form-panel">
    <div class="form-inner">
      <div class="form-header">
        <img
          src="/images/Coat_of_arms_of_Malawi.svg"
          alt="LandLock"
          class="form-logo"
        />
        <h2>Welcome back</h2>
        <p>Sign in to your LandLock account</p>
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
              on:click={() => (showPassword = !showPassword)}
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
          <div class="error-message">{error}</div>
        {/if}

        <button type="submit" class="btn-login" disabled={isLoading}>
          {#if isLoading}
            <span class="btn-content">
              <span class="spinner"></span>
              Logging in...
            </span>
          {:else}
            Login
          {/if}
        </button>
      </form>

      <div class="footer-links">
        <span>
          <a href="/reset-password" on:click|preventDefault={() => goto("/reset-password")}
            >Development password reset</a
          >
        </span>
        <span>
          Don't have an account?
          <a href="/register" on:click|preventDefault={() => goto("/register")}
            >Sign Up</a
          >
        </span>
      </div>
    </div>
  </div>

  <div class="brand-panel">
    <div class="brand-inner">
      <img
        src="/images/Coat_of_arms_of_Malawi.svg"
        alt="LandLock Logo"
        class="brand-logo"
      />
      <h1>LandLock</h1>
      <p>Secure Land Registry for Malawi</p>
    </div>
  </div>
</div>

<style>
  .login-container {
    width: min(960px, calc(100% - 2rem));
    min-height: 620px;
    position: fixed;
    inset: 50% auto auto 50%;
    transform: translate(-50%, -50%);
    display: flex;
    background: #f8f9fa;
    border-radius: 20px;
    overflow: hidden;
    box-shadow: 0 24px 70px rgba(15, 23, 42, 0.18);
  }

  .login-container,
  .login-container * {
    box-sizing: border-box;
  }

  :global(body) {
    margin: 0;
    background-color: #edf4f1;
    background-image:
      linear-gradient(rgba(0, 122, 61, 0.22) 1px, transparent 1px),
      linear-gradient(to right, rgba(0, 122, 61, 0.22) 1px, #edf4f1 1px);
    background-size: 20px 20px;
  }

  /* ═══════════ Right brand panel ═══════════ */
  .brand-panel {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #007a3d;
    padding: 2rem;
    position: relative;
    overflow: hidden;
  }

  /* subtle decorative shapes */
  .brand-panel::before {
    content: "";
    position: absolute;
    top: -120px;
    right: -120px;
    width: 320px;
    height: 320px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.08);
  }

  .brand-panel::after {
    content: "";
    position: absolute;
    bottom: -160px;
    left: -80px;
    width: 380px;
    height: 380px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.06);
  }

  .brand-inner {
    text-align: center;
    position: relative;
    z-index: 1;
  }

  .brand-logo {
    width: 7rem;
    height: 7rem;
    object-fit: contain;
    margin-bottom: 1.5rem;
  }

  .brand-inner h1 {
    font-size: 2.25rem;
    font-weight: 700;
    color: white;
    letter-spacing: -0.5px;
    margin: 0 0 0.5rem;
  }

  .brand-inner p {
    font-size: 1.05rem;
    color: rgba(255, 255, 255, 0.85);
    font-weight: 500;
    margin: 0;
  }

  /* ═══════════ Right form panel ═══════════ */
  .form-panel {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 2rem;
  }

  .form-inner {
    width: 100%;
    max-width: 420px;
  }

  .form-header {
    text-align: center;
    margin-bottom: 2rem;
  }

  .form-logo {
    width: 3.5rem;
    height: 3.5rem;
    object-fit: contain;
    margin-bottom: 1rem;
  }

  .form-header h2 {
    font-size: 1.75rem;
    font-weight: 700;
    color: #0f172a;
    margin: 0 0 0.375rem;
  }

  .form-header p {
    font-size: 0.95rem;
    color: #64748b;
    margin: 0;
  }

  /* ═══════════ Form ═══════════ */
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
    border: 2px solid #dee2e6;
    border-radius: 8px;
    font-size: 1rem;
    background: white;
    color: #212529;
    transition: all 0.2s;
  }

  input:focus {
    outline: none;
    border-color: #007a3d;
    box-shadow: 0 0 0 3px rgba(0, 122, 61, 0.15);
  }

  input:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .password-container {
    position: relative;
    display: flex;
    align-items: center;
    width: 100%;
  }

  .password-container input {
    padding-right: 3rem;
  }

  .toggle-password {
    position: absolute;
    right: 0.75rem;
    background: none;
    border: none;
    color: #6c757d;
    cursor: pointer;
    padding: 0.25rem;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: color 0.2s;
  }

  .toggle-password:hover:not(:disabled) {
    color: #007a3d;
  }

  .toggle-password:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .error-message {
    background: #fff5f5;
    color: #ce1126;
    padding: 0.75rem;
    border-radius: 6px;
    font-size: 0.875rem;
    margin-bottom: 1rem;
    border: 1px solid #fed7d7;
  }

  .btn-login {
    width: 100%;
    padding: 0.875rem;
    background: #007a3d;
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    font-size: 1rem;
    cursor: pointer;
    box-shadow: 0 4px 10px rgba(0, 122, 61, 0.2);
    transition: all 0.2s;
  }

  .btn-login:hover:not(:disabled) {
    background: #005c2e;
    transform: translateY(-1px);
    box-shadow: 0 6px 12px rgba(0, 122, 61, 0.25);
  }

  .btn-login:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
  }

  .btn-content {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
  }

  .spinner {
    width: 16px;
    height: 16px;
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-top: 2px solid white;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    0% {
      transform: rotate(0deg);
    }
    100% {
      transform: rotate(360deg);
    }
  }

  /* ═══════════ Footer ═══════════ */
  .footer-links {
    text-align: center;
    margin-top: 1.5rem;
    color: #495057;
    font-weight: 500;
    font-size: 0.9rem;
  }

  .footer-links a {
    color: #007a3d;
    font-weight: 600;
    margin-left: 0.25rem;
    text-decoration: none;
    transition: color 0.2s ease;
  }

  .footer-links a:hover {
    text-decoration: underline;
  }

  /* ═══════════ Responsive ═══════════ */
  @media (max-width: 900px) {
    .brand-panel {
      display: none;
    }
    .form-panel {
      background: #f8f9fa;
    }
  }
</style>
