<script>
  import { goto } from "$app/navigation";

  let phone = "";
  let password = "";
  let confirmPassword = "";
  let error = "";
  let success = "";
  let isLoading = false;

  async function resetPassword() {
    error = "";
    success = "";
    if (password.length < 8) {
      error = "Password must be at least 8 characters.";
      return;
    }
    if (password !== confirmPassword) {
      error = "Passwords do not match.";
      return;
    }

    isLoading = true;
    try {
      const response = await fetch("/api/auth/dev/reset-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phone, password })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Password reset failed.");
      success = "Password reset successfully. Redirecting to login...";
      setTimeout(() => goto("/login"), 800);
    } catch (err) {
      error = err instanceof Error ? err.message : "Password reset failed.";
    } finally {
      isLoading = false;
    }
  }
</script>

<svelte:head><title>Development Password Reset - LandLock</title></svelte:head>

<main>
  <form on:submit|preventDefault={resetPassword}>
    <h1>Reset password</h1>
    <p>Development-only password recovery.</p>
    <label for="phone">Phone number</label>
    <input id="phone" type="tel" autocomplete="tel" bind:value={phone} />
    <label for="password">New password</label>
    <input id="password" type="password" autocomplete="new-password" minlength="8" bind:value={password} />
    <label for="confirm-password">Confirm password</label>
    <input id="confirm-password" type="password" autocomplete="new-password" minlength="8" bind:value={confirmPassword} />
    {#if error}<div role="alert">{error}</div>{/if}
    {#if success}<div role="status">{success}</div>{/if}
    <button type="submit" disabled={isLoading}>{isLoading ? "Resetting..." : "Reset password"}</button>
  </form>
</main>
