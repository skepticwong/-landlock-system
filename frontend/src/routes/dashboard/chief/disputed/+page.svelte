<script lang="ts">
  import Navbar from '$lib/components/Navbar.svelte';
  import { AlertTriangle, MapPin, User } from 'lucide-svelte';
  import { onMount } from 'svelte';
  import { browser } from '$app/environment';

  const API = 'http://localhost:5000';
  let claims: any[] = [];
  let loading = true;
  let error = '';

  async function loadClaims() {
    try {
      const response = await fetch(`${API}/api/chief/disputed-claims`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      if (!response.ok) throw new Error('Could not load disputed claims');
      claims = await response.json();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Could not load disputed claims';
    } finally {
      loading = false;
    }
  }

  onMount(() => { if (browser) loadClaims(); });
</script>

<Navbar userType="chief" activeLink="/dashboard/chief/disputed" showNotification={false} />

<main class="page-content">
  <header><h1><AlertTriangle /> Disputed Claims</h1><p>Claims requiring dispute review and resolution</p></header>
  {#if loading}<p>Loading disputed claims...</p>
  {:else if error}<p class="error">{error}</p>
  {:else if claims.length === 0}<div class="empty">No disputed claims found.</div>
  {:else}
    <div class="claim-grid">
      {#each claims as claim}
        <article>
          <strong>{claim.plot_name || claim.name || `Claim ${claim.id}`}</strong>
          <p><User /> {claim.owner_name || 'Unknown owner'}</p>
          <p><MapPin /> {claim.location || claim.district || 'Location not recorded'}</p>
        </article>
      {/each}
    </div>
  {/if}
</main>

<style>
  :global(body) { background: #f8fafc; }
  .page-content { margin-left: 260px; padding: 2rem; }
  header { margin-bottom: 2rem; }
  h1 { display:flex; align-items:center; gap:.5rem; }
  .claim-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(280px,1fr)); gap:1rem; }
  article, .empty { background:white; border:1px solid #e2e8f0; border-radius:12px; padding:1.25rem; }
  article p { display:flex; gap:.5rem; align-items:center; color:#64748b; }
  .error { color:#dc2626; }
  @media (max-width: 768px) { .page-content { margin-left:0; padding-top:5rem; } }
</style>
