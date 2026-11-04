<script>
  import { goto } from "$app/navigation";
  import { browser } from "$app/environment";

  let password = "";
  let confirmPassword = "";
  let error = "";
  let success = "";
  let isLoading = false;

  async function changePassword() {
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

    const token = browser ? localStorage.getItem("token") : null;
    isLoading = true;
    try {
      const response = await fetch("/api/auth/change-password", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ password })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Password change failed.");
      success = "Password changed successfully.";
      setTimeout(() => goto("/dashboard"), 800);
    } catch (err) {
      error = err instanceof Error ? err.message : "Password change failed.";
    } finally {
      isLoading = false;
    }
  }
</script>

<svelte:head><title>Change Password - LandLock</title></svelte:head>

<main>
  <form on:submit|preventDefault={changePassword}>
    <h1>Create a new password</h1>
    <p>After three failed attempts, you must choose a new password.</p>
    <label for="password">New password</label>
    <input id="password" type="password" autocomplete="new-password" minlength="8" bind:value={password} />
    <label for="confirm-password">Confirm new password</label>
    <input id="confirm-password" type="password" autocomplete="new-password" minlength="8" bind:value={confirmPassword} />
    {#if error}<div role="alert">{error}</div>{/if}
    {#if success}<div role="status">{success}</div>{/if}
    <button type="submit" disabled={isLoading}>{isLoading ? "Saving..." : "Save password"}</button>
  </form>
</main>
